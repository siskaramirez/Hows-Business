import os
import io
import json
import subprocess
import tempfile
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import date
from pathlib import Path
from api.database import get_db_connection, ensure_user_scoped_invoice_index
from api.reporting import generate_report
from services.r_runtime import find_rscript
from services.result_cache import (
    get_cached_result,
    invalidate_user_cache,
    set_cached_result,
)

import traceback
from services.dataset_context import (
    build_dataset_insights,
    dataset_provenance,
    get_business_schedule_path,
    get_dataset_paths,
    save_user_dataset,
)

BASE_DIR = Path(__file__).resolve().parent.parent
FORECAST_R_SCRIPT = BASE_DIR / "R" / "run_forecast.R"
SIMULATION_R_SCRIPT = BASE_DIR / "R" / "run_simulation.R"
INSIGHTS_R_SCRIPT = BASE_DIR / "R" / "run_insights.R"


def build_journal_lines(account_name, transaction_type, amount, payment_method):
    amount = float(amount)
    debit_side = account_name in {"Asset", "Expense"}
    lines = [[
        account_name,
        transaction_type,
        amount if debit_side else 0,
        0 if debit_side else amount,
    ]]

    payment_account = payment_method if payment_method in {"Cash", "Gcash", "Maya"} else "Cash"
    if account_name == "Revenue":
        lines.append(["Asset", payment_account, amount, 0])
    elif account_name == "Expense":
        lines.append(["Asset", payment_account, 0, amount])
    elif account_name == "Asset":
        if transaction_type == "Cash":
            lines.append(["Equity", "Owner's Equity", 0, amount])
        else:
            lines.append(["Asset", payment_account, 0, amount])
    elif account_name == "Liability":
        counterpart = "Inventory" if transaction_type == "Accounts Payable" else payment_account
        lines.append(["Asset", counterpart, amount, 0])
    elif account_name == "Equity":
        lines.append(["Asset", payment_account, amount, 0])

    return lines


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

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


UPLOAD_FOLDER = BASE_DIR / "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    contact_number: str
    first_name: str
    middle_name: str | None = None
    last_name: str
    password: str

class PinVerifyRequest(BaseModel):
    email: str
    pin: str

class RecordCreate(BaseModel):
    user_no: int
    upload_id: int | None = None
    transaction_date: date
    description: str
    account_name: str
    amount: float
    payment_method: Optional[str] = None
    transaction_type: Optional[str] = None
    invoice_no: Optional[str] = None


class RecordUpdate(BaseModel):
    user_no: int
    transaction_date: date
    description: str
    account_name: str
    amount: float
    payment_method: str
    transaction_type: str
    invoice_no: str


class PinUserVerifyRequest(BaseModel):
    user_no: int
    pin: str


class ImportRecord(BaseModel):
    transaction_date: date
    description: str
    account_name: str
    amount: float
    payment_method: str
    transaction_type: str
    invoice_no: str


class ImportConfirmRequest(BaseModel):
    user_no: int
    file_name: str
    records: list[ImportRecord]


class ReportRequest(BaseModel):
    user_no: int
    upload_id: int | None = None
    month: str | None = None
    report_type: str = "income_statement"


class ReportBatchRequest(BaseModel):
    user_no: int
    months: list[str]
    report_type: str = "income_statement"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "api_version": 2,
        "signup_enabled": True,
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


