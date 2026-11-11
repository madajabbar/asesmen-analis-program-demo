# 05. Code Review Checklist
Unit Kompetensi: **J.620100.032.01** (Code Review)

## 1. Checklist Review

### Fungsional
- [ ] Setiap perintah CLI berfungsi sesuai spesifikasi (`init-db`, `seed`,
      `list-produk`, `cari-produk`, `buat-voucher`, `laporan`).
- [ ] Transaksi voucher atomik: stok tidak cukup → rollback, data tidak berubah.
- [ ] Trigger mengisi `stok_log` dengan perubahan yang benar.
- [ ] Function & stored procedure dapat dipanggil langsung.

### Keamanan
- [ ] Tidak ada kredensial asli di repo (hanya `.env.example`).
- [ ] SQL memakai parameter terikat (`%s`) — bebas SQL injection.
- [ ] User aplikasi `app_asesmen` memakai hak terbatas (least privilege).

### Kode & Pemeliharaan
- [ ] Docstring/komentar menjelaskan MENGAPA (bukan hanya APA).
- [ ] Validasi masukan di batas kepercayaan (jumlah > 0, kode valid).
- [ ] Tidak ada kode mati/duplikasi yang tidak perlu.
- [ ] Penamaan jelas dan konsisten (Inggris untuk kode).

### Pengujian
- [ ] Uji unit mencakup data normal, boundary, dan tidak valid.
- [ ] Uji integrasi benar-benar terhubung ke MySQL dan lulus.

## 2. Temuan Review pada Proyek Ini
| No | Temuan | Status |
|---|---|---|
| 1 | Trigger `tr_produk_stok_after_update` menggunakan aritmetika unsigned → error 1690. | **Diperbaiki** (CAST SIGNED) |
| 2 | Awalnya `init-db` memakai driver Python dengan `multi=True` yang tidak didukung `CMySQLCursor`. | **Diperbaiki** (pakai klien `mysql`) |
| 3 | Uji integrasi `test_stored_procedure_langsung` bergantung pada stok cached → rawan gagal. | **Diperbaiki** (baca stok segar) |
| 4 | `schema.sql` tidak idempotent untuk `CREATE INDEX` terpisah. | **Diperbaiki** (index inline, tanpa DDL terpisah) |

## 3. Contoh Pengecualian Guideline yang Didokumentasikan
**Pengecualian**: `src/cli.py` menjalankan file SQL (`schema.sql`, `seed.sql`)
melalui klien `mysql` (subprocess) alih-alih driver Python.

**Alasan**: `schema.sql` memuat `DELIMITER` untuk membuat stored procedure/function/
trigger. `DELIMITER` adalah direktif **klien mysql**, bukan statement server, sehingga
tidak dapat dieksekusi lewat driver Python. Menggunakan klien `mysql` adalah cara
yang benar dan umum untuk skenario DDL multi-statement ini. Pengecualian ini
didokumentasikan langsung pada fungsi yang bersangkutan.
