from threading import Lock

import mysql.connector
from mysql.connector import pooling
from config import load_db_config

_db_pool = None
_pool_lock = Lock()
_records_schema_lock = Lock()
_records_schema_ready = False


def get_db_connection():
    global _db_pool

    if _db_pool is None:
        with _pool_lock:
            if _db_pool is None:
                _db_pool = pooling.MySQLConnectionPool(
                    pool_name="delikart_pool",
                    pool_size=5,
                    use_pure=True,
                    **load_db_config(),
                )

    return _db_pool.get_connection()


def ensure_user_scoped_invoice_index(conn):
    """Replace a global invoice unique index with a per-user unique index."""
    global _records_schema_ready
    if _records_schema_ready:
        return

    with _records_schema_lock:
        if _records_schema_ready:
            return

        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SHOW INDEX FROM records")
            indexes = {}
            for row in cursor.fetchall():
                indexes.setdefault(row["Key_name"], []).append(row)

            has_user_invoice_index = False
            for index_name, rows in indexes.items():
                ordered = sorted(rows, key=lambda row: int(row["Seq_in_index"]))
                columns = [row["Column_name"] for row in ordered]
                is_unique = int(ordered[0]["Non_unique"]) == 0
                if is_unique and columns == ["user_no", "invoice_no"]:
                    has_user_invoice_index = True
                if is_unique and columns == ["invoice_no"]:
                    safe_name = index_name.replace("`", "``")
                    cursor.execute(f"ALTER TABLE records DROP INDEX `{safe_name}`")

            if not has_user_invoice_index:
                cursor.execute(
                    """
                    CREATE UNIQUE INDEX ux_records_user_invoice
                    ON records (user_no, invoice_no)
                    """
                )
            conn.commit()
            _records_schema_ready = True
        finally:
            cursor.close()