@app.post("/signup", status_code=201)
async def signup_user(payload: SignupRequest):
    """Create a user using the columns available in the deployed users table."""
    conn = None
    cursor = None
    try:
        email = payload.email.strip().lower()
        first_name = payload.first_name.strip()
        middle_name = (payload.middle_name or "").strip()
        last_name = payload.last_name.strip()
        contact_number = payload.contact_number.strip()

        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            raise HTTPException(status_code=422, detail="Enter a valid email address.")
        if not first_name or not last_name:
            raise HTTPException(status_code=422, detail="First and last name are required.")
        if len(payload.password) < 8:
            raise HTTPException(status_code=422, detail="Password must be at least 8 characters.")
        if not contact_number.replace("+", "", 1).isdigit():
            raise HTTPException(status_code=422, detail="Enter a valid contact number.")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_no FROM users WHERE LOWER(email) = %s LIMIT 1", (email,))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="An account with this email already exists.")

        cursor.execute("SHOW COLUMNS FROM users")
        schema = {row["Field"]: row for row in cursor.fetchall()}
        full_name = " ".join(part for part in (first_name, middle_name, last_name) if part)
        candidates = {
            "email": email,
            "password": payload.password,
            "contact_number": contact_number,
            "contact_no": contact_number,
            "phone": contact_number,
            "first_name": first_name,
            "middle_name": middle_name or None,
            "last_name": last_name,
            "full_name": full_name,
            "position": "Manager",
            "business_name": "Delikart",
            "pin": "",
        }
        values_by_column = {
            column: candidates[column]
            for column in schema
            if column in candidates
        }
        missing_required = [
            column
            for column, definition in schema.items()
            if definition["Null"] == "NO"
            and definition["Default"] is None
            and "auto_increment" not in (definition["Extra"] or "")
            and column not in values_by_column
        ]
        if missing_required:
            raise RuntimeError(
                "The users table requires unsupported columns: "
                + ", ".join(missing_required)
            )

        columns = list(values_by_column)
        placeholders = ", ".join(["%s"] * len(columns))
        cursor.execute(
            f"INSERT INTO users ({', '.join(f'`{column}`' for column in columns)}) "
            f"VALUES ({placeholders})",
            tuple(values_by_column[column] for column in columns),
        )
        user_no = cursor.lastrowid
        conn.commit()
        return {
            "status": "success",
            "message": "Account created successfully.",
            "user": {
                "user_no": user_no,
                "email": email,
                "full_name": full_name,
                "position": values_by_column.get("position"),
                "business_name": values_by_column.get("business_name"),
            },
        }
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as exc:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.post("/set-pin")
async def set_pin(data: PinVerifyRequest):
    if len(data.pin) != 4 or not data.pin.isdigit():
        raise HTTPException(status_code=422, detail="PIN must contain exactly four digits.")

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET pin = %s WHERE LOWER(email) = %s",
            (data.pin, data.email.strip().lower()),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Account not found.")
        conn.commit()
        return {"status": "success", "message": "PIN saved successfully."}
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as exc:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


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


@app.post("/verify-pin/user")
async def verify_pin_for_user(data: PinUserVerifyRequest):
    if len(data.pin) != 4 or not data.pin.isdigit():
        raise HTTPException(status_code=422, detail="PIN must contain exactly four digits.")

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_no FROM users WHERE user_no = %s AND pin = %s",
            (data.user_no, data.pin),
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=401, detail="Incorrect PIN.")
        return {"status": "success", "message": "PIN verified successfully."}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/download-template")
def download_template():
    from services.template_generator import generate_transaction_template

    file_path = generate_transaction_template()

    return FileResponse(
        path=file_path,
        filename="Transaction_Template.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/upload")
def upload_page():
    return FileResponse(BASE_DIR / "static" / "upload" / "index.html")


