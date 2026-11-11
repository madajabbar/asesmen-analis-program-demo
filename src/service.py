# src/service.py
# Unit Kompetensi:
#   - J.620100.021.02 (Akses Basis Data)   — transaksi, koneksi
#   - J.620100.033.02 (Uji Unit)            — fungsi validasi murni
#
# Lapisan layanan (business logic) aplikasi. Memisahkan logika dari
# antarmuka CLI agar dapat diuji unit (fungsi murni) dan integrasi
# (fungsi yang menyentuh basis data) secara terpisah.
#
# MENGAPA memisahkan validasi murni: fungsi seperti `validasi_jumlah`
# tidak perlu basis data sehingga dapat diuji unit dengan cepat tanpa
# menyiapkan MySQL (lihat tests/test_validation.py).

from typing import List, Optional, Tuple

import mysql.connector
from mysql.connector import Error as MySQLError

from .db import get_connection

# ---------------------------------------------------------------------
# Fungsi validasi MURNI (tanpa DB) — target uji unit
# ---------------------------------------------------------------------

def validasi_jumlah(jumlah: int) -> Tuple[bool, str]:
    """Memvalidasi jumlah voucher: harus bilangan bulat positif.

    MENGAPA digunakan batas numerik eksplisit: mencegah data negatif/nol
    masuk ke transaksi yang menggerus stok.
    """
    if not isinstance(jumlah, int):
        return False, "jumlah harus bilangan bulat"
    if jumlah <= 0:
        return False, "jumlah harus lebih besar dari nol"
    return True, "ok"


def validasi_kode(kode: str) -> Tuple[bool, str]:
    """Memvalidasi kode voucher: non-kosong, maks 40 karakter, alfanumerik.

    MENGAPA tanda hubung diizinkan: kode voucher sering memuat awalan
    seperti 'VC-'. Pembatasan ini mencegah masukan aneh/mencurigakan.
    """
    if not isinstance(kode, str) or not kode.strip():
        return False, "kode tidak boleh kosong"
    if len(kode) > 40:
        return False, "kode maksimal 40 karakter"
    if not all(c.isalnum() or c == "-" for c in kode):
        return False, "kode hanya boleh huruf, angka, dan tanda hubung"
    return True, "ok"


# ---------------------------------------------------------------------
# Operasi basis data (target uji integrasi)
# ---------------------------------------------------------------------

def list_produk(maks: int = 50) -> List[dict]:
    """Mengembalikan daftar produk (nama, kategori, harga, stok, status)."""
    query = """
        SELECT p.id, p.nama, k.nama AS kategori, p.harga, p.stok,
               p.min_stok,
               CASE WHEN p.stok = 0 THEN 'HABIS'
                    WHEN p.stok <= p.min_stok THEN 'MENIPIS'
                    ELSE 'CUKUP' END AS status
        FROM produk p JOIN kategori k ON k.id = p.kategori_id
        ORDER BY p.id LIMIT %s
    """
    with get_connection() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(query, (maks,))
            return cur.fetchall()


def cari_produk(kata_kunci: str, maks: int = 20) -> List[dict]:
    """Mencari produk berdasarkan nama (LIKE) dan juga nama kategori."""
    query = """
        SELECT p.id, p.nama, k.nama AS kategori, p.harga, p.stok, p.min_stok
        FROM produk p JOIN kategori k ON k.id = p.kategori_id
        WHERE p.nama LIKE %s OR k.nama LIKE %s
        ORDER BY p.nama LIMIT %s
    """
    pola = f"%{kata_kunci}%"
    with get_connection() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(query, (pola, pola, maks))
            return cur.fetchall()


def buat_voucher(kode: str, produk_id: int, jumlah: int) -> int:
    """Membuat voucher dalam satu transaksi: insert voucher + kurangi stok.

    - Stok tidak cukup -> ROLLBACK, data tidak berubah, melempar ValueError.
    - Stok cukup      -> COMMIT (trigger `stok_log` mencatat otomatis).
    Mengembalikan ID voucher yang baru dibuat.
    """
    ok, pesan = validasi_jumlah(jumlah)
    if not ok:
        raise ValueError(pesan)
    ok, pesan = validasi_kode(kode)
    if not ok:
        raise ValueError(pesan)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Baca harga (+ kunci baris agar aman terhadap race condition).
            cur.execute(
                "SELECT harga FROM produk WHERE id = %s FOR UPDATE",
                (produk_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError("produk tidak ditemukan")
            harga = float(row[0])

            # Kurangi stok HANYA bila masih cukup. ROW_COUNT()=0 => gagal.
            cur.execute(
                "UPDATE produk SET stok = stok - %s "
                "WHERE id = %s AND stok >= %s",
                (jumlah, produk_id, jumlah),
            )
            if cur.rowcount == 0:
                # Stok tidak cukup -> batalkan seluruh transaksi.
                conn.rollback()
                raise ValueError(
                    "Stok tidak mencukupi untuk membuat voucher"
                )

            cur.execute(
                "INSERT INTO voucher (kode, produk_id, jumlah, total_harga, status)"
                " VALUES (%s, %s, %s, %s, 'AKTIF')",
                (kode, produk_id, jumlah, harga * jumlah),
            )
            voucher_id = cur.lastrowid
        conn.commit()
        return voucher_id
    finally:
        conn.close()


def laporan() -> dict:
    """Merangkum laporan: nilai persediaan, jumlah produk, voucher aktif,
    dan ringkasan per kategori."""
    with get_connection() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT fn_nilai_persediaan() AS nilai")
            nilai = cur.fetchone()["nilai"]

            cur.execute("SELECT COUNT(*) AS total FROM produk")
            total_produk = cur.fetchone()["total"]

            cur.execute(
                "SELECT COUNT(*) AS aktif FROM voucher WHERE status = 'AKTIF'"
            )
            voucher_aktif = cur.fetchone()["aktif"]

            cur.execute(
                """
                SELECT k.nama AS kategori,
                       COUNT(p.id) AS jumlah_produk,
                       COALESCE(SUM(p.harga * p.stok), 0) AS nilai
                FROM kategori k
                LEFT JOIN produk p ON p.kategori_id = k.id
                GROUP BY k.id, k.nama ORDER BY k.nama
                """
            )
            per_kategori = cur.fetchall()

    return {
        "nilai_persediaan": float(nilai),
        "total_produk": total_produk,
        "voucher_aktif": voucher_aktif,
        "per_kategori": per_kategori,
    }
