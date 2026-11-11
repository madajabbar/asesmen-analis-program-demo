# 06. Pengujian
Unit Kompetensi: **J.620100.034.02** (Uji Integrasi) & **J.620100.033.02** (Uji Unit)

## 1. Rencana Uji

### Uji Unit (tanpa DB)
| File | Cakupan |
|---|---|
| `tests/test_algorithms.py` | `quick_sort`, `merge_sort`, `binary_search` (normal, boundary, tidak valid). |
| `tests/test_validation.py` | `validasi_jumlah`, `validasi_kode` (normal, boundary, tidak valid). |

### Uji Integrasi (terhubung MySQL)
| File | Cakupan |
|---|---|
| `tests/test_integration.py` | Koneksi & database, buat voucher sukses (stok berkurang, trigger log, function total), buat voucher gagal (rollback), produk tidak ada, laporan, view, panggil stored procedure langsung. |

**Skip otomatis**: `pytest.mark.skipif(not ping(), ...)` — bila DB tidak tersedia,
uji integrasi di-skip. Pada run E2E, DB tersedia sehingga uji integrasi **harus** jalan.

## 2. Lembar Hasil Uji (Output pytest Nyata)

Tanggal run: **2026-11-11** (MySQL 8 via Docker Compose).

```
============================== 39 passed in 0.40s ==============================
```

Rincian:
- **Uji unit**: 32 lulus (algoritma 17, validasi 15).
- **Uji integrasi**: 7 lulus (terhubung MySQL nyata).
- **Gagal**: 0.

Daftar uji integrasi yang lulus:
```
tests/test_integration.py::test_koneksi_dan_database_ada PASSED
tests/test_integration.py::test_buat_voucher_sukses_kurangi_stok_dan_log PASSED
tests/test_integration.py::test_buat_voucher_stok_kurang_rollback PASSED
tests/test_integration.py::test_buat_voucher_produk_tidak_ada PASSED
tests/test_integration.py::test_laporan_berisi_data PASSED
tests/test_integration.py::test_view_ringkasan_stok_tersedia PASSED
tests/test_integration.py::test_stored_procedure_langsung PASSED
```

Cara menjalankan:
```bash
.venv/bin/python -m pytest tests/ -v
```

## 3. Pengarsipan
- Hasil uji diarsipkan di **E2E_LOG.md** (tanggal, langkah, output nyata).
- Log pengujian terperinci dapat dihasilkan ulang kapan saja dengan:
  ```bash
  .venv/bin/python -m pytest tests/ -v --junitxml=test-report.xml
  ```
- `test-report.xml` dapat diarsipkan sebagai artefak CI bagi asesmen.
