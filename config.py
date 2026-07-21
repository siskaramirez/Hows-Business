import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "db_config.json"


def load_db_config():
    if not CONFIG_FILE.exists():
        return {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "",
            "database": "delikart",
        }

    import json
    with CONFIG_FILE.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_db_config(config):
    import json
    with CONFIG_FILE.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)