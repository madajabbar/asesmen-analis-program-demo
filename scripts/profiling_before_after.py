# scripts/profiling_before_after.py
# Unit Kompetensi: J.620100.031.01 (Profiling)
#
# Mengukur waktu eksekusi query SEBELUM dan SESUDAH dibuat index, pada
# tabel uji terpisah (tidak mengganggu data aplikasi). Sebelum: tanpa index
# (full scan). Sesudah: dengan index pada kolom nama (range scan).
#
# Metode  : timeit per 5 run, diambil rata-rata; EXPLAIN untuk mengonfirmasi
#           rencana eksekusi (type ALL vs range).
# Tanggal  : dicatat otomatis pada output.

import os
import time
from pathlib import Path

import mysql.connector

_ADMIN = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_ADMIN_USER", "root"),
    "password": os.getenv("DB_ADMIN_PASSWORD", "root_demo_lokal_123"),
    "database": os.getenv("DB_NAME", "asesmen_demo"),
}

N_BARIS = 50_000
N_RUN = 5
QUERY = "SELECT COUNT(*) FROM produk_pf WHERE nama LIKE 'Laptop%'"


def buat_data(conn):
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS produk_pf")
        cur.execute(
            """
            CREATE TABLE produk_pf (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                nama VARCHAR(120) NOT NULL,
                harga DECIMAL(12,2) NOT NULL DEFAULT 0,
                stok INT UNSIGNED NOT NULL DEFAULT 0
            ) ENGINE=InnoDB
            """
        )
        baris = [
            (f"Laptop-{i:05d}" if i % 5 == 0 else f"Produk-{i:05d}", i * 100, i % 500)
            for i in range(N_BARIS)
        ]
        cur.executemany("INSERT INTO produk_pf (nama, harga, stok) VALUES (%s,%s,%s)", baris)
    conn.commit()


def ukur(conn) -> float:
    """Rata-rata waktu (detik) untuk N_RUN eksekusi query."""
    total = 0.0
    with conn.cursor() as cur:
        for _ in range(N_RUN):
            t0 = time.perf_counter()
            cur.execute(QUERY)
            cur.fetchall()
            total += time.perf_counter() - t0
    return total / N_RUN


def explain(conn) -> str:
    with conn.cursor(dictionary=True) as cur:
        cur.execute("EXPLAIN " + QUERY)
        row = cur.fetchone()
    return f"type={row['type']} rows={row['rows']} key={row['key']}"


def main():
    tanggal = time.strftime("%Y-%m-%d %H:%M:%S")
    conn = mysql.connector.connect(**_ADMIN)
    try:
        buat_data(conn)
        print(f"Tanggal       : {tanggal}")
        print(f"Jumlah baris  : {N_BARIS:,}")
        print(f"Metode        : rata-rata {N_RUN} run (timeit), query:")
        print(f"  {QUERY}")
        print()

        print("[SEBELUM] tanpa index pada kolom nama")
        print(f"  EXPLAIN     : {explain(conn)}")
        sebelum = ukur(conn)
        print(f"  waktu       : {sebelum:.6f} dtk")

        with conn.cursor() as cur:
            cur.execute("CREATE INDEX idx_pf_nama ON produk_pf (nama)")
        conn.commit()

        print("[SESUDAH] dengan index idx_pf_nama (nama)")
        print(f"  EXPLAIN     : {explain(conn)}")
        sesudah = ukur(conn)
        print(f"  waktu       : {sesudah:.6f} dtk")

        peningkat = (sebelum - sesudah) / sebelum * 100
        print(f"\nPeningkatan   : {peningkat:.1f}% lebih cepat")
        print(f"  sebelum {sebelum:.6f} -> sesudah {sesudah:.6f} dtk")
    finally:
        try:
            with conn.cursor() as cur:
                cur.execute("DROP TABLE IF EXISTS produk_pf")
            conn.commit()
        except Exception:
            pass
        conn.close()


if __name__ == "__main__":
    main()
