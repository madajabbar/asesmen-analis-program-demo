-- =====================================================================
-- schema.sql — Skema basis data: asesmen_demo
-- Proyek: asesmen-analis-program-demo (portofolio asesmen BNSP Analis Program)
-- Unit Kompetensi: J.620100.020.02 (SQL)
--
-- Berisi: pembuatan database, tabel (kategori, produk, voucher, stok_log),
-- CREATE VIEW, CREATE INDEX, 1 stored procedure, 1 function, 1 trigger,
-- serta contoh pemakaian COMMIT / ROLLBACK.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. DATABASE
-- ---------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS asesmen_demo
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE asesmen_demo;

-- ---------------------------------------------------------------------
-- 2. TABEL
-- ---------------------------------------------------------------------
-- Tabel kategori: pengelompokan produk.
CREATE TABLE IF NOT EXISTS kategori (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nama        VARCHAR(80)  NOT NULL,
    deskripsi   VARCHAR(255) NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_kategori_nama (nama)
) ENGINE=InnoDB;

-- Tabel produk: barang inventaris. FK ke kategori.
CREATE TABLE IF NOT EXISTS produk (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nama        VARCHAR(120) NOT NULL,
    kategori_id INT UNSIGNED NOT NULL,
    harga       DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    stok       INT UNSIGNED NOT NULL DEFAULT 0,
    min_stok    INT UNSIGNED NOT NULL DEFAULT 5,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_produk_kategori FOREIGN KEY (kategori_id)
        REFERENCES kategori (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    INDEX idx_produk_nama (nama),          -- dipakai query pencarian (lihat docs/04_profiling.md)
    INDEX idx_produk_kategori (kategori_id)
) ENGINE=InnoDB;

-- Tabel voucher: bukti pembayaran (satu voucher = satu baris produk).
CREATE TABLE IF NOT EXISTS voucher (
    id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
    kode         VARCHAR(40)  NOT NULL,
    produk_id    INT UNSIGNED NOT NULL,
    jumlah       INT UNSIGNED NOT NULL,
    total_harga  DECIMAL(12,2) NOT NULL,
    status       ENUM('AKTIF','DIBATALKAN') NOT NULL DEFAULT 'AKTIF',
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_voucher_kode (kode),
    CONSTRAINT fk_voucher_produk FOREIGN KEY (produk_id)
        REFERENCES produk (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Tabel stok_log: jejak audit perubahan stok (diisi trigger).
CREATE TABLE IF NOT EXISTS stok_log (
    id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
    produk_id     INT UNSIGNED NOT NULL,
    stok_sebelum  INT NOT NULL,
    stok_sesudah  INT NOT NULL,
    perubahan      INT NOT NULL,
    alasan        VARCHAR(120) NOT NULL DEFAULT 'perubahan_stok',
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_stok_log_produk (produk_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3. CREATE INDEX
-- ---------------------------------------------------------------------
-- (index juga dibuat inline di definisi tabel di atas:
--   idx_produk_nama, idx_produk_kategori, idx_stok_log_produk)
-- Index tambahan utk agregasi dapat ditambahkan di sini bila diperlukan;
-- pada proyek ini seluruh index esensial sudah dibuat inline di definisi
-- tabel (idx_produk_nama, idx_produk_kategori, idx_stok_log_produk).
-- Catatan: MySQL 8 tidak mendukung CREATE/DROP INDEX IF EXISTS, sehingga
-- skema ini dijaga idempotent dengan menghindari DDL terpisah.

-- ---------------------------------------------------------------------
-- 4. CREATE VIEW
-- ---------------------------------------------------------------------
-- v_ringkasan_stok: JOIN antar tabel kategori + produk.
CREATE OR REPLACE VIEW v_ringkasan_stok AS
SELECT
    p.id          AS produk_id,
    p.nama        AS nama_produk,
    k.nama        AS nama_kategori,
    p.harga       AS harga_satuan,
    p.stok        AS stok,
    p.harga * p.stok AS nilai_persediaan,
    CASE
        WHEN p.stok = 0 THEN 'HABIS'
        WHEN p.stok <= p.min_stok THEN 'MENIPIS'
        ELSE 'CUKUP'
    END           AS status_stok
FROM produk p
JOIN kategori k ON k.id = p.kategori_id;

-- v_ringkasan_voucher: JOIN antar tabel voucher + produk + kategori.
CREATE OR REPLACE VIEW v_ringkasan_voucher AS
SELECT
    v.id          AS voucher_id,
    v.kode        AS kode_voucher,
    v.produk_id   AS produk_id,
    p.nama        AS nama_produk,
    k.nama        AS nama_kategori,
    v.jumlah      AS jumlah,
    v.total_harga AS total_harga,
    v.status      AS status_voucher,
    v.created_at  AS tanggal
FROM voucher v
JOIN produk p ON p.id = v.produk_id
JOIN kategori k ON k.id = p.kategori_id;

-- v_laporan_inventaris: contoh JOIN ANTAR VIEW (v_ringkasan_stok
-- digabung dengan v_ringkasan_voucher).
CREATE OR REPLACE VIEW v_laporan_inventaris AS
SELECT
    s.produk_id,
    s.nama_produk,
    s.nama_kategori,
    s.stok,
    s.nilai_persediaan,
    s.status_stok,
    COUNT(v.voucher_id)              AS jumlah_voucher,
    COALESCE(SUM(v.total_harga), 0) AS total_penjualan
FROM v_ringkasan_stok s
LEFT JOIN v_ringkasan_voucher v ON v.produk_id = s.produk_id
      AND v.status_voucher = 'AKTIF'
GROUP BY s.produk_id, s.nama_produk, s.nama_kategori,
         s.stok, s.nilai_persediaan, s.status_stok;

-- ---------------------------------------------------------------------
-- 5. FUNCTION
-- ---------------------------------------------------------------------
-- fn_nilai_persediaan: menjumlahkan nilai seluruh persediaan (stok * harga).
DROP FUNCTION IF EXISTS fn_nilai_persediaan;
DELIMITER $$
CREATE FUNCTION fn_nilai_persediaan()
RETURNS DECIMAL(12,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE total DECIMAL(12,2);
    SELECT COALESCE(SUM(harga * stok), 0) INTO total FROM produk;
    RETURN total;
END$$
DELIMITER ;

-- fn_total_voucher: menghitung total harga sebuah voucher aktiv kode.
DROP FUNCTION IF EXISTS fn_total_voucher;
DELIMITER $$
CREATE FUNCTION fn_total_voucher(p_kode VARCHAR(40))
RETURNS DECIMAL(12,2)
READS SQL DATA
BEGIN
    DECLARE total DECIMAL(12,2);
    SELECT COALESCE(total_harga, 0) INTO total
    FROM voucher WHERE kode = p_kode LIMIT 1;
    RETURN total;
END$$
DELIMITER ;

-- ---------------------------------------------------------------------
-- 6. STORED PROCEDURE (dengan transaksi COMMIT / ROLLBACK)
-- ---------------------------------------------------------------------
-- sp_buat_voucher:
--   • menyisipkan voucher
--   • mengurangi stok produk di dalam transaksi yang sama
--   • bila stok tidak cukup -> ROLLBACK + SIGNAL error (data tidak berubah)
--   • bila sukses -> COMMIT
DROP PROCEDURE IF EXISTS sp_buat_voucher;
DELIMITER $$
CREATE PROCEDURE sp_buat_voucher(
    IN p_kode     VARCHAR(40),
    IN p_produk_id INT,
    IN p_jumlah    INT
)
BEGIN
    DECLARE v_harga DECIMAL(12,2);
    DECLARE v_stok INT;

    START TRANSACTION;

    -- Ambil harga dan stok produk, kunci baris untuk mencegah race condition.
    SELECT harga, stok INTO v_harga, v_stok
    FROM produk WHERE id = p_produk_id FOR UPDATE;

    -- Validasi: stok tidak cukup -> ROLLBACK.
    IF v_stok < p_jumlah THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Stok tidak mencukupi untuk membuat voucher';
    END IF;

    -- Sisipkan voucher.
    INSERT INTO voucher (kode, produk_id, jumlah, total_harga, status)
    VALUES (p_kode, p_produk_id, p_jumlah, v_harga * p_jumlah, 'AKTIF');

    -- Kurangi stok (trigger stok_log akan mencatat otomatis).
    UPDATE produk SET stok = stok - p_jumlah WHERE id = p_produk_id;

    COMMIT;
END$$
DELIMITER ;

-- ---------------------------------------------------------------------
-- 7. TRIGGER
-- ---------------------------------------------------------------------
-- tr_produk_stok_after_update: setelah UPDATE stok pada tabel `produk`,
-- menyisipkan catatan perubahan ke tabel `stok_log`.
DROP TRIGGER IF EXISTS tr_produk_stok_after_update;
DELIMITER $$
CREATE TRIGGER tr_produk_stok_after_update
AFTER UPDATE ON produk
FOR EACH ROW
BEGIN
    IF OLD.stok <> NEW.stok THEN
        INSERT INTO stok_log (produk_id, stok_sebelum, stok_sesudah, perubahan, alasan)
        VALUES (NEW.id, OLD.stok, NEW.stok,
                CAST(NEW.stok AS SIGNED) - CAST(OLD.stok AS SIGNED),
                'perubahan_stok');
    END IF;
END$$
DELIMITER ;

-- ---------------------------------------------------------------------
-- 8. CONTOH PEMAKAIAN COMMIT / ROLLBACK (komentar dokumentasi)
-- ---------------------------------------------------------------------
-- COMMIT   : dipakai di akhir sp_buat_voucher (jalur sukses) untuk
--             mengunci semua perubahan yang sebelumnya dimulai START TRANSACTION.
-- ROLLBACK : dipakai pada jalur stok tidak cukup agar voucher yang sudah
--             disisipkan dibatalkan dan data kembali ke kondisi semula.
--
-- Lihat juga src/service.py yang mendemonstrasikan transaksi yang sama
-- dari sisi aplikasi Python (commit/rollback eksplisit).
