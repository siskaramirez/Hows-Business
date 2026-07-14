from fastapi import FastAPI
from fastapi.responses import FileResponse

from services.template_generator import generate_transaction_template
from api import records


app = FastAPI(
    title="How's Business API"
)


app.include_router(records.router)


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


