# 01. Analisis Skalabilitas Sistem
Unit Kompetensi: **J.620100.002.01** (Skalabilitas)

## 1. Lingkup Sistem
Aplikasi **Mini Sistem Inventaris & Payment Voucher** adalah CLI (non-interaktif, `argparse`)
untuk mengelola:
- **Kategori & Produk** — master data barang inventaris (harga, stok, stok minimum).
- **Voucher** — transaksi pembayaran yang mengurangi stok produk secara atomik.
- **Jejak audit** — setiap perubahan stok tercatat otomatis di `stok_log` via trigger.
- **Laporan** — nilai persediaan dan statistik per kategori (via function + view).

Aplikasi ini adalah *demo portofolio* untuk asesmen sertifikasi kompetensi Analis Program (BNSP).
Arsitekturnya sengaja dibuat sederhana namun representatif: satu lapisan CLI, satu lapisan
layanan (`service.py`), satu lapisan akses data (`db.py`), dan MySQL 8.

## 2. Lingkungan Operasi
| Komponen | Spesifikasi |
|---|---|
| Bahasa | Python 3.13 (min. 3.10) |
| Basis data | MySQL 8.0 (InnoDB, utf8mb4) |
| Koneksi | `mysql-connector-python` |
| OS | Linux (deploy), Windows (dev laptop) |
| Kontainerisasi | Docker Compose (MySQL) |

## 3. Analisis Kompleksitas
Kompleksitas algoritmik pada jalur kritis (sebagian kali di `src/algorithms.py`):

| Operasi | Kompleksitas waktu | Keterangan |
|---|---|---|
| Sorting produk (Quicksort/Mergesort) | O(n log n) | rata-rata, n = jumlah produk |
| Pencarian biner `binary_search` | O(log n) | pada data terurut |
| Transaksi voucher | O(1) per baris | dijamin atomik oleh `START TRANSACTION` |
| Query laporan agregasi | O(n) | scan data + agregasi GROUP BY |

### Kebutuhan Perangkat Keras
Untuk beban *demo* (skala kecil, < 1.000 produk):
- **RAM**: 512 MB–1 GB (proses Python ringan; MySQL 8 min. 512 MB).
- **CPU**: 1–2 vCPU.
- **Disk**: < 1 GB (data kecil; log query dianggap rendah).
Untuk proyeksi *produksi* (skala besar, lihat Section 4) disarankan min. 4 GB RAM dan
SSD.

## 4. Strategi Scaling

### Vertical Scaling (scaling up)
Menambah sumber daya pada satu server (RAM, CPU, disk).
- **Kelebihan**: sederhana, tanpa perubahan arsitektur, cocok untuk beban transisi.
- **Kekurangan**: ada batas fisik, biaya non-linear, *single point of failure*.
- **Langkah khas**: tingkatkan instance DB dari 1 → 2 → 4 vCPU; naikkan `innodb_buffer_pool_size`
  (mis. ke 50–70% RAM); gunakan SSD.

### Horizontal Scaling (scaling out)
Menambah node server dan membagi beban.
- **Pemisahan baca/tulis (read replicas)**: query laporan besar dialihkan ke replica
  (tabel `v_ringkasan_stok`, `v_laporan_inventaris`).
- **Sharding/partitioning**: partisi tabel besar (mis. `stok_log`) per bulan
  (`PARTITION BY RANGE` pada `created_at`) agar scan lebih kecil.
- **Load balancer** di depan beberapa instance aplikasi; gunakan session stateless.
- **Kelebihan**: skala elastis, ketersediaan tinggi.
- **Kekurangan**: kompleksitas konsistensi (eventual consistency) & operasional.

### Rekomendasi untuk sistem ini
1. **Beban kecil–menengah**: vertical scaling (upgrade RAM/CPU) + optimasi index.
2. **Beban besar**: horizontal read-replica untuk laporan + partitioning `stok_log`;
   aplikasi stateless sehingga mudah ditambah instance.

### Pengukuran
Bukti empiris optimasi index pada query pencarian ada di **docs/04_profiling.md**
(perbaikan **49,2%** lebih cepat setelah penambahan index).
