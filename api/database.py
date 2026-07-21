import json
import os
import mysql.connector
from mysql.connector import pooling

with open(os.path.join(os.path.dirname(__file__), "..", "db_config.json"), "r") as f:
    db_config = json.load(f)

db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="delikart_pool",
    pool_size=5,
    host=db_config["host"],
    port=db_config["port"],
    user=db_config["user"],
    password=db_config["password"],
    database=db_config["database"]
)

def get_db_connection():
    return db_pool.get_connection()