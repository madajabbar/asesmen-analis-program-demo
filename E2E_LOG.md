# E2E_LOG.md — Verifikasi End-to-End

**Tanggal**: 2026-11-11
**Jalur MySQL yang dipakai**: Docker Compose (`mysql:8`), container `asesmen-mysql`,
port `3306`, image `mysql:8`, versi server `8.0.x` (latest tag). MySQL lokal sistem tidak
tersedia di mesin (tidak ada binary `mysql`/service aktif), sehingga jalur Docker dipilih.

---

## Langkah & Hasil Nyata

### 1. Ketersediaan stack
```
mysql   : tidak terpasang di host (systemd inactive)
docker  : 29.6.2, container asesmen-mysql Up (healthy)
python  : 3.13.5 | pytest 8.4.2 | mysql-connector-python 9.4.0
gh/login: github.com account madajabbar (active)
```

### 2. Buat skema & data
```
$ python -m src.cli init-db
Skema database dibuat dari sql/schema.sql.
$ python -m src.cli seed
Data contoh dimuat dari sql/seed.sql.
$ mysql -uroot -p < sql/grants.sql
GRANTS_OK
```
Verifikasi objek (SHOW TABLES / SHOW PROCEDURE STATUS / SHOW FUNCTION STATUS /
SHOW TRIGGERS): **8 tabel+view**, `sp_buat_voucher`, `fn_nilai_persediaan`,
`fn_total_voucher`, trigger `tr_produk_stok_after_update` — semua ada.

### 3. CLI: list-produk & cari-produk
```
$ python -m src.cli list-produk
ID  Nama                        Kategori                 Harga  Stok  Status
1   Laptop ASUS VivoBook        Elektronik           8,500,000    12  CUKUP
...
9   Wajan Anti Lengket          Peralatan Dapur        110,000     2  MENIPIS
10  Air Mineral 600ml           Minuman                  3,500     0  HABIS

$ python -m src.cli cari-produk Laptop
ID  Nama                        Kategori                 Harga  Stok
1   Laptop ASUS VivoBook        Elektronik           8,500,000    12
```

### 4. buat-voucher SUKSES (stok berkurang, trigger log, function total)
```
$ python -m src.cli buat-voucher --kode VC-E2E-0001 --produk-id 6 --jumlah 10
Voucher dibuat: id=1 kode=VC-E2E-0001 produk_id=6 jumlah=10
```
Verifikasi DB:
```
produk: Pulpen Standard AE7 stok 300 -> 290
stok_log: stok_sebelum=300 stok_sesudah=290 perubahan=-10 alasan=perubahan_stok
fn_total_voucher('VC-E2E-0001') = 40000.00   (4000 x 10)
voucher: kode=VC-E2E-0001 jumlah=10 total_harga=40000.00 status=AKTIF
```

### 5. buat-voucher GAGAL (stok kurang → ROLLBACK, data tidak berubah)
```
$ python -m src.cli buat-voucher --kode VC-E2E-0002 --produk-id 9 --jumlah 99
GAGAL: Stok tidak mencukupi untuk membuat voucher   (exit code 1)
```
Verifikasi DB: Wajan Anti Lengket **tetap stok 2**; tidak ada voucher `VC-E2E-0002`;
tidak ada baris baru di `stok_log` (rollback sukses).

### 6. Query view v_ringkasan_stok
```
SELECT produk_id,nama_produk,stok,status_stok FROM v_ringkasan_stok WHERE produk_id IN (6,9);
6  Pulpen Standard AE7  290  CUKUP
9  Wajan Anti Lengket     2  MENIPIS
```

### 7. Panggil stored procedure & function langsung
```
CALL sp_buat_voucher('VC-SP-DIRECT', 6, 5);        -- via mysql CLI
produk: Pulpen stok 290 -> 285
stok_log: perubahan=-5
fn_nilai_persediaan() = 128355000.00
voucher: VC-SP-DIRECT jumlah=5
```

### 8. pytest (unit + integrasi, MySQL aktif)
```
$ python -m pytest tests/ -v
============================== 39 passed in 0.40s ==============================
```
- Uji unit: 32 lulus (algoritma 17, validasi 15)
- Uji integrasi: 7 lulus (koneksi, voucher sukses/gagal, produk tidak ada, laporan,
  view, stored procedure)

### 9. Profiling before/after
```
$ python scripts/profiling_before_after.py
Tanggal: 2026-11-11 10:52:04 | 50.000 baris | rata-rata 5 run
SEBELUM : EXPLAIN type=ALL rows=50000 key=None   -> 0.010858 dtk
SESUDAH : EXPLAIN type=range rows=18798 key=idx_pf_nama -> 0.005518 dtk
Peningkatan: 49,2% lebih cepat
```

### 10. Hasil & sisa
Semua langkah **LULUS**. Tidak ada blocker tersisa. Detail tambahan di `docs/01–06`.

---

## Fase 2 — Web (Interface Website Flask)

**Tanggal**: 2026-11-11
**Desain**: Stitch — "Inventaris & Payment Voucher" (design system *Cupertino Admin Console*).
**DB**: MySQL Docker `asesmen-mysql` aktif (healthy), skema + seed terpasang.

### Perintah menjalankan web
```
.venv/bin/python -m web.app        # atau: flask --app web.app run  (port 5000)
```

### Langkah & Hasil Nyata

**1. GET /** (Dashboard) → `200`
- Memuat angka nyata dari DB: Total Produk (10), Total Stok, Nilai Persediaan, Voucher Terbit.
- Pil status **"MySQL Terkoneksi"** hijau (dari `ping()` nyata).
- `v_ringkasan_stok` menampilkan ringkasan per kategori.

**2. GET /produk** → `200`
- Memuat nama produk seed nyata: `Laptop ASUS VivoBook`, `Pulpen Standard AE7`.
- Pencarian `?q=Mouse` → hanya menampilkan `Mouse Wireless Logitech`.

**3. POST /voucher/baru VALID** → `302` → `200` (alert hijau)
```
POST kode=PV-E2E-<ts> produk_id=5 (Kertas A4 80gsm) jumlah=7
stok produk 5: 82 -> 75   (berkurang 7, diverifikasi via SQL)
Alert: "Voucher PV-E2E-... berhasil dibuat — stok Kertas A4 80gsm berkurang 82 → 75 dan tercatat di stok_log oleh trigger."
(contoh segar lain: 69 -> 67)
```

**4. POST /voucher/baru MELEBIHI STOK** → `400` (ditolak)
```
POST kode=PV-E2E-OVER-<ts> produk_id=9 (Wajan Anti Lengket) jumlah=999
Response: "Stok tidak mencukupi untuk membuat voucher"
Verifikasi SQL: stok Wajan tetap 2 (TIDAK berubah); tidak ada voucher baru; tidak ada baris stok_log baru. BUKAN crash/500.
```

**5. GET /laporan** → `200`
- Memuat ringkasan + tabel `stok_log` (bukti trigger) dengan entri nyata
  (produk, stok_sebelum, stok_sesudah, perubahan, alasan, waktu).

**6. pytest (total akhir: lama + web)**
```
$ python -m pytest tests/ -v
============================== 47 passed in 1.46s ==============================
```
- 39 uji lama (32 unit + 7 integrasi) tetap lulus, **tanpa regresi**.
- 8 uji web baru (test client): dashboard angka nyata, produk seed, pencarian,
  daftar voucher, buat sukses/kurangi stok, tolak melebihi stok, tolak kode
  duplikat, laporan memuat stok_log.

**Hasil**: semua langkah E2E web **LULUS**. Tidak ada blocker.
