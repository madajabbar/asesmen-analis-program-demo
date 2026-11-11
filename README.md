# asesmen-analis-program-demo

Aplikasi **demo portofolio** untuk asesmen sertifikasi kompetensi **Analis Program (BNSP)**
a.n. **Madajabbar Palapa Hakim, S.Kom** — LSP Nusa Mandiri (asesmen 21 November 2026).

Stack: **Python 3** + **MySQL 8**. Bentuk: **CLI non-interaktif** (argparse) sehingga
mudah di-script untuk pengujian end-to-end.

---

## Tujuan
Mendemonstrasikan 10 unit kompetensi melalui sistem mini inventaris & payment voucher
yang berfungsi penuh (bukan sekadar kode rujukan). Seluruh bukti ditelusuri pada
tabel Traceability di bawah.

---

## Cara Menjalankan

### Opsi A — Docker Compose (disarankan)
```bash
cp .env.example .env          # isi jika perlu (default cocok utk docker)
docker compose up -d          # menjalankan MySQL 8 di port 3306
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Siapkan skema + data
.venv/bin/python -m src.cli init-db    # buat skema
.venv/bin/python -m src.cli seed       # isi data contoh
```

> MySQL di docker compose adalah untuk **demo lokal**. Password di dalam
> `docker-compose.yml` HANYA password demo lokal (lihat label pada file). `.env`
> asli masuk `.gitignore`; yang di-commit hanya `.env.example` tanpa kredensial asli.

### Opsi B — MySQL Lokal
1. Install MySQL 8 di mesin Anda dan pastikan service berjalan.
2. Buat database & user (atau pakai root untuk setup):
   ```bash
   mysql -uroot -p < sql/schema.sql
   mysql -uroot -p < sql/seed.sql
   mysql -uroot -p < sql/grants.sql
   ```
3. Isi kredensial di `.env` (salin dari `.env.example`).

**Langkah ringkas di Windows (laptop Mada)**:
1. Install MySQL 8 (MySQL Installer) → pastikan service "MySQL80" berjalan.
2. Buka `cmd`, jalankan 3 perintah `mysql -uroot -p < sql/...` di atas.
3. Jalankan perintah CLI dengan `.venv\Scripts\python -m src.cli <perintah>`.
4. Ubah `DB_PASSWORD` di `.env` sesuai password MySQL Anda.

---

## Daftar Perintah CLI
| Perintah | Keterangan |
|---|---|
| `init-db` | Buat database & skema dari `sql/schema.sql`. |
| `seed` | Isi data contoh dari `sql/seed.sql`. |
| `list-produk` | Tampilkan daftar produk. |
| `cari-produk <kata>` | Cari produk berdasarkan nama/kategori. |
| `buat-voucher --kode K --produk-id ID --jumlah N` | Buat voucher (transaksi: kurangi stok, catat log). |
| `laporan` | Ringkasan nilai persediaan & statistik. |

```bash
.venv/bin/python -m src.cli list-produk
.venv/bin/python -m src.cli buat-voucher --kode VC-0001 --produk-id 6 --jumlah 10
```

---

## Interface Website (Fase 2)

Antarmuka web Flask mengikuti desain **Stitch** *"Inventaris & Payment Voucher"*
(design system **Cupertino Admin Console**). Token warna utama: primer biru
`#0071E3`, hijau `#34C759`, oranye `#FF9500`, merah `#FF3B30`, latar `#F5F5F7`.
Memakai ulang service/repository & konfigurasi `.env` Fase 1. CLI tetap utuh.

### Menjalankan
```bash
# pastikan MySQL (docker compose) aktif & sudah init-db + seed
.venv/bin/python -m web.app          # port 5000
# atau
flask --app web.app run
```

### Halaman
| Route | Halaman |
|---|---|
| `GET /` | Dashboard (statistik, ringkasan per kategori, stok menipis/habis, voucher terakhir) |
| `GET /produk` | Daftar produk + pencarian + urut |
| `GET /voucher` | Daftar payment voucher |
| `GET|POST /voucher/baru` | Form buat voucher (transaksi ACID, alert sukses/gagal) |
| `GET /laporan` | Ringkasan + bukti trigger `stok_log` |

Semua angka/tabel/kode voucher diambil dari **database nyata** (dilarang data
rekaan). Status voucher = `AKTIF`. Format rupiah konsisten `Rp8.500.000`.

---

## Struktur Folder
```
asesmen-analis-program-demo/
├── README.md
├── docker-compose.yml          # MySQL 8 (demo lokal)
├── requirements.txt
├── .env.example                # contoh env (tanpa kredensial asli)
├── .gitignore
├── sql/
│   ├── schema.sql              # DB, tabel, view, index, SP, function, trigger
│   ├── seed.sql                # DML contoh
│   └── grants.sql              # GRANT user aplikasi (least privilege)
├── src/
│   ├── __init__.py
│   ├── cli.py                  # argparse CLI
│   ├── service.py              # layanan + validasi
│   ├── db.py                   # koneksi
│   ├── config.py               # konfigurasi env
│   └── algorithms.py           # quick_sort, merge_sort, binary_search
├── tests/
│   ├── test_algorithms.py      # uji unit algoritma
│   ├── test_validation.py      # uji unit validasi
│   ├── test_integration.py     # uji integrasi MySQL (skip bila DB mati)
│   └── test_web.py             # uji web Flask (skip bila DB mati)
├── web/
│   ├── app.py                  # aplikasi Flask (routes)
│   ├── templates/              # Jinja2 (base, dashboard, produk, voucher, buat_voucher, laporan)
│   └── static/style.css         # token desain Cupertino Admin Console
├── examples/
│   └── buggy_demo.py           # contoh latihan debugging
├── scripts/
│   └── profiling_before_after.py
└── docs/
    ├── 01_analisis_skalabilitas.md
    ├── 02_dokumentasi_kode.md
    ├── 03_debugging_log.md
    ├── 04_profiling.md
    ├── 05_code_review_checklist.md
    ├── 06_pengujian.md
```

---

## Traceability Unit Kompetensi → Bukti
| Kode UK | Unit Kompetensi | Bukti di Repo |
|---|---|---|
| J.620100.002.01 | Skalabilitas | `docs/01_analisis_skalabilitas.md` |
| J.620100.020.02 | SQL | `sql/schema.sql`, `sql/seed.sql` (database, tabel, view, index, SP, function, trigger, COMMIT/ROLLBACK) |
| J.620100.021.02 | Akses Basis Data | `src/db.py`, `src/config.py`, `sql/grants.sql`, `.env.example`, `docs/04_profiling.md` (EXPLAIN) |
| J.620100.022.02 | Algoritma | `src/algorithms.py` (sorting + binary_search, Big-O) |
| J.620100.023.02 | Dokumen Kode | `docs/02_dokumentasi_kode.md` + docstring seluruh modul |
| J.620100.029.02 | Debugging | `docs/03_debugging_log.md`, `examples/buggy_demo.py` |
| J.620100.031.01 | Profiling | `docs/04_profiling.md`, `scripts/profiling_before_after.py` |
| J.620100.032.01 | Code Review | `docs/05_code_review_checklist.md` |
| J.620100.033.02 | Uji Unit | `tests/test_algorithms.py`, `tests/test_validation.py` |
| J.620100.034.02 | Uji Integrasi | `tests/test_integration.py`, `docs/06_pengujian.md` |

---

## Pengujian
```bash
.venv/bin/python -m pytest tests/ -v
```
Hasil terbaru: **47 lulus** (32 unit, 7 integrasi + 8 web) — lihat `docs/06_pengujian.md` & `E2E_LOG.md`.
