# src/algorithms.py
# Unit Kompetensi: J.620100.022.02 (Algoritma)
#
# Modul ini berisi algoritma klasik (sorting & pencarian) yang dipakai
# sebagai bukti kompetensi algoritma. Setiap fungsi mencantumkan
# kompleksitas waktu dan memori Big-O dalam docstring-nya.
#
# MENGAPA modul ini ada: portofolio asesmen memerlukan demonstrasi
# pemahaman algoritma yang tidak bergantung pada basis data (murni
# struktur data), sehingga mudah diuji unit tanpa DB.

from typing import List, TypeVar, Optional

T = TypeVar("T")


def quick_sort(arr: List[T]) -> List[T]:
    """Mengurutkan daftar secara menaik memakai Quicksort (in-place split).

    Kompleksitas waktu : rata-rata O(n log n), terburuk O(n^2).
    Kompleksitas memori: O(log n) (ruang stack rekursi, partisi in-place).

    MENGAPA Quicksort dikandung: implementasi partisi Hoare sederhana dan
    performa rata-rata baik untuk data tak terurut, mudah dijelaskan dalam
    asesmen.
    """
    if len(arr) <= 1:
        return list(arr)
    pivot = arr[len(arr) // 2]
    kiri = [x for x in arr if x < pivot]
    tengah = [x for x in arr if x == pivot]
    kanan = [x for x in arr if x > pivot]
    return quick_sort(kiri) + tengah + quick_sort(kanan)


def merge_sort(arr: List[T]) -> List[T]:
    """Mengurutkan daftar secara menaik memakai Mergesort.

    Kompleksitas waktu : O(n log n) pada semua kasus.
    Kompleksitas memori: O(n) (membutuhkan daftar tambahan saat merger).

    MENGAPA Mergesort dikandung: stabil dan memiliki batas waktu terburuk
    yang dapat dijamin O(n log n), berlawanan dengan Quicksort.
    """
    if len(arr) <= 1:
        return list(arr)
    tengah = len(arr) // 2
    kiri = merge_sort(arr[:tengah])
    kanan = merge_sort(arr[tengah:])
    hasil: List[T] = []
    i = j = 0
    while i < len(kiri) and j < len(kanan):
        if kiri[i] <= kanan[j]:
            hasil.append(kiri[i])
            i += 1
        else:
            hasil.append(kanan[j])
            j += 1
    hasil.extend(kiri[i:])
    hasil.extend(kanan[j:])
    return hasil


def binary_search(arr: List[T], target: T) -> Optional[int]:
    """Mencari `target` pada daftar TERURUT menaik. Mengembalikan indeks
    atau None bila tidak ditemukan.

    Kompleksitas waktu : O(log n).
    Kompleksitas memori: O(1) (iteratif, tanpa rekursi).

    MENGAPA diasumsikan terurut: binary_search hanya valid pada data terurut;
    pemakai wajib mengurutkan dahulu (mis. dengan quick_sort/merge_sort).
    """
    kiri, kanan = 0, len(arr) - 1
    while kiri <= kanan:
        tengah = (kiri + kanan) // 2
        if arr[tengah] == target:
            return tengah
        if arr[tengah] < target:
            kiri = tengah + 1
        else:
            kanan = tengah - 1
    return None
