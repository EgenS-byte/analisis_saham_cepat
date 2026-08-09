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
    return easyocr.Reader(['en','id'])

pembaca = inisialisasi_pembaca()

# === BAGIAN UNGGAH GAMBAR ===
unggah_gambar = st.file_uploader("📸 Unggah Gambar Indikator (JPG/PNG)", type=["jpg","jpeg","png"])

# === VARIABEL DATA ===
harga = 0
rata = 0
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
        hasil_baca = pembaca.readtext(gambar, detail=0)
        semua_teks = " ".join(hasil_baca)
        
        # Ambil angka dari pola teks
        ambil_angka = lambda pola: float(grup.group(1)) if (grup:=re.search(pola, semua_teks)) else 0
        
        harga = ambil_angka(r"Harga\D*(\d+\.?\d*)")
        rata = ambil_angka(r"Rata\D*(\d+\.?\d*)")
        macd = ambil_angka(r"MACD\D*(-?\d+\.?\d*)")
        sinyal = ambil_angka(r"Sinyal\D*(-?\d+\.?\d*)")
        histogram = ambil_angka(r"Histogram\D*(-?\d+\.?\d*)")
        vol_sekarang = int(ambil_angka(r"Volume\D*(\d+\.?\d*)") * 1000000)
        vol_rata = int(ambil_angka(r"Vol\s*Rata\D*(\d+\.?\d*)") * 1000000)

# === BAGIAN KOREKSI / INPUT MANUAL ===
st.markdown("### ✏️ Periksa & Koreksi Angka (jika salah terbaca)")
col1, col2 = st.columns(2)

with col1:
    harga = st.number_input("Harga Terakhir", value=harga, step=1)
    rata = st.number_input("Harga Rata-rata", value=rata, step=1)
    vol_sekarang = st.number_input("Volume Saat Ini", value=vol_sekarang, step=100000)
    vol_rata = st.number_input("Volume Rata-rata", value=vol_rata, step=100000)

with col2:
    macd = st.number_input("Nilai MACD", value=macd, step=0.01)
    sinyal = st.number_input("Nilai Garis Sinyal", value=sinyal, step=0.01)
    histogram = st.number_input("Nilai Histogram", value=histogram, step=0.01)

st.markdown("---")

# === TOMBOL ANALISA ===
if st.button("🔍 BERIKAN KEPUTUSAN", type="primary"):
    keputusan = "⏳ TUNGGU DULU"
    alasan = []

    # Aturan analisis persis seperti yang kita sepakati
    jenuh_beli = macd > 2.5
    jenuh_jual = macd < -2.0
    sinyal_beli = macd > sinyal and histogram > 0
    sinyal_jual = macd < sinyal and histogram < 0
    harga_atas_rata = harga > rata
    volume_kuat = vol_sekarang > (vol_rata * 1.3) if vol_rata > 0 else False

    # Logika keputusan
    if jenuh_beli:
        keputusan = "🔴 JANGAN BELI / SIAP AMBIL UNTUNG"
        alasan.append(f"MACD {macd:.2f} → Zona Jenuh Beli")
        if histogram <= 0: alasan.append("Momentum kenaikan sudah habis")

    elif jenuh_jual and histogram > -0.1:
        keputusan = "🟢 SIAP ANTRI BELI"
        alasan.append(f"MACD {macd:.2f} → Zona Jenuh Jual")
        alasan.append("Kekuatan penurunan mulai habis")

    elif sinyal_beli and not jenuh_beli and harga_atas_rata and volume_kuat:
        keputusan = "🟢 BOLEH DIPERTIMBANGKAN MASUK"
        alasan.append("MACD di atas garis sinyal + Histogram Hijau")
        alasan.append("Harga di atas rata-rata + Volume mendukung")

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

