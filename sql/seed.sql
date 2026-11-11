-- =====================================================================
-- seed.sql — Data contoh (DML) untuk asesmen_demo
-- Unit Kompetensi: J.620100.020.02 (SQL) — contoh DML insert/update/select
-- =====================================================================
USE asesmen_demo;

-- Kategori
INSERT INTO kategori (nama, deskripsi) VALUES
    ('Elektronik',  'Barang elektronik dan aksesori'),
    ('Alat Tulis',  'Perlengkapan kantor dan alat tulis'),
    ('Peralatan Dapur', 'Peralatan rumah tangga dapur'),
    ('Minuman',     'Minuman dalam kemasan')
ON DUPLICATE KEY UPDATE nama = VALUES(nama);

-- Produk (stok awal sengaja dibuat kecil agar mudah diuji)
INSERT INTO produk (nama, kategori_id, harga, stok, min_stok) VALUES
    ('Laptop ASUS VivoBook',   1, 8500000, 12, 3),
    ('Mouse Wireless Logitech', 1, 150000,  30, 5),
    ('Keyboard Mekanik',        1, 400000,  8,  2),
    ('Monitor 24 inch',         1, 1700000, 6,  2),
    ('Kertas A4 80gsm',         2, 45000,   100, 20),
    ('Pulpen Standard AE7',     2, 4000,    300, 50),
    ('Spidol Whiteboard',       2, 12000,   60,  10),
    ('Panci Stainless',         3, 125000,   15, 3),
    ('Wajan Anti Lengket',      3, 110000,   2,  3),   -- stok < min -> MENIPIS
    ('Air Mineral 600ml',       4, 3500,    0,  20)    -- stok 0 -> HABIS
ON DUPLICATE KEY UPDATE nama = VALUES(nama);

-- Contoh DML SELECT dengan JOIN (contoh pemakaian di luar aplikasi)
-- SELECT k.nama AS kategori, p.nama, p.harga, p.stok
-- FROM produk p JOIN kategori k ON k.id = p.kategori_id
-- WHERE p.stok <= p.min_stok ORDER BY p.stok;