@app.post("/extract")
async def preview_excel(file: UploadFile, user_no: int = Form(...)):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are allowed.")

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".xlsx",
            dir=UPLOAD_FOLDER,
            delete=False,
        ) as handle:
            content = await file.read()
            if len(content) > 10 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="The file must be 10 MB or smaller.")
            handle.write(content)
            temp_path = handle.name

        completed = subprocess.run(
            [
                find_rscript(),
                "--vanilla",
                str(BASE_DIR / "R" / "extract_data.R"),
                temp_path,
            ],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR / "R"),
            timeout=120,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())

        raw = completed.stdout.strip()
        start, end = raw.find("["), raw.rfind("]")
        if start == -1 or end == -1:
            raise RuntimeError("R extraction returned invalid JSON.")
        extracted_data = json.loads(raw[start:end + 1])

        return {
            "status": "preview",
            "user_no": user_no,
            "file_name": Path(file.filename).name,
            "records": extracted_data,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@app.post("/imports/confirm")
def confirm_excel_import(payload: ImportConfirmRequest):
    if not payload.records:
        raise HTTPException(status_code=400, detail="No records were submitted.")

    allowed_accounts = {"Asset", "Liability", "Equity", "Revenue", "Expense"}
    allowed_payments = {"Cash", "Gcash", "Maya"}
    allowed_transactions = {
        "Cash", "Kitchen Equipment", "Inventory", "Accounts Payable",
        "Loans Payable", "Lease Liability", "Owner's Equity",
        "Retained Earnings", "Food Sales", "Beverage and Snack Sales",
        "Cost of Goods Sold (COGS)", "Canteen Rent Expense",
        "Utilities Expense", "Sales", "Rent Expense", "Office Supplies",
        "Service Revenue", "Cost of Goods Sold", "Equipment",
    }
    invoice_numbers = [record.invoice_no.strip() for record in payload.records]
    if any(not invoice for invoice in invoice_numbers):
        raise HTTPException(status_code=400, detail="Every row requires an invoice number.")
    if len(invoice_numbers) != len(set(invoice_numbers)):
        raise HTTPException(status_code=400, detail="Duplicate invoice numbers exist in the review.")

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        ensure_user_scoped_invoice_index(conn)
        cursor = conn.cursor()

        placeholders = ", ".join(["%s"] * len(invoice_numbers))
        cursor.execute(
            f"""
                SELECT invoice_no
                FROM records
                WHERE user_no = %s AND invoice_no IN ({placeholders})
            """,
            (payload.user_no, *invoice_numbers),
        )
        existing = [row[0] for row in cursor.fetchall()]
        if existing:
            raise ValueError(
                "Already imported invoice number(s): " + ", ".join(existing)
            )

        cursor.execute(
            """
                INSERT INTO uploads (user_no, file_name, upload_date)
                VALUES (%s, %s, NOW())
            """,
            (payload.user_no, Path(payload.file_name).name[:255]),
        )
        upload_id = cursor.lastrowid

        record_insert = """
            INSERT INTO records (
                user_no, upload_id, transaction_date, description,
                account_name, amount, payment_method, transaction_type,
                invoice_no, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
        """
        line_insert = """
            INSERT INTO record_lines
                (ref_no, account_name, transaction_type, debit, credit)
            VALUES (%s, %s, %s, %s, %s)
        """

        for record in payload.records:
            if record.account_name not in allowed_accounts:
                raise ValueError(f"Invalid account type: {record.account_name}")
            if record.payment_method not in allowed_payments:
                raise ValueError(f"Invalid payment method: {record.payment_method}")
            if record.transaction_type not in allowed_transactions:
                raise ValueError(f"Invalid transaction type: {record.transaction_type}")
            if record.amount <= 0:
                raise ValueError(f"Amount must be positive for {record.invoice_no}.")

            cursor.execute(
                record_insert,
                (
                    payload.user_no,
                    upload_id,
                    record.transaction_date,
                    record.description.strip(),
                    record.account_name,
                    record.amount,
                    record.payment_method,
                    record.transaction_type,
                    record.invoice_no.strip(),
                ),
            )
            ref_no = cursor.lastrowid
            for line in build_journal_lines(
                record.account_name,
                record.transaction_type,
                record.amount,
                record.payment_method,
            ):
                cursor.execute(line_insert, (ref_no, *line))

        conn.commit()
        invalidate_user_cache(payload.user_no)
        return {
            "status": "success",
            "upload_id": upload_id,
            "imported": len(payload.records),
        }
    except ValueError as exc:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.post("/extract-legacy")
async def extract_excel(file: UploadFile, user_no: int = Form(...),):
    raise HTTPException(
        status_code=410,
        detail="Direct import is disabled. Preview and confirm the extracted records.",
    )

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
                find_rscript(),
                "--vanilla",
                str(BASE_DIR / "R" / "extract_data.R"),
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

        line_insert_query = """
            INSERT INTO record_lines (ref_no, account_name, transaction_type, debit, credit)
            VALUES (%s, %s, %s, %s, %s)
        """
        imported_count = 0

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
                "SELECT ref_no FROM records WHERE invoice_no = %s AND user_no = %s",
                (invoice_no, user_no),
            )
            if cursor.fetchone():
                print(f"⏭ Skipping duplicate invoice: {invoice_no}")
                continue

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

            ref_no = cursor.lastrowid
            for line in build_journal_lines(
                account_name,
                transaction_type,
                amount,
                payment_method,
            ):
                cursor.execute(line_insert_query, (ref_no, *line))

            imported_count += 1

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
def get_records(
    user_no: int = Query(...),
    limit: int | None = Query(None, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None, max_length=100),
):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        where_parts = ["user_no = %s"]
        params = [user_no]
        if search and search.strip():
            needle = f"%{search.strip()}%"
            where_parts.append(
                """
                (
                    CAST(transaction_date AS CHAR) LIKE %s OR
                    account_name LIKE %s OR description LIKE %s OR
                    invoice_no LIKE %s OR CAST(amount AS CHAR) LIKE %s OR
                    status LIKE %s OR payment_method LIKE %s OR
                    transaction_type LIKE %s
                )
                """
            )
            params.extend([needle] * 8)
        where_sql = " AND ".join(where_parts)

        cursor.execute(f"SELECT COUNT(*) AS total FROM records WHERE {where_sql}", tuple(params))
        total = int(cursor.fetchone()["total"])

        pagination_sql = ""
        query_params = list(params)
        order_direction = "ASC"
        if limit is not None:
            order_direction = "DESC"
            pagination_sql = " LIMIT %s OFFSET %s"
            query_params.extend([limit, offset])

        cursor.execute(
            f"""
                SELECT *
                FROM records
                WHERE {where_sql}
                ORDER BY ref_no {order_direction}
                {pagination_sql}
            """,
            tuple(query_params),
        )
        rows = cursor.fetchall()
        
        records_list = []
        for row_index, row in enumerate(rows):
            display_no = (
                total - offset - row_index
                if limit is not None
                else offset + row_index + 1
            )
            records_list.append({
                "display_no": display_no,
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
            
        if limit is None:
            return records_list
        return {"records": records_list, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/records/version")
def get_records_version(user_no: int = Query(...)):
    """Return a cheap change marker without transferring the full records table."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT COUNT(*) AS record_count, COALESCE(MAX(ref_no), 0) AS latest_ref
            FROM records
            WHERE user_no = %s
            """,
            (user_no,),
        )
        return cursor.fetchone()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.delete("/records/{ref_no}")
def delete_record(ref_no: int, user_no: int = Query(...)):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ref_no FROM records WHERE ref_no = %s AND user_no = %s",
            (ref_no, user_no),
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Record not found.")

        cursor.execute(
            """
            UPDATE records
            SET status = 'voided'
            WHERE ref_no = %s AND user_no = %s
            """,
            (ref_no, user_no),
        )
        conn.commit()
        invalidate_user_cache(user_no)
        return {"status": "success", "voided_ref_no": ref_no}
    except HTTPException:
        raise
    except Exception as exc:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.post("/records/")
async def add_manual_record(record: RecordCreate):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        ensure_user_scoped_invoice_index(conn)
        cursor = conn.cursor()

        invoice_no = (record.invoice_no or "").strip()
        if not invoice_no:
            raise HTTPException(status_code=400, detail="Invoice number is required.")
        cursor.execute(
            """
            SELECT ref_no FROM records
            WHERE user_no = %s AND invoice_no = %s
            LIMIT 1
            """,
            (record.user_no, invoice_no),
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="That invoice number already exists in your records.",
            )

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
            invoice_no
        )

        cursor.execute(query, values)
        
        ref_no = cursor.lastrowid

        line_insert_query = """
            INSERT INTO record_lines
                (ref_no, account_name, transaction_type, debit, credit)
            VALUES (%s, %s, %s, %s, %s)
        """
        for line in build_journal_lines(
            record.account_name,
            record.transaction_type,
            record.amount,
            record.payment_method,
        ):
            cursor.execute(line_insert_query, (ref_no, *line))

        conn.commit()
        invalidate_user_cache(record.user_no)
        return {
            "status": "success",
            "message": "Record saved successfully",
            "ref_no": ref_no,
        }
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as exc:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.put("/records/{ref_no}")
def update_record(ref_no: int, record: RecordUpdate):
    conn = None
    cursor = None
    try:
        if record.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive.")
        invoice_no = record.invoice_no.strip()
        if not invoice_no:
            raise HTTPException(status_code=400, detail="Invoice number is required.")

        conn = get_db_connection()
        ensure_user_scoped_invoice_index(conn)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ref_no FROM records
            WHERE ref_no = %s AND user_no = %s AND status <> 'voided'
            """,
            (ref_no, record.user_no),
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Record not found.")
        cursor.execute(
            """
            SELECT ref_no FROM records
            WHERE user_no = %s AND invoice_no = %s AND ref_no <> %s
            LIMIT 1
            """,
            (record.user_no, invoice_no, ref_no),
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="That invoice number already exists in your records.",
            )

        cursor.execute(
            """
            UPDATE records
            SET transaction_date = %s,
                description = %s,
                account_name = %s,
                amount = %s,
                payment_method = %s,
                transaction_type = %s,
                invoice_no = %s,
                status = 'edited'
            WHERE ref_no = %s AND user_no = %s
            """,
            (
                record.transaction_date,
                record.description.strip(),
                record.account_name,
                record.amount,
                record.payment_method,
                record.transaction_type,
                invoice_no,
                ref_no,
                record.user_no,
            ),
        )
        cursor.execute("DELETE FROM record_lines WHERE ref_no = %s", (ref_no,))
        line_insert = """
            INSERT INTO record_lines
                (ref_no, account_name, transaction_type, debit, credit)
            VALUES (%s, %s, %s, %s, %s)
        """
        for line in build_journal_lines(
            record.account_name,
            record.transaction_type,
            record.amount,
            record.payment_method,
        ):
            cursor.execute(line_insert, (ref_no, *line))

        conn.commit()
        invalidate_user_cache(record.user_no)
        return {"status": "success", "message": "Record updated successfully."}
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as exc:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.post("/reports")
def generate_reports(payload: ReportRequest):
    try:
        cache_key = (
            "report",
            payload.user_no,
            payload.upload_id,
            payload.report_type,
            payload.month or "",
        )
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached
        data = generate_report(
            report_type=payload.report_type,
            user_no=payload.user_no,
            upload_id=payload.upload_id,
            month=payload.month,
        )
        return set_cached_result(cache_key, data, ttl_seconds=60)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/reports/batch")
def generate_report_batch(payload: ReportBatchRequest):
    months = tuple(dict.fromkeys(month for month in payload.months if month))
    if not months:
        raise HTTPException(status_code=422, detail="At least one month is required.")
    try:
        cache_key = ("report_batch", payload.user_no, payload.report_type, *months)
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached
        data = generate_report(
            report_type=payload.report_type,
            user_no=payload.user_no,
            months=list(months),
        )
        return set_cached_result(cache_key, data, ttl_seconds=60)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.get("/reports/{report_type}")
def get_financial_report(report_type: str, user_no: int = Query(...), month: str = Query(...), upload_id: int | None = Query(None),):
    try:
        cache_key = ("report", user_no, upload_id, report_type, month or "")
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached
        data = generate_report(
            report_type=report_type,
            user_no=user_no,
            upload_id=upload_id,
            month=month,
        )
        return set_cached_result(cache_key, data, ttl_seconds=60)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/forecast")
def get_forecast(
    user_no: int = Query(...),
    periods: int = Query(12, ge=1, le=120),
):

    try:
        cache_key = ("forecast", user_no, periods)
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached
        dataset_paths = get_dataset_paths(user_no)
        schedule_path = get_business_schedule_path(dataset_paths)
        completed = subprocess.run(
            [
                find_rscript(),
                "--vanilla",
                str(FORECAST_R_SCRIPT),
                str(user_no),
                str(periods),
                str(schedule_path) if schedule_path else "",
            ],
            capture_output=True, 
            text=True, 
            cwd=str(FORECAST_R_SCRIPT.parent), 
            timeout=120,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stdout.strip() or completed.stderr.strip())

        raw = completed.stdout.strip()
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1:
            raw = raw[start:end + 1]
        result = json.loads(raw)
        result["dataset_context"] = dataset_provenance(dataset_paths)
        return set_cached_result(cache_key, result, ttl_seconds=120)
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print("Backend Forecast Error:", error_msg)
        raise HTTPException(status_code=500, detail=str(e) or "R script execution failed")


@app.get("/insights")
def get_business_insights(user_no: int = Query(...)):
    conn = None
    cursor = None

    try:
        cache_key = ("insights", user_no)
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                transaction_date,
                account_name,
                transaction_type,
                amount,
                status
            FROM records
            WHERE user_no = %s
            ORDER BY transaction_date, ref_no
            """,
            (user_no,),
        )

        records_payload = [
            {
                "transaction_date": row["transaction_date"].isoformat(),
                "account_name": row["account_name"],
                "transaction_type": row["transaction_type"],
                "amount": float(row["amount"]),
                "status": row["status"],
            }
            for row in cursor.fetchall()
        ]

        completed = subprocess.run(
            [
                find_rscript(),
                "--vanilla",
                INSIGHTS_R_SCRIPT.as_posix(),
                "-",
            ],
            input=json.dumps({"user_no": user_no, "records": records_payload}),
            capture_output=True,
            text=True,
            cwd=str(INSIGHTS_R_SCRIPT.parent),
            timeout=60,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())

        raw = completed.stdout.strip()
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end == -1:
            raise RuntimeError("R insights script returned invalid JSON.")

        result = json.loads(raw[start:end + 1])
        if result.get("status") == "failed":
            raise RuntimeError(result.get("error", "R insights generation failed."))

        dataset_paths = get_dataset_paths(user_no)
        dataset_insights = build_dataset_insights(dataset_paths, records_payload)
        if dataset_insights:
            result.setdefault("insights", []).extend(dataset_insights)
        result["datasets_connected"] = [path.name for path in dataset_paths]
        return set_cached_result(cache_key, result, ttl_seconds=120)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.post("/insights/datasets", status_code=201)
