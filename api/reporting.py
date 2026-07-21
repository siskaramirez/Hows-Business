import json
import os
import subprocess
import tempfile
from pathlib import Path

from config import load_db_config

BASE_DIR = Path(__file__).resolve().parent.parent
R_SCRIPT = BASE_DIR / "R" / "run_reports.R"

def generate_report(
    user_no: int,
    upload_id: int | None = None,
    report_type: str = "income_statement",
    month: str | None = None,
):
    if not R_SCRIPT.exists():
        raise FileNotFoundError(f"R report script not found: {R_SCRIPT}")

    payload = {
        "user_no": user_no,
        "upload_id": upload_id,
        "report_type": report_type,
        "month": month or "",
        "db": load_db_config(),
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        json.dump(payload, handle)
        temp_path = handle.name

    try:
        completed = subprocess.run(
            ["Rscript", str(R_SCRIPT), temp_path],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR),
            timeout=120,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())

        raw_output = completed.stdout.strip()
        if not raw_output:
            raise RuntimeError("R reports script returned no output")

        start = raw_output.find("{")
        end = raw_output.rfind("}")
        if start != -1 and end != -1 and end > start:
            raw_output = raw_output[start:end + 1]

        return json.loads(raw_output)
    
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)