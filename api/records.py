from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import date
from typing import Optional


router = APIRouter(
    prefix="/records",
    tags=["Transaction Records"]
)


# =========================
# Request Model
# =========================

class TransactionRecord(BaseModel):
    transaction_date: date
    description: str
    account_name: str
    amount: float
    payment_method: Optional[str] = None
    transaction_type: Optional[str] = None
    invoice_no: Optional[str] = None



# =========================
# Temporary storage
# Replace with MySQL later
# =========================

records = []



# =========================
# CREATE RECORD
# =========================

@router.post("/")
def create_record(record: TransactionRecord):

    new_record = {
        "id": len(records) + 1,
        "date": record.transaction_date,
        "description": record.description,
        "account_name": record.account_name,
        "amount": record.amount,
        "payment_method": record.payment_method,
        "transaction_type": record.transaction_type,
        "invoice_no": record.invoice_no,
        "status": "active"
    }

    records.append(new_record)

    return {
        "message": "Transaction saved successfully",
        "record": new_record
    }



# =========================
# GET ALL RECORDS
# =========================

@router.get("/")
def get_records():

    return {
        "records": records
    }



# =========================
# GET ONE RECORD
# =========================

@router.get("/{record_id}")
def get_record(record_id: int):

    for record in records:
        if record["id"] == record_id:
            return record

    raise HTTPException(
        status_code=404,
        detail="Record not found"
    )



# =========================
# DELETE RECORD
# =========================

@router.delete("/{record_id}")
def delete_record(record_id: int):

    for record in records:

        if record["id"] == record_id:

            record["status"] = "void"

            return {
                "message": "Record voided",
                "record": record
            }


    raise HTTPException(
        status_code=404,
        detail="Record not found"
    )