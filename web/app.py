# web/app.py
# Antarmuka Website (Fase 2) — mengikuti desain Stitch "Cupertino Admin Console".
# Memakai ulang service/repository & konfigurasi .env Fase 1.
#
# Desain token:
#   - Font: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
#   - Background #F5F5F7; kartu putih radius 20px; border #E5E5EA
#   - Teks utama #1D1D1F; sekunder #86868B
#   - Primer #0071E3; hijau #34C759; oranye #FF9500; merah #FF3B30
#
# Menjalankan:
#   python -m web.app            (atau)
#   flask --app web.app run      (port 5000)

import os

from flask import Flask, flash, redirect, render_template, request, url_for
from mysql.connector import IntegrityError

from src import service
from src.db import ping

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _fmt_uang(v):
    """Format rupiah konsisten: Rp8.500.000 (tanpa spasi liar)."""
    return "Rp" + f"{int(round(float(v))):,}".replace(",", ".")


def create_app():
    app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"),
                static_folder=os.path.join(BASE_DIR, "static"))
    app.secret_key = os.getenv("SECRET_KEY", "demo-lokal-rahasia")
    app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

    @app.template_filter("uang")
    def uang(v):
        return _fmt_uang(v)

    @app.context_processor
    def inject_global():
        # Status koneksi NYATA: hijau bila DB hidup, merah bila mati.
        return {"db_ok": ping()}

    # ------------------------------------------------------------------
    # Dashboard (Screen 1)
    # ------------------------------------------------------------------
    @app.route("/")
    def dashboard():
        stok_menipis = service.stok_menipis_habis()
        rincian_kategori = service.ringkasan_stok_per_kategori()
        voucher_terakhir = service.voucher_terbaru(5)
        statistik = [
            {"label": "Total Produk", "nilai": service.laporan()["total_produk"],
             "ikon": "📦", "warna": "blue"},
            {"label": "Total Stok", "nilai": service.total_stok(),
             "ikon": "📊", "warna": "green"},
            {"label": "Nilai Persediaan", "nilai": _fmt_uang(service.laporan()["nilai_persediaan"]),
             "ikon": "💰", "warna": "orange"},
            {"label": "Voucher Terbit", "nilai": service.voucher_terbit(),
             "ikon": "🧾", "warna": "red"},
        ]
        return render_template(
            "dashboard.html",
            statistik=statistik,
            rincian_kategori=rincian_kategori,
            stok_menipis=stok_menipis,
            voucher_terakhir=voucher_terakhir,
            total_kategori=sum(r["total_stok"] for r in rincian_kategori),
            total_nilai_kategori=sum(float(r["nilai"]) for r in rincian_kategori),
        )

    # ------------------------------------------------------------------
    # Produk
    # ------------------------------------------------------------------
    @app.route("/produk")
    def produk():
        q = request.args.get("q", "").strip()
        sort_by = request.args.get("sort", "nama")
        if q:
            rows = service.cari_produk(q, maks=100)
        else:
            rows = service.list_produk(maks=100)

        urut = {"nama": "nama", "harga": "harga", "stok": "stok"}
        kunci = urut.get(sort_by, "nama")
        if kunci in ("harga", "stok"):
            rows.sort(key=lambda r: float(r[kunci]))
        else:
            rows.sort(key=lambda r: r["nama"].lower())

        return render_template("produk.html", rows=rows, q=q, sort=sort_by)

    # ------------------------------------------------------------------
    # Daftar Voucher
    # ------------------------------------------------------------------
    @app.route("/voucher")
    def voucher():
        return render_template("voucher.html", rows=service.daftar_voucher())

    # ------------------------------------------------------------------
    # Buat Voucher (Screen 2)
    # ------------------------------------------------------------------
    @app.route("/voucher/baru", methods=["GET", "POST"])
    def buat_voucher():
        produk_list = service.list_produk(maks=200)
        if request.method == "POST":
            kode = request.form.get("kode", "").strip()
            try:
                produk_id = int(request.form.get("produk_id", ""))
            except ValueError:
                produk_id = None
            try:
                jumlah = int(request.form.get("jumlah", ""))
            except ValueError:
                jumlah = None

            # Validasi form
            ok, pesan = service.validasi_kode(kode)
            if not ok:
                flash(pesan, "gagal")
                return render_template("buat_voucher.html", produk_list=produk_list), 400
            ok, pesan = service.validasi_jumlah(jumlah)
            if not ok:
                flash(pesan, "gagal")
                return render_template("buat_voucher.html", produk_list=produk_list), 400

            produk = next((p for p in produk_list if p["id"] == produk_id), None)
            if produk is None:
                flash("Produk tidak valid.", "gagal")
                return render_template("buat_voucher.html", produk_list=produk_list), 400

            # Baca stok SEBELUM transaksi (untuk laporan nyata)
            stok_sebelum = produk["stok"]
            try:
                service.buat_voucher(kode, produk_id, jumlah)
            except ValueError as e:
                # Penolakan transaksi: stok tidak berubah, bukan crash/500.
                flash(str(e), "gagal")
                return render_template("buat_voucher.html", produk_list=produk_list), 400
            except IntegrityError:
                flash("Kode voucher sudah digunakan.", "gagal")
                return render_template("buat_voucher.html", produk_list=produk_list), 400

            # Baca stok SESUDAH (nyata dari DB)
            stok_sesudah = service.list_produk(maks=200)
            stok_sesudah = next(
                (p["stok"] for p in stok_sesudah if p["id"] == produk_id),
                stok_sebelum,
            )
            flash(
                f"Voucher {kode} berhasil dibuat — stok {produk['nama']} "
                f"berkurang {stok_sebelum} → {stok_sesudah} dan tercatat "
                f"di stok_log oleh trigger.",
                "sukses",
            )
            return redirect(url_for("buat_voucher"))

        return render_template("buat_voucher.html", produk_list=produk_list)

    # ------------------------------------------------------------------
    # Laporan
    # ------------------------------------------------------------------
    @app.route("/laporan")
    def laporan():
        lap = service.laporan()
        log = service.riwayat_stok_log(100)
        return render_template("laporan.html", lap=lap, log=log)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
