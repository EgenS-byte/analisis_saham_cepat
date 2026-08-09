import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# ---------------------- KONFIGURASI APLIKASI ----------------------
st.set_page_config(page_title="Pantau Sinyal Trading", layout="wide")
st.title("📈 Pantauan Sinyal Trading (Kerangka Waktu 30 Menit)")
st.subheader("Sumber Data: Yahoo Finance | Indikator: Harga Rata-rata, MACD, Volume")

# ---------------------- INPUT KODE SAHAM OLEH PENGGUNA ----------------------
st.markdown("### ✏️ Masukkan Kode Emiten yang Akan Dipantau")
st.caption("Contoh: BBRI.JK, BMRI.JK, BBCA.JK — akhiri dengan .JK untuk saham Indonesia")

kode1 = st.text_input("Emiten 1", value="BBRI.JK")
kode2 = st.text_input("Emiten 2", value="BMRI.JK")
kode3 = st.text_input("Emiten 3", value="BBCA.JK")

# Susun menjadi daftar
DAFTAR_EMITEN = {
    f"Emiten 1 ({kode1})": kode1.strip().upper(),
    f"Emiten 2 ({kode2})": kode2.strip().upper(),
    f"Emiten 3 ({kode3})": kode3.strip().upper()
}

# ---------------------- FUNGSI PENGHITUNG INDIKATOR ----------------------
def hitung_harga_rata_rata(df, periode=20):
    """Hitung Harga Rata-rata / SMA"""
    df['SMA'] = df['Close'].rolling(window=periode).mean()
    return df

def hitung_macd(df, cepat=12, lambat=26, sinyal=9):
    """Hitung Indikator MACD"""
    ema_cepat = df['Close'].ewm(span=cepat, adjust=False).mean()
    ema_lambat = df['Close'].ewm(span=lambat, adjust=False).mean()
    df['MACD'] = ema_cepat - ema_lambat
    df['Sinyal'] = df['MACD'].ewm(span=sinyal, adjust=False).mean()
    df['Histogram'] = df['MACD'] - df['Sinyal']
    return df

def ambil_data_30menit(kode_saham, hari_histori=5):
    """
    Ambil data 30 menit dari Yahoo Finance
    Optimal: 5 hari histori → ±65 batang 30 menit
    """
    try:
        data = yf.download(
            tickers=kode_saham,
            period=f"{hari_histori}d",
            interval="30m",
            progress=False
        )
        data = data.dropna()
        return data
    except Exception as e:
        st.error(f"❌ Gagal mengambil data `{kode_saham}`: {str(e)}")
        return pd.DataFrame()

def berikan_sinyal_terakhir(df):
    """Buat keputusan berdasarkan data terakhir"""
    terakhir = df.iloc[-1]
    sinyal = "🔄 TUNGGU"
    alasan = []

    # Kondisi Beli
    if (terakhir['MACD'] > terakhir['Sinyal']) and \
       (terakhir['Close'] > terakhir['SMA']) and \
       (terakhir['Volume'] > df['Volume'].rolling(20).mean().iloc[-1]):
        sinyal = "✅ BELI"
        alasan = ["MACD di atas Garis Sinyal", "Harga di atas Rata-rata", "Volume Meningkat"]
    
    # Kondisi Jual
    elif (terakhir['MACD'] < terakhir['Sinyal']) and \
         (terakhir['Close'] < terakhir['SMA']):
        sinyal = "❌ JUAL"
        alasan = ["MACD di bawah Garis Sinyal", "Harga di bawah Rata-rata"]
    
    return sinyal, alasan, terakhir

