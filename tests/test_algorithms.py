# tests/test_algorithms.py
# Unit Kompetensi: J.620100.033.02 (Uji Unit) — algoritma
#
# Pola Arrange-Act-Assert: menyiapkan data (Arrange), memanggil algoritma
# (Act), memverifikasi hasil (Assert). Tidak memerlukan basis data.

import random
import pytest

from src.algorithms import quick_sort, merge_sort, binary_search


# --- Arrange: data uji (normal, boundary, tidak valid untuk binary_search) ---
KASUS_SORT = [
    [],                     # kosong (boundary)
    [7],                    # satu elemen (boundary)
    [3, 3, 3],              # semua sama
    [5, 1, 4, 2, 3],        # acak
    list(range(100)),       # sudah terurut
    list(range(100, 0, -1)),  # terurut terbalik
]


@pytest.mark.parametrize("data", KASUS_SORT)
def test_quick_sort_menghasilkan_terurut(data):
    hasil = quick_sort(data)                 # Act
    assert hasil == sorted(data)             # Assert


@pytest.mark.parametrize("data", KASUS_SORT)
def test_merge_sort_menghasilkan_terurut(data):
    hasil = merge_sort(data)
    assert hasil == sorted(data)


def test_quick_sort_tidak_mengubah_input_asli():
    data = [3, 1, 2]
    quick_sort(data)
    assert data == [3, 1, 2]  # fungsi murni, input tidak diubah


def test_binary_search_ditemukan():
    data = sorted([9, 4, 7, 1, 5])
    assert binary_search(data, 4) == data.index(4)


def test_binary_search_tidak_ditemukan():
    data = [1, 3, 5, 7, 9]
    assert binary_search(data, 6) is None


def test_binary_search_boundary_awal_akhir():
    data = [2, 4, 6, 8]
    assert binary_search(data, 2) == 0   # elemen pertama
    assert binary_search(data, 8) == 3   # elemen terakhir


def test_binary_search_daftar_kosong():
    assert binary_search([], 1) is None
