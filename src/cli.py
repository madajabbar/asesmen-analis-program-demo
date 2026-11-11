# src/cli.py
# Unit Kompetensi: J.620100.001.01 (Skalabilitas — desain antarmuka modular)
#
# Antarmuka baris perintah (CLI) non-interaktif memakai argparse agar dapat
# di-script untuk pengujian end-to-end (E2E).
#
# MENGAPA argparse: non-interaktif, mudah diautomasi, dan menyediakan
# bantuan (-h) yang memenuhi asesmen dokumentasi perintah.
#
# Perintah:
#   init-db      buat database & skema dari sql/schema.sql
#   seed         isi data contoh dari sql/seed.sql
#   list-produk  tampilkan daftar produk
#   cari-produk  cari produk berdasarkan nama/kategori
#   buat-voucher buat voucher (transaksi: kurangi stok, catat stok_log)
#   laporan      ringkasan nilai persediaan & statistik

import argparse
import os
import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.db import ping, get_connection  # noqa: E402
from src import service  # noqa: E402


# Nama container MySQL docker compose (default). Bisa langsungtimpa via env.
_MYSQL_CONTAINER = os.getenv("MYSQL_CONTAINER", "asesmen-mysql")
_DB_ADMIN_USER = os.getenv("DB_ADMIN_USER", "root")
_DB_ADMIN_PASSWORD = os.getenv("DB_ADMIN_PASSWORD", "root_demo_lokal_123")


def _jalankan_sql_file(path: Path) -> None:
    """Menjalankan file SQL memakai klien `mysql` (root).

    MENGAPA klien CLI, bukan driver Python: file seperti schema.sql memuat
    `DELIMITER` untuk stored procedure/function/trigger yang hanya dipahami
    klien `mysql`, bukan server. Jika Docker tersedia, jalankan di dalam
    container asesmen-mysql; jika tidak, fallback ke `mysql` sistem.
    """
    sql = path.read_text(encoding="utf-8")
    if _MYSQL_CONTAINER and subprocess.run(
        ["docker", "inspect", _MYSQL_CONTAINER],
        capture_output=True,
    ).returncode == 0:
        cmd = [
            "docker", "exec", "-i", _MYSQL_CONTAINER, "mysql",
            f"-u{_DB_ADMIN_USER}", f"-p{_DB_ADMIN_PASSWORD}",
        ]
    else:
        cmd = ["mysql", f"-u{_DB_ADMIN_USER}", f"-p{_DB_ADMIN_PASSWORD}"]
    hasil = subprocess.run(cmd, input=sql, text=True, capture_output=True)
    if hasil.returncode != 0:
        raise RuntimeError(
            f"Gagal menjalankan {path.name}:\n{hasil.stderr}"
        )


def cmd_init_db(args) -> int:
    # init-db memakai user root (pembuatan skema = DDL).
    # `schema.sql` bersifat idempotent (IF NOT EXISTS / DROP IF EXISTS),
    # sehingga aman dijalankan beberapa kali.
    _jalankan_sql_file(_PROJECT_ROOT / "sql" / "schema.sql")
    print("Skema database dibuat dari sql/schema.sql.")
    return 0


def cmd_seed(args) -> int:
    _jalankan_sql_file(_PROJECT_ROOT / "sql" / "seed.sql")
    print("Data contoh dimuat dari sql/seed.sql.")
    return 0


def cmd_list_produk(args) -> int:
    rows = service.list_produk(maks=args.maks)
    if not rows:
        print("Tidak ada produk.")
        return 0
    print(f"{'ID':<4}{'Nama':<28}{'Kategori':<18}{'Harga':>12}{'Stok':>6}  Status")
    for r in rows:
        print(
            f"{r['id']:<4}{r['nama'][:26]:<28}{r['kategori']:<18}"
            f"{r['harga']:>12,.0f}{r['stok']:>6}  {r['status']}"
        )
    return 0


def cmd_cari_produk(args) -> int:
    rows = service.cari_produk(args.kata_kunci)
    if not rows:
        print(f"Tidak ditemukan produk untuk '{args.kata_kunci}'.")
        return 0
    print(f"{'ID':<4}{'Nama':<28}{'Kategori':<18}{'Harga':>12}{'Stok':>6}")
    for r in rows:
        print(
            f"{r['id']:<4}{r['nama'][:26]:<28}{r['kategori']:<18}"
            f"{r['harga']:>12,.0f}{r['stok']:>6}"
        )
    return 0


def cmd_buat_voucher(args) -> int:
    try:
        vid = service.buat_voucher(args.kode, args.produk_id, args.jumlah)
    except ValueError as e:
        print(f"GAGAL: {e}")
        return 1
    print(f"Voucher dibuat: id={vid} kode={args.kode} produk_id={args.produk_id} jumlah={args.jumlah}")
    return 0


def cmd_laporan(args) -> int:
    lap = service.laporan()
    print("=== LAPORAN INVENTARIS ===")
    print(f"Nilai persediaan      : {lap['nilai_persediaan']:,.0f}")
    print(f"Total produk           : {lap['total_produk']}")
    print(f"Voucher aktif          : {lap['voucher_aktif']}")
    print("Per kategori:")
    print(f"  {'Kategori':<18}{'Jumlah':>8}{'Nilai':>16}")
    for k in lap["per_kategori"]:
        print(
            f"  {k['kategori']:<18}{k['jumlah_produk']:>8}"
            f"{float(k['nilai']):>16,.0f}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="asesmen-cli",
        description="Mini Sistem Inventaris & Payment Voucher (demo BNSP).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Buat database & skema.")
    sub.add_parser("seed", help="Isi data contoh.")

    sp = sub.add_parser("list-produk", help="Daftar produk.")
    sp.add_argument("--maks", type=int, default=50)

    sc = sub.add_parser("cari-produk", help="Cari produk.")
    sc.add_argument("kata_kunci")

    sv = sub.add_parser("buat-voucher", help="Buat voucher.")
    sv.add_argument("--kode", required=True)
    sv.add_argument("--produk-id", type=int, required=True)
    sv.add_argument("--jumlah", type=int, required=True)

    sl = sub.add_parser("laporan", help="Ringkasan laporan.")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "init-db":
        return cmd_init_db(args)
    if args.command == "seed":
        return cmd_seed(args)
    if args.command == "list-produk":
        return cmd_list_produk(args)
    if args.command == "cari-produk":
        return cmd_cari_produk(args)
    if args.command == "buat-voucher":
        return cmd_buat_voucher(args)
    if args.command == "laporan":
        return cmd_laporan(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
