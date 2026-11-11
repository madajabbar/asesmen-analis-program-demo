# 04. Profiling (Before / After)
Unit Kompetensi: **J.620100.031.01** (Profiling)

## Metode
- **Tanggal**: 2026-11-11 10:52:04 (waktu lokal).
- **Query yang diukur**:
  ```sql
  SELECT COUNT(*) FROM produk_pf WHERE nama LIKE 'Laptop%';
  ```
- **Data**: tabel uji `produk_pf` (terpisah, tidak menyentuh data aplikasi) berisi
  **50.000 baris**. Skrip: `scripts/profiling_before_after.py`.
- **Pengukuran**: rata-rata dari **5 run** (`time.perf_counter`), memakai MySQL
  8.0 via Docker Compose. Rencana eksekusi dikonfirmasi dengan `EXPLAIN`.

Has Hasil Nyata
| Tahap | EXPLAIN | Waktu rata-rata |
|---|---|---|
| **Sebelum** (tanpa index pada `nama`) | `type=ALL rows=50000 key=None` | `0.010858` dtk |
| **Sesudah** (index `idx_pf_nama` pada `nama`) | `type=range rows=18798 key=idx_pf_nama` | `0.005518` dtk |

**Peningkatan: 49,2% lebih cepat** (`0.010858` → `0.005518` dtk).

## Identifikasi Bottleneck
- Sebelum index: query melakukan **full table scan** (`type=ALL`, menelusuri 50.000
  baris).
- Sesudah index: MySQL memakai **range scan** via `idx_pf_nama` (hanya `18.798` baris
  dievaluasi), tanpa perlu membaca seluruh tabel.

## Kesimpulan
Penambahan index pada kolom yang sering dipakai sebagai predikat `WHERE`/`LIKE`
(prefix) secara langsung menurunkan jumlah baris yang discan dan mempercepat query.
Untuk query `LIKE '%...%'` (wildcard di awal) index B-tree tidak membantu; solusi
lanjutan adalah full-text index atau `LOCATE`.

> Catatan: hasil ini sesuai optimasi yang dipakai pada schema (mis. `idx_produk_nama`
> pada tabel `produk` untuk perintah `cari-produk`).
