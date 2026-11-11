# tests/test_web.py
# Uji web (Flask test client) — Fase 2. Di-skip otomatis bila DB mati.

import itertools
import time

import pytest

from src.db import get_connection, ping
from web.app import create_app

pytestmark = pytest.mark.skipif(
    not ping(),
    reason="Basis data MySQL tidak tersedia (skip otomatis)",
)

_SEQ = itertools.count(int(time.time_ns()))
def _kode(prefix):
    return f"{prefix}-{next(_SEQ)}"

WARNA_PRIMER = "#0071E3"


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _query(sql, params=()):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def _stok(produk_id):
    return _query("SELECT stok FROM produk WHERE id = %s", (produk_id,))[0]


def test_dashboard_200_memuat_angka_nyata(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    # Angka dari DB nyata, bukan karangan.
    total = _query("SELECT COUNT(*) FROM produk")[0]
    assert f"{total}" in body
    assert "Ringkasan Stok per Kategori" in body
    assert "Data dari view MySQL" in body


def test_produk_200_memuat_nama_seed(client):
    resp = client.get("/produk")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Laptop ASUS VivoBook" in body
    assert "Pulpen Standard AE7" in body


def test_produk_pencarian(client):
    resp = client.get("/produk?q=Mouse")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Mouse Wireless Logitech" in body
    assert "Laptop ASUS VivoBook" not in body


def test_voucher_daftar(client):
    resp = client.get("/voucher")
    assert resp.status_code == 200
    assert "Voucher" in resp.get_data(as_text=True)


def test_buat_voucher_sukses_kurangi_stok(client):
    produk_id = _query("SELECT id FROM produk WHERE nama = 'Kertas A4 80gsm'")[0]
    stok_awal = _stok(produk_id)
    kode = _kode("PV-WEB")

    resp = client.post(
        "/voucher/baru",
        data={"kode": kode, "produk_id": str(produk_id), "jumlah": "7"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "berhasil dibuat" in body
    assert kode in body
    # Stok benar-benar berkurang sesuai jumlah.
    assert _stok(produk_id) == stok_awal - 7


def test_buat_voucher_stok_melebihi_ditolak(client):
    produk_id = _query("SELECT id FROM produk WHERE nama = 'Wajan Anti Lengket'")[0]
    stok_awal = _stok(produk_id)
    kode = _kode("PV-WEB-GAGAL")

    resp = client.post(
        "/voucher/baru",
        data={"kode": kode, "produk_id": str(produk_id), "jumlah": "999"},
        follow_redirects=True,
    )
    assert resp.status_code == 400
    assert "Stok tidak mencukupi" in resp.get_data(as_text=True)
    # Data TIDAK berubah (rollback).
    assert _stok(produk_id) == stok_awal


def test_buat_voucher_kode_duplikat_ditolak(client):
    produk_id = _query("SELECT id FROM produk WHERE nama = 'Kertas A4 80gsm'")[0]
    kode = _kode("PV-WEB-DUP")
    data = {"kode": kode, "produk_id": str(produk_id), "jumlah": "2"}
    client.post("/voucher/baru", data=data)
    # Kode yang sama -> ditolak, bukan crash 500.
    resp = client.post("/voucher/baru", data=data)
    assert resp.status_code == 400
    assert "sudah digunakan" in resp.get_data(as_text=True)


def test_laporan_memuat_stok_log(client):
    resp = client.get("/laporan")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "stok_log" in body
    entri = _query("SELECT COUNT(*) FROM stok_log")[0]
    assert entri > 0
