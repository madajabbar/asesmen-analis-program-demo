# tests/test_integration.py
# Unit Kompetensi: J.620100.034.02 (Uji Integrasi)
#
# Uji integrasi yang BENAR-BENAR terkoneksi ke MySQL. Otomatis di-skip
# bila basis data tidak tersedia (pytest.mark.skipif), tetapi pada run
# E2E basis data WAJIB tersedia sehingga seluruh uji ini dijalankan.

import itertools

import pytest

from src.db import get_connection, ping
from src.config import Config
from src import service

# Skip otomatis bila DB tidak bisa diping.
pytestmark = pytest.mark.skipif(
    not ping(),
    reason="Basis data MySQL tidak tersedia (skip otomatis)",
)


@pytest.fixture(scope="module")
def ids_produk():
    """Ambil id produk 'Pulpen Standard AE7' (stok 300) dan 'Wajan Anti
    Lengket' (stok 2) untuk uji sukses & gagal."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, stok FROM produk WHERE nama = 'Pulpen Standard AE7'")
            pulpen = cur.fetchone()
            cur.execute("SELECT id, stok FROM produk WHERE nama = 'Wajan Anti Lengket'")
            wajan = cur.fetchone()
    return {"pulpen": pulpen, "wajan": wajan}


def test_koneksi_dan_database_ada():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DATABASE()")
            assert cur.fetchone()[0] == "asesmen_demo"


def _stok_terakhir(produk_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT stok FROM produk WHERE id = %s", (produk_id,))
            return cur.fetchone()[0]


def _voucher_ada(kode):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM voucher WHERE kode = %s", (kode,))
            return cur.fetchone()[0] > 0


def test_buat_voucher_sukses_kurangi_stok_dan_log(ids_produk):
    produk_id, stok_awal = ids_produk["pulpen"]
    kode = f"VC-INT-{next(itertools.count())}"

    # Act
    vid = service.buat_voucher(kode, produk_id, 5)

    # Assert
    stok_akhir = _stok_terakhir(produk_id)
    assert stok_akhir == stok_awal - 5          # stok berkurang
    assert _voucher_ada(kode)                    # voucher tersimpan

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Trigger mencatat ke stok_log
            cur.execute(
                "SELECT stok_sebelum, stok_sesudah, perubahan FROM stok_log "
                "WHERE produk_id = %s ORDER BY id DESC LIMIT 1",
                (produk_id,),
            )
            log = cur.fetchone()
            assert log == (stok_awal, stok_awal - 5, -5)

            # Function menghitung total voucher (harga * jumlah = 5)
            cur.execute("SELECT harga FROM produk WHERE id = %s", (produk_id,))
            harga = cur.fetchone()[0]
            cur.execute("SELECT fn_total_voucher(%s)", (kode,))
            total = cur.fetchone()[0]
            assert float(total) == float(harga) * 5


def test_buat_voucher_stok_kurang_rollback(ids_produk):
    produk_id, stok_awal = ids_produk["wajan"]  # stok 2
    kode = f"VC-INT-GAGAL-{next(itertools.count())}"

    # Act: minta jumlah jauh melebihi stok.
    with pytest.raises(ValueError):
        service.buat_voucher(kode, produk_id, 999)

    # Assert: data TIDAK berubah (rollback).
    assert _stok_terakhir(produk_id) == stok_awal
    assert not _voucher_ada(kode)


def test_buat_voucher_produk_tidak_ada():
    with pytest.raises(ValueError):
        service.buat_voucher("VC-INT-NOL", 999999, 1)


def test_laporan_berisi_data():
    lap = service.laporan()
    assert lap["total_produk"] > 0
    assert lap["nilai_persediaan"] > 0
    assert len(lap["per_kategori"]) >= 3


def test_view_ringkasan_stok_tersedia():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM v_ringkasan_stok")
            assert cur.fetchone()[0] > 0


def test_stored_procedure_langsung(ids_produk):
    produk_id = ids_produk["pulpen"][0]
    kode = f"VC-SP-{next(itertools.count())}"

    # Baca stok segar tepat sebelum CALL (agar uji terisolasi dari uji lain).
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT stok FROM produk WHERE id = %s", (produk_id,))
            stok_awal = cur.fetchone()[0]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.callproc("sp_buat_voucher", (kode, produk_id, 3))
            conn.commit()
            cur.execute("SELECT stok FROM produk WHERE id = %s", (produk_id,))
            assert cur.fetchone()[0] == stok_awal - 3