# ---------------------- FUNGSI GRAFIK & SIMPAN GAMBAR ----------------------
def buat_grafik(df, nama, kode):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True,
                                         gridspec_kw={'height_ratios': [3, 2, 1]})
    
    # Grafik Harga + SMA
    ax1.plot(df.index, df['Close'], label='Harga Tutup', color='blue', linewidth=1.5)
    ax1.plot(df.index, df['SMA'], label='Harga Rata-rata (20)', color='orange', linewidth=1.5)
    ax1.set_title(f"{nama} ({kode}) | Data 30 Menit", fontsize=14, fontweight='bold')
    ax1.set_ylabel("Harga")
    ax1.legend(loc='upper left')
    ax1.grid(alpha=0.3)

    # Grafik MACD
    ax2.plot(df.index, df['MACD'], label='MACD', color='green', linewidth=1.5)
    ax2.plot(df.index, df['Sinyal'], label='Garis Sinyal', color='red', linewidth=1.5)
    warna_hist = ['green' if h >= 0 else 'red' for h in df['Histogram']]
    ax2.bar(df.index, df['Histogram'], color=warna_hist, alpha=0.3, width=0.02)
    ax2.set_ylabel("MACD")
    ax2.legend(loc='upper left')
    ax2.grid(alpha=0.3)

    # Grafik Volume
    ax3.bar(df.index, df['Volume'], label='Volume', color='gray', alpha=0.5, width=0.02)
    rata_volume = df['Volume'].rolling(20).mean()
    ax3.plot(df.index, rata_volume, label='Rata-rata Volume', color='purple', linewidth=1.2)
    ax3.set_ylabel("Volume")
    ax3.legend(loc='upper left')
    ax3.grid(alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

def simpan_gambar(fig, format_gambar):
    """Simpan grafik ke dalam memori untuk diunduh"""
    buffer = BytesIO()
    fig.savefig(buffer, format=format_gambar.lower(), dpi=150, bbox_inches='tight')
    buffer.seek(0)
    return buffer

# ---------------------- TOMBOL UTAMA ----------------------
st.markdown("---")
format_pilihan = st.radio("Format unduhan gambar:", ["PNG", "JPEG"], horizontal=True)

if st.button("🔄 AMBIL DATA & ANALISIS", type="primary"):
    st.info("Mengambil data terbaru dari Yahoo Finance...")

    for nama_emiten, kode in DAFTAR_EMITEN.items():
        st.markdown(f"---\n### 📊 {nama_emiten}")

        # Validasi kode
        if not kode or "." not in kode:
            st.warning(f"⚠️ Kode saham `{kode}` tidak valid. Periksa kembali!")
            continue

        # Ambil & proses data
        df = ambil_data_30menit(kode, hari_histori=5)  # ✅ 5 hari = jumlah optimal
        if len(df) == 0:
            st.warning(f"⚠️ Tidak ada data untuk `{kode}`. Periksa kode saham!")
            continue
        if len(df) < 30:
            st.warning(f"⚠️ Data terbatas: hanya ada {len(df)} batang.")

        df = hitung_harga_rata_rata(df, periode=20)
        df = hitung_macd(df)
        sinyal, alasan, terakhir = berikan_sinyal_terakhir(df)

        # Tampilkan ringkasan
        st.subheader(f"Keputusan: {sinyal}")
        if alasan:
            for a in alasan:
                st.write(f"- {a}")
        st.write(f"Harga Terakhir: **{terakhir['Close']:,.2f}** | "
                 f"SMA: **{terakhir['SMA']:,.2f}** | "
                 f"MACD: **{terakhir['MACD']:.4f}** | "
                 f"Sinyal: **{terakhir['Sinyal']:.4f}**")

        # Tampilkan grafik
        fig = buat_grafik(df, nama_emiten, kode)
        st.pyplot(fig)

        # Tombol unduh gambar
        gambar_buffer = simpan_gambar(fig, format_pilihan)
        nama_file = f"{kode.replace('.','_')}_grafik.{format_pilihan.lower()}"
        st.download_button(
            label=f"📥 Unduh Grafik ({format_pilihan})",
            data=gambar_buffer,
            file_name=nama_file,
            mime=f"image/{format_pilihan.lower()}"
        )

        plt.close(fig)  # Bersihkan memori

    st.success("✅ Analisis selesai! Data diperbarui dari Yahoo Finance.")

else:
    st.info("Tekan tombol **AMBIL DATA & ANALISIS** di atas untuk mulai mengambil data dan melihat sinyal trading.")

# ---------------------- PENJELASAN ----------------------
with st.expander("ℹ️ Informasi Penggunaan"):
    st.markdown("""
    - **Cara mengubah saham**: Ketik kode saham langsung di kolom input di atas (contoh: `TLKM.JK`, `ASII.JK`, `ICBP.JK`)
    - **Kerangka waktu**: 30 menit
    - **Data histori**: 5 hari perdagangan terakhir → menghasilkan ±65 batang 30 menit (jumlah optimal untuk perhitungan MACD & SMA)
    - **Indikator**: SMA 20 periode, MACD (12,26,9), Volume
    - **Pembaruan data**: Hanya saat tombol ditekan → mengambil data terbaru dari Yahoo Finance
    - **Format gambar**: Bisa dipilih **PNG** atau **JPEG**, lalu tekan tombol unduh
    - **Format kode**: Akhiri dengan `.JK` untuk saham Indonesia (contoh: `BBRI.JK`)
    """)
