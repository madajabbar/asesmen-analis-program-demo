# src/config.py
# Unit Kompetensi: J.620100.021.02 (Akses Basis Data)
#
# Memuat konfigurasi koneksi DB dari environment (.env). Nilai default
# cocok untuk docker compose lokal (lihat docker-compose.yml / .env.example).
#
# MENGAPA lewat env: kredensial tidak boleh dikeraskan di kode; pemisahan
# konfigurasi dari kode memudahkan penggantian lingkungan tanpa mengubah
# program.

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

# Muat .env bila ada (root proyek).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if load_dotenv is not None:
    load_dotenv(_PROJECT_ROOT / ".env")


class Config:
    """Wadah konfigurasi koneksi basis data."""

    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "app_asesmen")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "app_demo_lokal_456")
    DB_NAME = os.getenv("DB_NAME", "asesmen_demo")

    @classmethod
    def dsn(cls) -> dict:
        """Mengembalikan parameter koneksi dalam bentuk dict (mysql.connector)."""
        return {
            "host": cls.DB_HOST,
            "port": cls.DB_PORT,
            "user": cls.DB_USER,
            "password": cls.DB_PASSWORD,
            "database": cls.DB_NAME,
            "charset": "utf8mb4",
            "autocommit": False,
        }
