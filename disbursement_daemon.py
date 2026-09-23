#!/usr/bin/env python3
"""
CivicAdvocate.OS - PayPal Payout Execution Daemon
Handles pre-flight checks, SHA-512 ledger sealing, OAuth2 authentication,
and dead-letter queue routing for operational disbursements.
"""

import hashlib
import json
import logging
import os
import sqlite3
import sys
import time
from typing import Any, Dict, Optional
import urllib.parse
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(daemon)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.LoggerAdapter(logging.getLogger("PayoutDaemon"), {"daemon": "DISBURSEMENT_DAEMON"})

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "SANDBOX_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "SANDBOX_CLIENT_SECRET")
PAYPAL_BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
DB_PATH = os.getenv("CIVIC_DB_PATH", "forensic_ledger.db")


class DisbursementDaemon:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ledger_accounts (
                    account_id TEXT PRIMARY KEY,
                    account_name TEXT NOT NULL,
                    balance REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS disbursements (
                    disbursement_id TEXT PRIMARY KEY,
                    sender_batch_id TEXT UNIQUE NOT NULL,
                    recipient_email TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    status TEXT NOT NULL,
                    sha512_digest TEXT NOT NULL,
                    paypal_batch_id TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dead_letter_queue (
                    dlq_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    disbursement_id TEXT NOT NULL,
                    error_code INTEGER NOT NULL,
                    response_payload TEXT NOT NULL,
                    failed_at REAL NOT NULL
                )
            """)
            cursor.execute("SELECT COUNT(*) as cnt FROM ledger_accounts")
            if cursor.fetchone()["cnt"] == 0:
                cursor.execute("INSERT INTO ledger_accounts VALUES ('1010_PAYPAL_CLEARING', 'PayPal Clearing', 10000.00)")
                cursor.execute("INSERT INTO ledger_accounts VALUES ('5020_OPERATIONAL_DISBURSEMENT', 'Disbursement Expense', 0.00)")
            conn.commit()

    def _compute_digest(self, payload: Dict[str, Any]) -> str:
        canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha512(canonical_json.encode('utf-8')).hexdigest()

    def _get_bearer_token(self) -> str:
        if self._token and time.time() < (self._token_expires_at - 60):
            return self._token

        url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
        import base64
        encoded_auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode('utf-8')

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                res_body = json.loads(resp.read().decode('utf-8'))
                self._token = res_body["access_token"]
                self._token_expires_at = time.time() + res_body.get("expires_in", 3600)
                logger.info("OAuth2 Bearer token successfully acquired/refreshed.")
                return self._token
        except urllib.error.HTTPError as e:
            logger.error(f"Failed to obtain OAuth2 token: HTTP {e.code} - {e.read().decode()}")
            raise RuntimeError("Authentication failure with payment gateway.")

    def _preflight_check(self, amount: float) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM ledger_accounts WHERE account_id = '1010_PAYPAL_CLEARING'")
            row = cursor.fetchone()
            return bool(row and row["balance"] >= amount)

    def _route_to_dlq(self, disbursement_id: str, status_code: int, response_payload: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dead_letter_queue (disbursement_id, error_code, response_payload, failed_at)
                VALUES (?, ?, ?, ?)
            """, (disbursement_id, status_code, response_payload, time.time()))
            cursor.execute("""
                UPDATE disbursements SET status = 'FAILED_AUDIT', updated_at = ?
                WHERE disbursement_id = ?
            """, (time.time(), disbursement_id))
            conn.commit()
        logger.warning(f"Disbursement {disbursement_id} routed to DLQ (HTTP {status_code}).")

    def execute_disbursement(self, disbursement_id: str, recipient_email: str, amount: float, currency: str = "USD") -> Dict[str, Any]:
        logger.info(f"Initiating disbursement: {disbursement_id} -> {recipient_email} (${amount} {currency})")

        if not self._preflight_check(amount):
            raise ValueError(f"Insufficient cleared funds for disbursement {disbursement_id}.")

        timestamp = time.time()
        idempotency_raw = f"{disbursement_id}:{recipient_email}:{amount}:{currency}"
        sender_batch_id = f"ca_batch_{hashlib.sha512(idempotency_raw.encode()).hexdigest()[:16]}"

        pre_seal_payload = {
            "disbursement_id": disbursement_id,
            "sender_batch_id": sender_batch_id,
            "recipient": recipient_email,
            "amount": amount,
            "currency": currency,
            "status": "PENDING",
            "timestamp": timestamp
        }
        sha512_digest = self._compute_digest(pre_seal_payload)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO disbursements (disbursement_id, sender_batch_id, recipient_email, amount, currency, status, sha512_digest, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?, ?)
            """, (disbursement_id, sender_batch_id, recipient_email, amount, currency, sha512_digest, timestamp, timestamp))
            conn.commit()

        token = self._get_bearer_token()

        payout_payload = {
            "sender_batch_header": {
                "sender_batch_id": sender_batch_id,
                "email_subject": "CivicAdvocate.OS Disbursement Authorization"
            },
            "items": [
                {
                    "recipient_type": "EMAIL",
                    "amount": {
                        "value": f"{amount:.2f}",
                        "currency": currency
                    },
                    "receiver": recipient_email,
                    "note": f"Audit Reference ID: {disbursement_id}",
                    "sender_item_id": f"item_{disbursement_id}"
                }
            ]
        }

        url = f"{PAYPAL_BASE_URL}/v1/payments/payouts"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        body = json.dumps(payout_payload).encode('utf-8')
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req) as resp:
                response_data = json.loads(resp.read().decode('utf-8'))
                paypal_batch_id = response_data.get("batch_header", {}).get("payout_batch_id")
                batch_status = response_data.get("batch_header", {}).get("batch_status", "PROCESSING")

                post_seal_payload = {
                    "disbursement_id": disbursement_id,
                    "paypal_batch_id": paypal_batch_id,
                    "status": batch_status,
                    "amount": amount,
                    "pre_digest": sha512_digest
                }
                final_digest = self._compute_digest(post_seal_payload)

                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE ledger_accounts SET balance = balance - ? WHERE account_id = '1010_PAYPAL_CLEARING'", (amount,))
                    cursor.execute("UPDATE ledger_accounts SET balance = balance + ? WHERE account_id = '5020_OPERATIONAL_DISBURSEMENT'", (amount,))
                    cursor.execute("""
                        UPDATE disbursements 
                        SET status = ?, paypal_batch_id = ?, sha512_digest = ?, updated_at = ?
                        WHERE disbursement_id = ?
                    """, (batch_status, paypal_batch_id, final_digest, time.time(), disbursement_id))
                    conn.commit()

                logger.info(f"Disbursement {disbursement_id} successfully executed. Batch ID: {paypal_batch_id}")
                return {
                    "status": "SUCCESS",
                    "disbursement_id": disbursement_id,
                    "paypal_batch_id": paypal_batch_id,
                    "digest": final_digest
                }

        except urllib.error.HTTPError as e:
            error_response = e.read().decode('utf-8')
            self._route_to_dlq(disbursement_id, e.code, error_response)
            return {
                "status": "FAILED",
                "disbursement_id": disbursement_id,
                "error_code": e.code,
                "dlq_routed": True
            }


if __name__ == "__main__":
    daemon = DisbursementDaemon(db_path=DB_PATH)
    result = daemon.execute_disbursement(
        disbursement_id="disb_20260922_001",
        recipient_email="payee@example.com",
        amount=150.00,
        currency="USD"
    )
    print("\nExecution Output:")
    print(json.dumps(result, indent=2))
