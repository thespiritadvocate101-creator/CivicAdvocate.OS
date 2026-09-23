#!/usr/bin/env python3
"""
CivicAdvocate.OS - FastAPI Disbursement Gateway Server
Running on port 8089 to circumvent kernel TIME_WAIT locks.
"""

import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
import sqlite3
import os
from typing import List, Optional
from disbursement_daemon import DisbursementDaemon, DB_PATH

app = FastAPI(
    title="CivicAdvocate.OS Disbursement & Forensic Ledger API",
    version="1.0.0",
    description="REST API gateway for operational disbursements and SHA-512 ledger verification."
)

daemon = DisbursementDaemon(db_path=DB_PATH)


class DisbursementCreateRequest(BaseModel):
    disbursement_id: str = Field(..., json_schema_extra={"example": "disb_20260922_002"})
    recipient_email: EmailStr = Field(..., json_schema_extra={"example": "payee@example.com"})
    amount: float = Field(..., gt=0.0, json_schema_extra={"example": 150.00})
    currency: str = Field(default="USD", json_schema_extra={"example": "USD"})


class DisbursementResponseModel(BaseModel):
    disbursement_id: str
    sender_batch_id: Optional[str] = None
    recipient_email: str
    amount: float
    currency: str
    status: str
    paypal_batch_id: Optional[str] = None
    sha512_digest: str


class DLQItemModel(BaseModel):
    dlq_id: int
    disbursement_id: str
    error_code: int
    response_payload: str
    failed_at: float


class LedgerAccountModel(BaseModel):
    account_id: str
    account_name: str
    balance: float


@app.post("/v1/disbursements", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_disbursement(payload: DisbursementCreateRequest):
    try:
        result = daemon.execute_disbursement(
            disbursement_id=payload.disbursement_id,
            recipient_email=payload.recipient_email,
            amount=payload.amount,
            currency=payload.currency
        )
        if result.get("status") == "FAILED":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Disbursement failed and routed to DLQ. Error code: {result.get('error_code')}"
            )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/v1/disbursements/{disbursement_id}", response_model=DisbursementResponseModel)
def get_disbursement(disbursement_id: str):
    with daemon._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM disbursements WHERE disbursement_id = ?", (disbursement_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Disbursement record not found.")
        return dict(row)


@app.get("/v1/disbursements/dlq/items", response_model=List[DLQItemModel])
def get_dead_letter_queue():
    with daemon._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dead_letter_queue")
        return [dict(row) for row in cursor.fetchall()]


@app.get("/v1/ledger/accounts", response_model=List[LedgerAccountModel])
def get_ledger_accounts():
    with daemon._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ledger_accounts")
        return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8089, reload=True)
