-- =====================================================================
-- grants.sql — Contoh GRANT untuk user aplikasi (least privilege)
-- Unit Kompetensi: J.620100.021.02 (Akses Basis Data)
--
-- User aplikasi `app_asesmen` hanya diberi hak yang dibutuhkan:
--   SELECT, INSERT, UPDATE, DELETE pada tabel data (bukan DDL),
--   serta EXECUTE untuk panggil stored procedure / function.
-- User ini TIDAK mendapat hak CREATE/DROP/ALTER/GRANT (bukan DBA).
-- =====================================================================
USE asesmen_demo;

-- Buat user aplikasi (dengan password demo lokal; ganti di produksi).
CREATE USER IF NOT EXISTS 'app_asesmen'@'%' IDENTIFIED BY 'app_demo_lokal_456';

-- Hak terbatas pada tabel data.
GRANT SELECT, INSERT, UPDATE, DELETE ON asesmen_demo.kategori  TO 'app_asesmen'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON asesmen_demo.produk    TO 'app_asesmen'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON asesmen_demo.voucher    TO 'app_asesmen'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON asesmen_demo.stok_log   TO 'app_asesmen'@'%';

-- Hak untuk memanggil stored procedure dan function.
GRANT EXECUTE ON PROCEDURE asesmen_demo.sp_buat_voucher TO 'app_asesmen'@'%';
GRANT EXECUTE ON FUNCTION  asesmen_demo.fn_nilai_persediaan TO 'app_asesmen'@'%';
GRANT EXECUTE ON FUNCTION  asesmen_demo.fn_total_voucher TO 'app_asesmen'@'%';

FLUSH PRIVILEGES;

-- Catatan: user aplikasi TIDAK memiliki hak buat/ubah skema, sehingga
-- proses `init-db` (pembuatan skema) dijalankan dengan user root/dba,
-- sedangkan operasi harian aplikasi memakai `app_asesmen`.