async def upload_insight_dataset(
    user_no: int = Form(...),
    file: UploadFile = File(...),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="Only CSV datasets are supported.")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Dataset must be 10 MB or smaller.")
    try:
        path = save_user_dataset(user_no, file.filename, content)
        invalidate_user_cache(user_no)
        parsed = build_dataset_insights([path], [])
        return {
            "status": "success",
            "filename": path.name,
            "insights_ready": len(parsed),
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/simulation/initial-inputs")
async def get_simulation_initial_inputs(user_no: int = Query(...)):
    """Build simulator defaults from the user's active records in this month."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SHOW COLUMNS FROM records")
        record_columns = {row["Field"] for row in cursor.fetchall()}
        quantity_column = next(
            (
                column
                for column in ("quantity", "sales_volume", "units")
                if column in record_columns
            ),
            None,
        )
        quantity_select = (
            f", `{quantity_column}` AS quantity" if quantity_column else ", NULL AS quantity"
        )
        cursor.execute(
            f"""
            SELECT transaction_date, description, account_name,
                   transaction_type, amount {quantity_select}
            FROM records
            WHERE user_no = %s
              AND status <> 'voided'
              AND YEAR(transaction_date) = YEAR(CURRENT_DATE())
              AND MONTH(transaction_date) = MONTH(CURRENT_DATE())
            ORDER BY transaction_date, ref_no
            """,
            (user_no,),
        )
        rows = cursor.fetchall()

        revenue_rows = [
            row for row in rows
            if str(row.get("account_name") or "").lower() == "revenue"
        ]
        revenue = sum(float(row.get("amount") or 0) for row in revenue_rows)

        def expense_total(*terms):
            total = 0.0
            for row in rows:
                if str(row.get("account_name") or "").lower() != "expense":
                    continue
                label = " ".join(
                    str(row.get(field) or "")
                    for field in ("description", "transaction_type")
                ).lower()
                if any(term in label for term in terms):
                    total += float(row.get("amount") or 0)
            return total

        recorded_quantities = [
            float(row["quantity"])
            for row in revenue_rows
            if row.get("quantity") is not None and float(row["quantity"]) > 0
        ]
        # If the deployed records table has no quantity-like column, each revenue
        # line is treated as one recorded sale.
        volume = sum(recorded_quantities) if recorded_quantities else len(revenue_rows)
        if float(volume).is_integer():
            volume = int(volume)
        price = revenue / volume if volume else 0
        return {
            "status": "success",
            "has_current_month_records": bool(rows),
            "source_period": date.today().strftime("%Y-%m"),
            "record_count": len(rows),
            "price": round(price, 2),
            "volume": volume,
            "marketing": round(expense_total("marketing", "advertis", "promotion"), 2),
            "raw_material": round(
                expense_total("raw material", "ingredient", "inventory", "cogs", "cost of goods"),
                2,
            ),
            "wages": round(expense_total("wage", "salary", "labor", "payroll"), 2),
            "utilities": round(
                expense_total("utilit", "electric", "water", "fuel", "gas"),
                2,
            ),
            "seasonality": 0,
            "inflation": 0,
            "competition": 0,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


class SimulationRequest(BaseModel):
    user_no: int
    price: float = 0
    volume: int = 0
    marketing: float = 0
    raw_material: float = 0
    wages: float = 0
    utilities: float = 0
    seasonality: float = 0
    inflation: float = 0
    competition: float = 0

@app.post("/simulate")
async def run_simulation(payload: SimulationRequest):

    try:
        completed = subprocess.run(
            [
                find_rscript(),
                "--vanilla",
                str(SIMULATION_R_SCRIPT),
                str(payload.user_no),
                str(payload.price),
                str(payload.volume),
                str(payload.marketing),
                str(payload.raw_material),
                str(payload.wages),
                str(payload.utilities),
                str(payload.seasonality),
                str(payload.inflation),
                str(payload.competition),
            ],
            capture_output=True,
            text=True,
            cwd=str(SIMULATION_R_SCRIPT.parent),
            timeout=120,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stdout.strip() or completed.stderr.strip())

        raw = completed.stdout.strip()
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1:
            raw = raw[start:end + 1]
        return json.loads(raw)
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
