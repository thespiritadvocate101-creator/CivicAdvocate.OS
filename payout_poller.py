#!/usr/bin/env python3
"""
CivicAdvocate.OS - PayPal Payout Status Polling Daemon
Polls active payout batches against PayPal API, updates finality states,
and seals status transitions in the forensic ledger.
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
logger = logging.LoggerAdapter(logging.getLogger("StatusPoller"), {"daemon": "POLL_DAEMON"})

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "SANDBOX_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "SANDBOX_CLIENT_SECRET")
PAYPAL_BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
DB_PATH = os.getenv("CIVIC_DB_PATH", "forensic_ledger.db")


class StatusPollingDaemon:
    def __init__(self, db_path: str, poll_interval: int = 60):
        self.db_path = db_path
        self.poll_interval = poll_interval
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

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
                return self._token
        except urllib.error.HTTPError as e:
            logger.error(f"Failed to obtain OAuth2 token during poll: HTTP {e.code}")
            raise RuntimeError("Authentication failure during status polling.")

    def fetch_batch_status(self, batch_id: str) -> Dict[str, Any]:
        token = self._get_bearer_token()
        url = f"{PAYPAL_BASE_URL}/v1/payments/payouts/{batch_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            logger.error(f"Failed to query batch {batch_id}: HTTP {e.code} - {e.read().decode()}")
            return {}

    def poll_active_disbursements(self) -> None:
        """Query open batches and update local ledger states."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT disbursement_id, paypal_batch_id, status, sha512_digest 
                FROM disbursements 
                WHERE status IN ('PENDING', 'PROCESSING') AND paypal_batch_id IS NOT NULL
            """)
            rows = cursor.fetchall()

        if not rows:
            logger.info("No active pending batches found for polling.")
            return

        logger.info(f"Polling {len(rows)} active payout batch(es)...")

        for row in rows:
            disb_id = row["disbursement_id"]
            batch_id = row["paypal_batch_id"]
            current_status = row["status"]
            prev_digest = row["sha512_digest"]

            api_response = self.fetch_batch_status(batch_id)
            if not api_response:
                continue

            batch_header = api_response.get("batch_header", {})
            new_status = batch_header.get("batch_status", current_status)

            if new_status != current_status:
                logger.info(f"Batch {batch_id} status transition: {current_status} -> {new_status}")

                seal_payload = {
                    "disbursement_id": disb_id,
                    "paypal_batch_id": batch_id,
                    "previous_status": current_status,
                    "new_status": new_status,
                    "previous_digest": prev_digest,
                    "timestamp": time.time()
                }
                new_digest = self._compute_digest(seal_payload)

                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE disbursements 
                        SET status = ?, sha512_digest = ?, updated_at = ?
                        WHERE disbursement_id = ?
                    """, (new_status, new_digest, time.time(), disb_id))
                    conn.commit()
                logger.info(f"Ledger sealed for disbursement {disb_id} under new state: {new_status}")
            else:
                logger.info(f"Batch {batch_id} state unchanged: {current_status}")

    def run_daemon_loop(self) -> None:
        logger.info(f"Starting Payout Status Polling Daemon (Interval: {self.poll_interval}s)...")
        try:
            while True:
                self.poll_active_disbursements()
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("Status Polling Daemon stopped by operator.")


if __name__ == "__main__":
    poller = StatusPollingDaemon(db_path=DB_PATH, poll_interval=30)
    poller.run_daemon_loop()
