# 03. Log Debugging
Unit Kompetensi: **J.620100.029.02** (Debugging)

Bagian ini mencatat **1 bug nyata** yang ditemui saat membangun proyek ini, serta
**1 contoh latihan** (berlabel jelas) pada `examples/buggy_demo.py`.

---

## A. Bug Nyata 1: Underflow INTEGER UNSIGNED pada Trigger

**Gejala**: Saat menjalankan `buat-voucher` (sukses), aplikasi melempar:
```
mysql.connector.errors.DataError: 1690 (22003):
BIGINT UNSIGNED value is out of range in '(NEW.stok - OLD.stok)'
```

**Cara menemukan (log/breakpoint)**: Debug memakai `mysql` CLI langsung:
1. Jalankan `UPDATE produk SET stok = stok - 1 WHERE id = 6;`
2. Query `SELECT * FROM stok_log;` → baris baru tidak muncul.
3. `SHOW ERRORS;` → pesan 1690 di atas (error diteruskan dari trigger).

**Akar masalah**: Kolom `stok` bertipe `INT UNSIGNED`. Statement di dalam trigger
`NEW.stok - OLD.stok` dihitung sebagai bilangan *unsigned*. Ketika stok *berkurang*
(`NEW.stok < OLD.stok`), hasil pengurangan menjadi negatif, yang tidak dapat
direpresentasikan dalam tipe unsigned → MySQL melempar error 1690 dan membatalkan
transaksi.

**Perbaikan**: Lakukan operasi mengurangi dalam aritmetika bertanda:
```sql
CAST(NEW.stok AS SIGNED) - CAST(OLD.stok AS SIGNED)
```
Setelah perbaikan, `stok_log` terisi benar (mis. perubahan `-5`) dan transaksi
berhasil.

---

## B. Contoh Latihan (berlabel): `examples/buggy_demo.py`
File ini sengaja memuat **versi yang salah** (`versi_buggy`) dan **versi benar**
(`versi_diperbaiki`) dari fungsi penghitung total belanja dengan diskon.

**Gejala**: Untuk subtotal `123.456` (tanpa diskon), `versi_buggy` mengembalikan
`123.45`, sedangkan yang seharusnya adalah `123.46` (pembulatan uang).

**Breakpoint/log**: Tambahkan `print(subtotal)` sebelum return; nilai `123.456`
tetap utuh, tetapi hasil akhir salah besar.

**Akar masalah**: `int(subtotal * 100) / 100` **memangkas (truncate)** desimal,
bukan membulatkan: `int(12345.6) = 12345` → `123.45`, sehingga pecahan sen yang
seharusnya dibulatkan ke atas hilang.

**Perbaikan**: Gunakan `round(subtotal, 2)` (pembulatan untuk uang).

Perbandingan output:
```
buggy       : 90.44
diperbaiki  : 90.45
```
