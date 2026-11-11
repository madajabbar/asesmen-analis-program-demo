# tests/test_validation.py
# Unit Kompetensi: J.620100.033.02 (Uji Unit) — validasi service
#
# Menguji fungsi validasi murni (tanpa DB) pada src/service.py.
# Pola Arrange-Act-Assert; mencakup data normal, boundary, dan tidak valid.

import pytest

from src.service import validasi_jumlah, validasi_kode


# --- validasi_jumlah ------------------------------------------------------
@pytest.mark.parametrize("jumlah,expected", [
    (1, True),      # normal: positif
    (999, True),    # normal: besar
    (0, False),     # boundary: nol -> tidak valid
    (-1, False),    # tidak valid: negatif
    (2.5, False),   # tidak valid: bukan bulat
    (None, False),  # tidak valid: None
])
def test_validasi_jumlah(jumlah, expected):
    ok, pesan = validasi_jumlah(jumlah)
    assert ok is expected
    if not expected:
        assert pesan  # pesan error tersedia


# --- validasi_kode --------------------------------------------------------
@pytest.mark.parametrize("kode,expected", [
    ("VC-0001", True),        # normal
    ("A", True),              # normal: pendek
    ("x" * 40, True),         # boundary: tepat 40 karakter
    ("x" * 41, False),        # boundary: lebih dari 40
    ("", False),              # tidak valid: kosong
    ("   ", False),           # tidak valid: spasi saja
    ("VC 0001", False),       # tidak valid: ada spasi
    ("VC@123", False),        # tidak valid: karakter khusus
    (123, False),             # tidak valid: bukan string
])
def test_validasi_kode(kode, expected):
    ok, pesan = validasi_kode(kode)
    assert ok is expected
    if not expected:
        assert pesan
