# examples/buggy_demo.py
# Unit Kompetensi: J.620100.029.02 (Debugging)
#
# File ini berisi DUA versi fungsi yang sama:
#   1. versi_buggy() — sengaja dibuat SALAH (contoh latihan debugging).
#   2. versi_diperbaiki() — versi yang benar setelah ditelusuri.
#
# Fungsi tujuan: menghitung total harga keranjang belanja dengan diskon.
#   - diskon 10% bila subtotal >= 100.000
#   - hasil dibulatkan ke 2 desimal (pembulatan RUPIAH)
#
# BUG yang disengaja (lihat docs/03_debugging_log.md):
#   • `int(harga * 100) / 100` memangkas (truncate) bukan membulatkan,
#     sehingga 1.005 menjadi 1.00, bukan 1.01 (masalah pembulatan).
#   • operasi dikerjakan setelah diskon, menghasilkan selisih kecil pada
#     nilai desimal tertentu.

def versi_buggy(harga_barang: list[float], diskon_persen: float = 10.0) -> float:
    subtotal = sum(harga_barang)
    if subtotal >= 100_000:
        subtotal *= (1 - diskon_persen / 100.0)
    # BUG: truncate (pangkas) bukan round -> 1.005 jadi 1.00
    return int(subtotal * 100) / 100


def versi_diperbaiki(harga_barang: list[float], diskon_persen: float = 10.0) -> float:
    subtotal = sum(harga_barang)
    if subtotal >= 100_000:
        subtotal *= (1 - diskon_persen / 100.0)
    # PERBAIKAN: pakai round() (pembulatan bankir) untuk uang.
    return round(subtotal, 2)


if __name__ == "__main__":
    # subtotal 123.456 (< 100.000 -> tanpa diskon); inti perbedaan truncate vs round.
    keranjang = [123.456]
    print("buggy       :", versi_buggy(keranjang))        # 123.45 (memangkas)
    print("diperbaiki  :", versi_diperbaiki(keranjang))   # 123.46 (membulatkan)
