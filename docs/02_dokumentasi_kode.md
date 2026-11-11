# 02. Dokumentasi Kode
Unit Kompetensi: **J.620100.023.02** (Dokumen Kode)

## 1. Prinsip
Setiap modul dan fungsi diberi `docstring`/komentar yang menjelaskan **MENGAPA**
(rasional) di samping **apa** yang dilakukan. Bahasa dokumentasi: Bahasa Indonesia;
nama kode: Inggris.

## 2. Daftar Modul & Fungsi

### `src/algorithms.py` — Algoritma
| Fungsi | Deskripsi | Kompleksitas |
|---|---|---|
| `quick_sort(arr)` | Quicksort menaik | waktu O(n log n), memori O(log n) |
| `merge_sort(arr)` | Mergesort menaik | waktu O(n log n), memori O(n) |
| `binary_search(arr, target)` | Pencarian biner pada data terurut | waktu O(log n), memori O(1) |

### `src/config.py` — Konfigurasi
| Anggota | Deskripsi |
|---|---|
| `Config` | Membaca `DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME` dari env (`.env`). |
| `Config.dsn()` | Mengembalikan parameter koneksi bertipe dict untuk connector. |

### `src/db.py` — Akses Basis Data
| Fungsi | Deskripsi |
|---|---|
| `get_connection()` | Membuka koneksi ke `asesmen_demo`. |
| `ping()` | Uji ketersediaan basis data (dipakai untuk skip otomatis uji integrasi). |

### `src/service.py` — Lapisan Layanan
| Fungsi | Deskripsi |
|---|---|
| `validasi_jumlah(jumlah)` | Validasi murni: jumlah harus bulat positif. |
| `validasi_kode(kode)` | Validasi murni: kode ≤ 40 karakter alfanumerik. |
| `list_produk(maks)` | Daftar produk bergabung dengan kategori. |
| `cari_produk(kata_kunci)` | Pencarian produk berdasarkan nama/kategori (LIKE). |
| `buat_voucher(kode, produk_id, jumlah)` | Transaksi atomik: insert voucher + kurangi stok, commit/rollback. |
| `laporan()` | Ringkasan nilai persediaan via `fn_nilai_persediaan`. |

### `src/cli.py` — Antarmuka Perintah
| Perintah | Fungsi | Deskripsi |
|---|---|---|
| `init-db` | `cmd_init_db` | Buat database & skema dari `sql/schema.sql` (lewat klien `mysql`). |
| `seed` | `cmd_seed` | Isi data contoh dari `sql/seed.sql`. |
| `list-produk` | `cmd_list_produk` | Tampilkan daftar produk. |
| `cari-produk` | `cmd_cari_produk` | Cari produk. |
| `buat-voucher` | `cmd_buat_voucher` | Buat voucher (transaksi). |
| `laporan` | `cmd_laporan` | Ringkasan laporan. |

### `tests/` — Uji
- `test_algorithms.py` — uji unit algoritma (tanpa DB).
- `test_validation.py` — uji unit validasi (tanpa DB).
- `test_integration.py` — uji integrasi terhadap MySQL (skip otomatis bila DB mati).

## 3. Cara Men-generate Dokumentasi
Menggunakan **pydoc** (bawaan Python):

```bash
# HTML lengkap semua modul
.venv/bin/python -m pydoc -w src
# Tampil di terminal per modul
.venv/bin/python -m pydoc src.service
```

Menghasilkan `src.html`, `config.html`, `db.html`, `service.html`, `cli.html`, `algorithms.html`
di direktori proyek.

## 4. Log Revisi
| Tanggal | Revisi |
|---|---|
| 2026-11-11 | Versi awal; seluruh modul & fungsi didokumentasikan. |
