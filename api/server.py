import os
import io
import json
import subprocess
import mysql.connector
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from unittest import result
from pydantic import BaseModel
from typing import Optional
from datetime import date
from api import records
from api.database import get_db_connection
from api.reporting import generate_report
from services.template_generator import generate_transaction_template


app = FastAPI(
    title="How's Business API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


def get_db_connection():
    with open("db_config.json", "r") as f:
        db_config = json.load(f)
        
    return mysql.connector.connect(**db_config)


class LoginRequest(BaseModel):
    email: str
    password: str

class PinVerifyRequest(BaseModel):
    email: str
    pin: str

class RecordCreate(BaseModel):
    transaction_date: date
    description: str
    account_name: str
    amount: float
    payment_method: Optional[str] = None
    transaction_type: Optional[str] = None
    invoice_no: Optional[str] = None


@app.get("/")
def home():
    return {
        "message": "How's Business API is running"
    }


@app.get("/login")
async def login_get_fallback():
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Login must be accessed via the main application."
        },
    )

@app.post("/login")
async def login_user(credentials: LoginRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT user_no, email, full_name, position, business_name FROM users WHERE email = %s AND password = %s"
        cursor.execute(query, (credentials.email, credentials.password))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
        return {
            "status": "success",
            "message": "Login successful",
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/verify-pin")
async def verify_pin(data: PinVerifyRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT user_no FROM users WHERE email = %s AND pin = %s"
        cursor.execute(query, (data.email, data.pin))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect PIN")
            
        return {"status": "success", "message": "PIN verified successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download-template")
def download_template():

    file_path = generate_transaction_template()

    return FileResponse(
        path=file_path,
        filename="Transaction_Template.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/upload")
def upload_page():
    return FileResponse("static/upload/index.html")


@app.post("/extract")
async def extract_excel(file: UploadFile, user_no: int = Form(...),):

    if not file.filename.endswith(".xlsx"):
        return {
            "status": "failed",
            "message": "Only .xlsx files allowed"
        }

    file_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    # Save uploaded file
    with open(file_path, "wb") as f:
        f.write(await file.read())

    print(f"✅ File saved: {file_path}")

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO uploads (user_no, file_name, upload_date) 
            VALUES (%s, %s, NOW())
        """,
            (user_no, file.filename),
        )
        conn.commit()

        upload_id = cursor.lastrowid
        print(f"✅ Upload created with ID: {upload_id}")

        result = subprocess.run(
            [
                r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe",
                "R/extract_data.R",
                file_path,
                str(user_no),
                str(upload_id),
            ],
            capture_output=True,
            text=True,
            check=True
        )
        print("===== R STDOUT =====")
        print(result.stdout)

        extracted_data = json.loads(result.stdout)

        insert_query = """
            INSERT INTO records (
                user_no,
                upload_id,
                transaction_date, 
                description,
                account_name, 
                amount, 
                payment_method, 
                transaction_type,
                invoice_no, 
                status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        for row in extracted_data:
            transaction_date = row.get("transaction_date", row.get("Date"))
            description = row.get("description", row.get("Description", ""))
            account_name = row.get("account_name", row.get("Account Type"))
            amount = float(row.get("amount", row.get("Amount", 0)))
            payment_method = row.get("payment_method", row.get("Payment Method"))
            transaction_type = row.get("transaction_type", row.get("Account Name"))
            invoice_no = row.get(
                "invoice_no", row.get("Invoice No.", row.get("Invoice No"))
            )
            status = row.get("status", "active")

            cursor.execute(
                insert_query,
                (
                    user_no,
                    upload_id,
                    transaction_date,
                    description,
                    account_name,
                    amount,
                    payment_method,
                    transaction_type,
                    invoice_no,
                    status,
                ),
            )

        conn.commit()

        return {
            "status": "success",
            "upload_id": upload_id,
            "user_no": user_no,
            "imported": len(extracted_data)
        }

    except subprocess.CalledProcessError as e:
        print("===== R STDERR =====")
        print(e.stderr)
        if conn:
            conn.rollback()

        return {
            "status": "failed",
            "message": e.stderr
        }

    except Exception as e:
        print("===== PYTHON ERROR =====")
        print(e)
        if conn:
            conn.rollback()

        return {
            "status": "failed",
            "message": str(e)
        }
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/records/")
async def get_records():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM records WHERE status = 'active' ORDER BY ref_no ASC")
        rows = cursor.fetchall()

        cursor.close()
        conn.close()
        
        records_list = []
        for row in rows:
            records_list.append({
                "ref_no": row["ref_no"],
                "transaction_date": str(row["transaction_date"]),
                "description": row["description"],
                "account_name": row["account_name"],
                "amount": float(row["amount"]),
                "payment_method": row["payment_method"],
                "transaction_type": row["transaction_type"],
                "invoice_no": row["invoice_no"],
                "status": row["status"]
            })
            
        return records_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/records/")
async def add_manual_record(record: RecordCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Pull all active records
        query = """
            INSERT INTO records (
                user_no,
                upload_id,
                transaction_date, 
                description, 
                account_name, 
                amount, 
                payment_method, 
                transaction_type, 
                invoice_no, 
                status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
        """
        values = (
            record.user_no,
            record.upload_id,
            record.transaction_date,
            record.description,
            record.account_name,
            record.amount,
            record.payment_method,
            record.transaction_type,
            record.invoice_no
        )

        cursor.execute(query, values)
        conn.commit()

        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Record saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    


class ReportRequest(BaseModel):
    user_no: int
    upload_id: int | None = None
    month: str | None = None
    report_type: str = "income_statement"

@app.post("/reports")
def generate_reports(payload: ReportRequest):
    try:
        data = generate_report(
            report_type=payload.report_type,
            user_no=payload.user_no,
            upload_id=payload.upload_id,
            month=payload.month,
        )
        return data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.get("/reports/{report_type}")
async def get_financial_report(report_type: str, user_no: int = Query(...), month: str = Query(...), upload_id: int | None = Query(None),):
    try:
        data = generate_report(
            report_type=report_type,
            user_no=user_no,
            upload_id=upload_id,
            month=month,
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn

    #init_db()

    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
