import csv
import io
import re
from datetime import date, datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
REFERENCE_DIR = BASE_DIR / "data" / "reference_datasets"
USER_DATASET_DIR = BASE_DIR / "uploads" / "insight_datasets"


def _safe_filename(filename: str) -> str:
    name = Path(filename).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    if not name or name in {".", ".."}:
        raise ValueError("Invalid dataset filename.")
    return name


def save_user_dataset(user_no: int, filename: str, content: bytes) -> Path:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV datasets must use UTF-8 encoding.") from exc
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or not any(any(cell.strip() for cell in row) for row in rows):
        raise ValueError("The CSV dataset is empty.")

    destination = USER_DATASET_DIR / str(user_no)
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / _safe_filename(filename)
    path.write_text(text, encoding="utf-8", newline="")
    return path


def get_dataset_paths(user_no: int) -> list[Path]:
    paths = sorted(REFERENCE_DIR.glob("*.csv")) if REFERENCE_DIR.exists() else []
    user_dir = USER_DATASET_DIR / str(user_no)
    if user_dir.exists():
        paths.extend(sorted(user_dir.glob("*.csv")))
    return paths


def classify_dataset(path: Path) -> str:
    """Classify supported datasets from their schema, never attachment order."""
    try:
        rows = _read_rows(path)
    except (OSError, UnicodeError, csv.Error):
        return "unknown"
    header_text = " ".join(cell for row in rows[:5] for cell in row).lower()
    first_row = {cell.strip().lower() for cell in rows[0]} if rows else set()
    if {"phase", "start_date", "end_date"}.issubset(first_row):
        return "business_schedule"
    if "commodity" in header_text and "weight" in header_text:
        return "cpi_weights"
    if any(row and row[0].strip().lower() == "..restaurants" for row in rows):
        return "industry_benchmark"
    return "unknown"


def get_business_schedule_path(paths: list[Path]) -> Path | None:
    return next(
        (path for path in paths if classify_dataset(path) == "business_schedule"),
        None,
    )


def dataset_provenance(paths: list[Path]) -> dict:
    return {
        "business_schedule": [
            path.name for path in paths if classify_dataset(path) == "business_schedule"
        ],
        "industry_benchmark": [
            path.name for path in paths if classify_dataset(path) == "industry_benchmark"
        ],
        "cpi_weights": [
            path.name for path in paths if classify_dataset(path) == "cpi_weights"
        ],
    }


def _read_rows(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle))


def _metric(value, label):
    return {"value": value, "label": label}


def _calendar_insight(path: Path, rows: list[list[str]], records: list[dict]):
    if not rows or "Start_Date" not in rows[0] or "End_Date" not in rows[0]:
        return None
    entries = []
    for row in csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig"))):
        try:
            start = datetime.strptime(row["Start_Date"], "%m/%d/%Y").date()
            end = datetime.strptime(row["End_Date"], "%m/%d/%Y").date()
        except (KeyError, TypeError, ValueError):
            continue
        entries.append((start, end, row))
    if not entries:
        return None

    today = date.today()
    upcoming = next((item for item in entries if item[1] >= today), entries[-1])
    start, end, row = upcoming
    sales_dates = []
    for record in records:
        if str(record.get("account_name", "")).lower() != "revenue":
            continue
        try:
            sales_dates.append(datetime.fromisoformat(record["transaction_date"]).date())
        except (KeyError, TypeError, ValueError):
            pass
    overlapping_sales = sum(1 for value in sales_dates if start <= value <= end)
    label = row.get("Phase") or row.get("Term_Or_Block") or "calendar period"
    return {
        "id": f"dataset_calendar_{path.stem.lower()}",
        "category": "Demand",
        "eyebrow": "DATASET DEMAND SIGNAL",
        "title": f"Plan demand around {label}",
        "summary": (
            f"The connected calendar marks {start:%b %d}–{end:%b %d, %Y} "
            f"as {label}. Use this window when scheduling inventory and promotions."
        ),
        "estimate": f"{len(entries)} periods mapped",
        "detail_title": f"{row.get('Term_Or_Block', 'Calendar')} — {label}",
        "detail": (
            f"{row.get('Notes', 'External calendar period')}. "
            f"{overlapping_sales} recorded revenue entries currently overlap this period."
        ),
        "metrics": [
            _metric(f"{start:%b %d}", "Starts"),
            _metric(f"{end:%b %d}", "Ends"),
            _metric(str(overlapping_sales), "Sales in window"),
        ],
        "actions": [
            "Compare sales inside this period with the weeks immediately before it.",
            "Schedule promotions before expected high-demand school activities.",
            "Adjust inventory and staffing only after checking the signal against your own sales.",
        ],
        "has_enough_data": True,
        "source_dataset": path.name,
    }


