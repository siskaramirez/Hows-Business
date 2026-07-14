from unittest import result

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from services.template_generator import generate_transaction_template
from api import records

import subprocess
import json
import os
import pandas as pd


app = FastAPI(
    title="How's Business API"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(records.router)

UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


@app.get("/")
def home():
    return {
        "message": "How's Business API is running"
    }

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


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    save_path = f"uploads/{file.filename}"

    with open(save_path, "wb") as buffer:
        buffer.write(await file.read())

    # Read the uploaded Excel file
    df = pd.read_excel(save_path)

    print("=== Uploaded Data ===")
    print(df.head())

    return {"message": "Upload successful"}


@app.post("/extract")
async def extract_excel(file: UploadFile = File(...)):

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

    try:

        result = subprocess.run(
            [
                r"C:\Program Files\R\R-4.6.1\bin\Rscript.exe",
                "R/extract_data.R",
                file_path
            ],
            capture_output=True,
            text=True,
            check=True
)
        print("===== R STDOUT =====")
        print(result.stdout)

        extracted_data = json.loads(result.stdout)

        for row in extracted_data:

            records.records.append({
                "id": len(records.records) + 1,
                "date": row["Date"],
                "description": row["Description"],
                "account_name": row["Account Name"],
                "amount": float(row["Amount"]),
                "payment_method": row.get("Payment Method"),
                "transaction_type": row.get("Account Type"),
                "invoice_no": row.get("Invoice No."),
                "status": "active"
            })

        return {
            "status": "success",
            "imported": len(extracted_data)
        }



    except subprocess.CalledProcessError as e:

        print("===== R STDERR =====")
        print(e.stderr)

        return {
            "status": "failed",
            "message": e.stderr
        }

    except Exception as e:

        print("===== PYTHON ERROR =====")
        print(e)

        return {
            "status": "failed",
            "message": str(e)
        }
    

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )