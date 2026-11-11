# src/db.py
# Unit Kompetensi: J.620100.021.02 (Akses Basis Data)
#
# Helper koneksi basis data memakai mysql-connector-python.
#
# MENGAPA memakai mysql-connector-python: resmi dari MySQL, murni Python
# (tanpa dependensi C), cukup untuk satu koneksi sederhana.

import mysql.connector
from mysql.connector import Error as MySQLError

from .config import Config


def get_connection():
    """Membuka koneksi baru ke basis data asesmen_demo."""
    return mysql.connector.connect(**Config.dsn())


def ping() -> bool:
    """Menguji ketersediaan basis data. Mengembalikan True bila tersedia."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True
    except (MySQLError, OSError):
        return False