def _restaurant_benchmark_insight(path: Path, rows: list[list[str]]):
    restaurant = next(
        (row for row in rows if row and row[0].strip().lower() == "..restaurants"),
        None,
    )
    if not restaurant or len(restaurant) < 6:
        return None
    try:
        establishments = float(restaurant[1])
        income = float(restaurant[4])
        expense = float(restaurant[5])
    except (TypeError, ValueError):
        return None
    ratio = expense / income * 100 if income else 0
    return {
        "id": f"dataset_industry_{path.stem.lower()}",
        "category": "Cost Control",
        "eyebrow": "PSA INDUSTRY BENCHMARK",
        "title": f"Restaurant expenses were {ratio:.1f}% of income",
        "summary": (
            "Use this external small-establishment statistic as context, not as a "
            "target; your current records remain the basis of the recommendation."
        ),
        "estimate": f"{int(establishments):,} establishments",
        "detail_title": "Accommodation and food service benchmark",
        "detail": (
            "The connected PSA table reports values in thousand pesos for restaurants "
            "with fewer than 20 employees in 2016."
        ),
        "metrics": [
            _metric(f"{ratio:.1f}%", "Expense/income"),
            _metric(f"{income:,.0f}K", "Total income"),
            _metric(f"{expense:,.0f}K", "Total expense"),
        ],
        "actions": [
            "Compare your latest expense-to-revenue ratio with your own prior months.",
            "Investigate material, labor, and utility categories driving any increase.",
            "Treat the older industry figure as context and prioritize recent business records.",
        ],
        "has_enough_data": True,
        "source_dataset": path.name,
    }


def _cpi_insight(path: Path, rows: list[list[str]]):
    header_text = " ".join(cell for row in rows[:5] for cell in row).lower()
    if "commodity" not in header_text or "weight" not in header_text:
        return None
    commodities = []
    for row in rows:
        if len(row) < 3:
            continue
        try:
            weight = float(row[2])
        except (TypeError, ValueError):
            continue
        if row[1].strip():
            commodities.append((row[1].strip(), weight))
    if not commodities:
        return None
    top = sorted(commodities, key=lambda item: item[1], reverse=True)[:3]
    return {
        "id": f"dataset_cpi_{path.stem.lower()}",
        "category": "Cost Control",
        "eyebrow": "CPI INPUT CONTEXT",
        "title": "Prioritize price checks for the highest-weight food inputs",
        "summary": (
            "The connected NCR CPI-weight table identifies cereals, rice, and fresh meat "
            "among the more material listed food-input groups."
        ),
        "estimate": f"{len(commodities)} inputs mapped",
        "detail_title": "Commodity weights connected to cost recommendations",
        "detail": "Higher table weights indicate greater importance within the supplied CPI basket.",
        "metrics": [
            _metric(f"{weight:.1f}", re.sub(r"^\d+(?:\.\d+)*\s*-\s*", "", name)[:22])
            for name, weight in top
        ],
        "actions": [
            "Track supplier price changes for the highest-weight ingredients each month.",
            "Compare alternate suppliers before changing menu prices.",
            "Combine CPI context with actual purchase records before acting.",
        ],
        "has_enough_data": True,
        "source_dataset": path.name,
    }


def build_dataset_insights(paths: list[Path], records: list[dict]) -> list[dict]:
    insights = []
    for path in paths:
        try:
            rows = _read_rows(path)
        except (OSError, UnicodeError, csv.Error):
            continue
        candidates = (
            _calendar_insight(path, rows, records),
            _restaurant_benchmark_insight(path, rows),
            _cpi_insight(path, rows),
        )
        insights.extend(candidate for candidate in candidates if candidate)
    return insights
