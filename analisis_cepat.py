import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# ---------------------- KONFIGURASI ----------------------
st.set_page_config(page_title="Pantau Sinyal Trading", layout="wide")
st.title("📈 Pantauan Sinyal Trading (Data 30 Menit)")
st.caption("Sumber: Yahoo Finance | Indikator: SMA, MACD, Volume")

# ---------------------- INPUT KODE SAHAM ----------------------
st.markdown("### ✏️ Masukkan Kode Emiten")
st.info("💡 Akhiri dengan .JK untuk saham Indonesia (contoh: BBRI.JK)")

kode1 = st.text_input("Emiten 1", value="BBRI.JK").strip().upper()
kode2 = st.text_input("Emiten 2", value="BMRI.JK").strip().upper()
kode3 = st.text_input("Emiten 3", value="BBCA.JK").strip().upper()

DAFTAR = {
    f"Emiten 1": kode1,
    f"Emiten 2": kode2,
    f"Emiten 3": kode3
}

# ---------------------- FUNGSI INDIKATOR ----------------------
def hitung_sma(df, periode=20):
    df['SMA'] = df['Close'].rolling(window=periode).mean()
    return df

def hitung_macd(df, p1=12, p2=26, p3=9):
    ema12 = df['Close'].ewm(span=p1, adjust=False).mean()
    ema26 = df['Close'].ewm(span=p2, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Sinyal'] = df['MACD'].ewm(span=p3, adjust=False).mean()
    df['Hist'] = df['MACD'] - df['Sinyal']
    return df

def ambil_data(kode):
    """Ambil data 30 menit dengan rentang waktu yang disesuaikan"""
    hari_coba = [7, 10, 14]  # Coba bertahap: 7 hari → 10 hari → 14 hari
    for hari in hari_coba:
        try:
            df = yf.download(kode, period=f"{hari}d", interval="30m", progress=False)
            if not df.empty and len(df) >= 30:
                return df
        except Exception:
            continue
    return pd.DataFrame()

def sinyal_trading(df):
    if len(df) < 26:
        return "🔄 Data Kurang", ["Belum cukup data untuk analisis"], None
    d = df.iloc[-1]
    sma_vol = df['Volume'].rolling(20).mean().iloc[-1]
    alasan = []
    sinyal = "🔄 TUNGGU"
    try:
        if d['MACD'] > d['Sinyal'] and d['Close'] > d['SMA'] and d['Volume'] > sma_vol:
            sinyal = "✅ BELI"
            alasan = ["MACD di atas Sinyal", "Harga > SMA", "Volume Naik"]
        elif d['MACD'] < d['Sinyal'] and d['Close'] < d['SMA']:
            sinyal = "❌ JUAL"
            alasan = ["MACD di bawah Sinyal", "Harga < SMA"]
        else:
            alasan = ["Belum memenuhi syarat Beli maupun Jual"]
    except Exception:
        alasan = ["Data belum cukup lengkap untuk menghitung indikator"]
    return sinyal, alasan, d

def buat_grafik(df, nama, kode):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 9), sharex=True,
                                         gridspec_kw={'height_ratios': [3, 2, 1]})
    ax1.plot(df.index, df['Close'], 'b-', linewidth=1.5, label='Harga')
    ax1.plot(df.index, df['SMA'], 'orange', linewidth=1.5, label='SMA 20')
    ax1.set_title(f"{nama} ({kode}) — Data 30 Menit", fontweight='bold')
    ax1.set_ylabel("Harga"); ax1.legend(loc='upper left'); ax1.grid(alpha=0.3)

    ax2.plot(df.index, df['MACD'], 'g-', label='MACD')
    ax2.plot(df.index, df['Sinyal'], 'r-', label='Sinyal')
    warna = ['g' if h >= 0 else 'r' for h in df['Hist']]
    ax2.bar(df.index, df['Hist'], color=warna, alpha=0.3, width=0.02)
    ax2.set_ylabel("MACD"); ax2.legend(loc='upper left'); ax2.grid(alpha=0.3)

    ax3.bar(df.index, df['Volume'], color='gray', alpha=0.5, width=0.02, label='Volume')
    ax3.plot(df.index, df['Volume'].rolling(20).mean(), 'purple', label='Rata2 Volume')
    ax3.set_ylabel("Volume"); ax3.legend(loc='upper left'); ax3.grid(alpha=0.3)

    plt.xticks(rotation=45); plt.tight_layout()
    return fig

def simpan_gambar(fig, fmt):
    b = BytesIO()
    fig.savefig(b, format=fmt.lower(), dpi=150, bbox_inches='tight')
    b.seek(0)
    return b

# ---------------------- TOMBOL UTAMA ----------------------
st.markdown("---")
fmt = st.radio("Format Gambar:", ["PNG", "JPEG"], horizontal=True)

if st.button("🔄 AMBIL DATA & ANALISIS", type="primary"):
    for nama, kode in DAFTAR.items():
        st.markdown(f"---\n### 📊 {nama}: `{kode}`")
        
        if not kode or ".JK" not in kode:
            st.error("❌ Format salah! Harus berakhiran .JK (contoh: BBRI.JK)")
            continue

        with st.spinner(f"Mengambil data {kode}..."):
            df = ambil_data(kode)
        
        if df.empty:
            st.error("❌ Tidak dapat mengambil data! Kemungkinan:")
            st.write("- Kode saham belum pernah diperdagangkan")
            st.write("- Yahoo Finance sedang tidak dapat diakses")
            st.write("- Data 30 menit tidak tersedia untuk saham ini")
            continue

        df = hitung_sma(df)
        df = hitung_macd(df)
        sinyal, alasan, d = sinyal_trading(df)

        st.subheader(f"Keputusan: {sinyal}")
        for a in alasan: st.write(f"- {a}")
        
        if d is not None:
            st.write(f"Harga: **{d['Close']:,.2f}** | SMA: **{d['SMA']:,.2f}** | MACD: **{d['MACD']:.4f}**")

        fig = buat_grafik(df, nama, kode)
        st.pyplot(fig)
        berkas = simpan_gambar(fig, fmt)
        st.download_button(f"📥 Unduh {fmt}", berkas, f"{kode.replace('.','_')}.{fmt.lower()}", f"image/{fmt.lower()}")
        plt.close(fig)

    st.success("✅ Selesai!")
else:
    st.info("Masukkan kode saham lalu tekan tombol di atas.")
