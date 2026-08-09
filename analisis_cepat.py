import streamlit as st
from PIL import Image
import easyocr
import re

# === PENGATURAN HALAMAN ===
st.set_page_config(page_title="Analisis Saham Cepat", layout="centered")
st.title("📊 ANALISIS SAHAM OTOMATIS")
st.subheader("Unggah Screenshot atau Masukkan Angka Manual")
st.markdown("---")

# === MUAT ALAT BACA TEKS ===
@st.cache_resource
def inisialisasi_pembaca():
    # Tambahkan 'numeric' agar lebih baik membaca angka
    return easyocr.Reader(['en'])  # Bahasa Inggris saja lebih konsisten untuk angka

pembaca = inisialisasi_pembaca()

# === BAGIAN UNGGAH GAMBAR ===
unggah_gambar = st.file_uploader("📸 Unggah Gambar Indikator (JPG/PNG)", type=["jpg","jpeg","png"])

# === VARIABEL DATA ===
harga = 0.0
rata = 0.0
macd = 0.0
sinyal = 0.0
histogram = 0.0
vol_sekarang = 0
vol_rata = 0

# === JIKA ADA GAMBAR DIUNGGAH ===
if unggah_gambar:
    gambar = Image.open(unggah_gambar)
    st.image(gambar, width=380, caption="Gambar yang Diunggah")
    
    with st.spinner("🔍 Sedang membaca data..."):
        # Konversi gambar ke array agar EasyOCR bisa baca
        import numpy as np
        gambar_np = np.array(gambar)
        hasil_baca = pembaca.readtext(gambar_np, detail=0)
        semua_teks = " ".join(hasil_baca)
        
        # Tampilkan teks yang terbaca (untuk pengecekan)
        with st.expander("🔍 Lihat teks yang terbaca dari gambar"):
            st.code(semua_teks)
        
        # Fungsi ekstraksi angka yang lebih tangguh
        def ambil_angka(pola, teks):
            cocok = re.search(pola, teks, re.IGNORECASE)
            if cocok:
                try:
                    return float(cocok.group(1).replace(',', '.'))
                except:
                    return 0.0
            return 0.0
        
        # Ekstraksi dengan pola yang lebih fleksibel
        harga = ambil_angka(r"Harga\D*([\d.,]+)", semua_teks)
        rata = ambil_angka(r"Rata\D*([\d.,]+)", semua_teks)
        macd = ambil_angka(r"MACD\D*(-?[\d.,]+)", semua_teks)
        sinyal = ambil_angka(r"Sinyal\D*(-?[\d.,]+)", semua_teks)
        histogram = ambil_angka(r"Histogram\D*(-?[\d.,]+)", semua_teks)
        
        # Volume: bisa dalam juta atau ribuan
        vol_sementara = ambil_angka(r"Volume\D*([\d.,]+)", semua_teks)
        vol_rata_sementara = ambil_angka(r"Vol\s*Rata\D*([\d.,]+)", semua_teks)
        
        # Asumsi angka dalam juta (sesuai tampilan Stockbit)
        vol_sekarang = int(vol_sementara * 1_000_000) if vol_sementara > 0 else 0
        vol_rata = int(vol_rata_sementara * 1_000_000) if vol_rata_sementara > 0 else 0

# === BAGIAN KOREKSI / INPUT MANUAL ===
st.markdown("### ✏️ Periksa & Koreksi Angka (jika salah terbaca)")
col1, col2 = st.columns(2)

with col1:
    harga = st.number_input("Harga Terakhir", value=harga, step=1.0, format="%.2f")
    rata = st.number_input("Harga Rata-rata", value=rata, step=1.0, format="%.2f")
    vol_sekarang = st.number_input("Volume Saat Ini", value=vol_sekarang, step=100_000)
    vol_rata = st.number_input("Volume Rata-rata", value=vol_rata, step=100_000)

with col2:
    macd = st.number_input("Nilai MACD", value=macd, step=0.01, format="%.2f")
    sinyal = st.number_input("Nilai Garis Sinyal", value=sinyal, step=0.01, format="%.2f")
    histogram = st.number_input("Nilai Histogram", value=histogram, step=0.01, format="%.2f")

st.markdown("---")

# === TOMBOL ANALISA ===
if st.button("🔍 BERIKAN KEPUTUSAN", type="primary"):
    keputusan = "⏳ TUNGGU DULU"
    alasan = []

    # Aturan analisis
    jenuh_beli = macd > 2.5
    jenuh_jual = macd < -2.0
    sinyal_beli = macd > sinyal and histogram > 0
    sinyal_jual = macd < sinyal and histogram < 0
    harga_atas_rata = harga > rata if rata > 0 else False
    volume_kuat = vol_sekarang > (vol_rata * 1.3) if vol_rata > 0 else False

    # Logika keputusan
    if jenuh_beli:
        keputusan = "🔴 JANGAN BELI / SIAP AMBIL UNTUNG"
        alasan.append(f"MACD {macd:.2f} → Zona Jenuh Beli")
        if histogram <= 0:
            alasan.append("Momentum kenaikan sudah mulai habis")

    elif jenuh_jual and histogram > -0.1:
        keputusan = "🟢 SIAP ANTRI BELI"
        alasan.append(f"MACD {macd:.2f} → Zona Jenuh Jual")
        alasan.append("Kekuatan penurunan mulai habis")

    elif sinyal_beli and not jenuh_beli and harga_atas_rata and volume_kuat:
        keputusan = "🟢 BOLEH DIPERTIMBANGKAN MASUK"
        alasan.append("MACD di atas garis sinyal + Histogram Positif")
        alasan.append("Harga di atas rata-rata + Volume mendukung (>130%)")

    elif sinyal_jual:
        keputusan = "🔴 JANGAN MASUK"
        alasan.append("MACD turun di bawah garis sinyal")

    else:
        alasan.append("Belum ada sinyal yang jelas, lebih baik tunggu konfirmasi")

    # Tampilkan Hasil
    st.success(f"🎯 KEPUTUSAN: {keputusan}")
    st.subheader("📝 Alasan:")
    for poin in alasan:
        st.write(f"✅ {poin}")
    
    st.info("💡 Ingat: Selalu pasang Stop Loss ±2-3% dan ambil untung wajar")
