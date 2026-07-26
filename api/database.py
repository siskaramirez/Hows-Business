from threading import Lock

import mysql.connector
from mysql.connector import pooling
from config import load_db_config

_db_pool = None
_pool_lock = Lock()


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
