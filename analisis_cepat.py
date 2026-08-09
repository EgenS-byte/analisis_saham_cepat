import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# ---------------------- KONFIGURASI ----------------------
st.set_page_config(page_title="Pantau Sinyal Trading", layout="wide")
st.title("📈 Pantauan Sinyal Trading (Data 30 Menit)")
st.caption("Indikator: SMA · MACD · Volume · RSI | Sumber: Yahoo Finance")

# ---------------------- INPUT KODE SAHAM ----------------------
st.markdown("### ✏️ Masukkan Kode Emiten")
st.info("💡 Akhiri dengan .JK untuk saham Indonesia (contoh: BUMI.JK)")

# Nilai bawaan: BUMI, DEWA, BNBR — tetap bisa diganti kapan saja
kode1 = st.text_input("Emiten 1", value="BUMI.JK").strip().upper()
kode2 = st.text_input("Emiten 2", value="DEWA.JK").strip().upper()
kode3 = st.text_input("Emiten 3", value="BNBR.JK").strip().upper()

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
    df['Sinyal_MACD'] = df['MACD'].ewm(span=p3, adjust=False).mean()
    df['Hist'] = df['MACD'] - df['Sinyal_MACD']
    return df

def hitung_rsi(df, periode=14):
    """Hitung Indikator RSI (Relative Strength Index)"""
    perubahan = df['Close'].diff(1)
    kenaikan = perubahan.where(perubahan > 0, 0)
    penurunan = (-perubahan).where(perubahan < 0, 0)

    rata_kenaikan = kenaikan.rolling(window=periode).mean()
    rata_penurunan = penurunan.rolling(window=periode).mean()

    kekuatan_relatif = rata_kenaikan / rata_penurunan
    df['RSI'] = 100 - (100 / (1 + kekuatan_relatif))
    return df

def ambil_data(kode):
    """Ambil data 30 menit — cari sampai cukup batang atau maksimal 30 hari"""
    for hari in [10, 15, 20, 30]:
        try:
            df = yf.download(kode, period=f"{hari}d", interval="30m", progress=False)
            if not df.empty:
                jumlah = len(df)
                st.info(f"📥 Data diterima: **{jumlah} batang 30 menit** (dari {hari} hari terakhir)")
                if jumlah >= 45:  # RSI butuh data lebih banyak → naikkan syarat minimal
                    return df
        except Exception:
            continue
    return pd.DataFrame()

def sinyal_trading(df):
    minimal = 45  # RSI butuh minimal 14 + data awalan
    if len(df) < minimal:
        return "🔄 Data Kurang", [f"Perlu minimal {minimal} batang, saat ini hanya {len(df)}. Coba saat pasar aktif (Senin–Jumat)."], None
    
    d = df.iloc[-1]
    sma_vol = df['Volume'].rolling(20).mean().iloc[-1]
    alasan = []
    sinyal = "🔄 TUNGGU"

    try:
        # ✅ KONDISI BELI: Semua indikator sepakat
        if (d['MACD'] > d['Sinyal_MACD']) and \
           (d['Close'] > d['SMA']) and \
           (d['Volume'] > sma_vol) and \
           (d['RSI'] > 50 and d['RSI'] < 70):  # RSI naik tapi belum jenuh beli
            sinyal = "✅ BELI"
            alasan = [
                "MACD di atas Garis Sinyal",
                "Harga di atas Rata-rata (SMA 20)",
                "Volume lebih tinggi dari rata-rata",
                f"RSI = {d['RSI']:.1f} → Tren naik sehat"
            ]

        # ❌ KONDISI JUAL: Semua indikator sepakat
        elif (d['MACD'] < d['Sinyal_MACD']) and \
             (d['Close'] < d['SMA']) and \
             (d['RSI'] < 50 or d['RSI'] > 75):  # RSI turun atau sudah jenuh beli berlebih
            sinyal = "❌ JUAL"
            alasan = [
                "MACD di bawah Garis Sinyal",
                "Harga di bawah Rata-rata (SMA 20)",
                f"RSI = {d['RSI']:.1f} → Tren melemah / Jenuh"
            ]

        # 🔄 TUNGGU: Belum sepakat semua
        else:
            alasan = [
                f"RSI = {d['RSI']:.1f}",
                "Belum semua indikator sepakat → tunggu konfirmasi berikutnya"
            ]
    except Exception:
        alasan = ["Indikator belum terbentuk sempurna, tunggu data berikutnya"]
    
    return sinyal, alasan, d

def buat_grafik(df, nama, kode):
    """Grafik sekarang bertambah bagian RSI"""
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 11), sharex=True,
                                         gridspec_kw={'height_ratios': [3, 2, 1.5, 1.5]})
    
    # 1. Harga + SMA
    ax1.plot(df.index, df['Close'], 'b-', linewidth=1.5, label='Harga Tutup')
    ax1.plot(df.index, df['SMA'], 'orange', linewidth=1.5, label='SMA 20')
    ax1.set_title(f"{nama} ({kode}) | Kerangka Waktu 30 Menit", fontweight='bold')
    ax1.set_ylabel("Harga"); ax1.legend(loc='upper left'); ax1.grid(alpha=0.3)

    # 2. MACD
    ax2.plot(df.index, df['MACD'], 'g-', label='MACD')
    ax2.plot(df.index, df['Sinyal_MACD'], 'r-', label='Garis Sinyal')
    warna = ['g' if h >= 0 else 'r' for h in df['Hist']]
    ax2.bar(df.index, df['Hist'], color=warna, alpha=0.3, width=0.02)
    ax2.set_ylabel("MACD"); ax2.legend(loc='upper left'); ax2.grid(alpha=0.3)

    # 3. RSI ✅ BARU
    ax3.plot(df.index, df['RSI'], 'purple', linewidth=1.5, label='RSI (14)')
    ax3.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='Jenuh Beli (70)')
    ax3.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='Jenuh Jual (30)')
    ax3.axhline(y=50, color='gray', linestyle=':', alpha=0.4)
    ax3.set_ylabel("RSI"); ax3.legend(loc='upper left'); ax3.grid(alpha=0.3)
    ax3.set_ylim(0, 100)

    # 4. Volume
    ax4.bar(df.index, df['Volume'], color='gray', alpha=0.5, width=0.02, label='Volume')
    ax4.plot(df.index, df['Volume'].rolling(20).mean(), 'darkcyan', label='Rata-rata Volume')
    ax4.set_ylabel("Volume"); ax4.legend(loc='upper left'); ax4.grid(alpha=0.3)

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
            st.error("❌ Format salah! Harus berakhiran .JK (contoh: BUMI.JK)")
            continue

        with st.spinner(f"Mengambil data {kode}..."):
            df = ambil_data(kode)
        
        if df.empty:
            st.error("❌ Tidak dapat mengambil data!")
            st.info("""
                Kemungkinan penyebab:
                - Data 30 menit tidak tersedia untuk saham ini
                - Yahoo Finance sedang membatasi akses
                - Hari ini akhir pekan/libur → coba saat pasar buka (Senin–Jumat)
            """)
            continue

        # Hitung SEMUA indikator
        df = hitung_sma(df)
        df = hitung_macd(df)
        df = hitung_rsi(df)  # ✅ RSI aktif!

        sinyal, alasan, d = sinyal_trading(df)

        st.subheader(f"Keputusan: {sinyal}")
        for a in alasan: st.write(f"- {a}")
        
        if d is not None:
            st.write(f"Harga: **{d['Close']:,.2f}** | SMA: **{d['SMA']:,.2f}** | MACD: **{d['MACD']:.4f}** | RSI: **{d['RSI']:.1f}**")

        fig = buat_grafik(df, nama, kode)
        st.pyplot(fig)
        berkas = simpan_gambar(fig, fmt)
        st.download_button(f"📥 Unduh Grafik ({fmt})", berkas, f"{kode.replace('.','_')}.{fmt.lower()}", f"image/{fmt.lower()}")
        plt.close(fig)

    st.success("✅ Analisis selesai! RSI sudah aktif.")
else:
    st.info("Masukkan kode saham lalu tekan tombol di atas.")

# ---------------------- PENJELASAN RSI ----------------------
with st.expander("ℹ️ Cara Membaca Indikator RSI"):
    st.markdown("""
    **RSI (Indeks Kekuatan Relatif)** = mengukur apakah harga sudah terlalu mahal atau terlalu murah.
    - **RSI > 70** → Jenuh Beli → Harga kemungkinan turun / hati-hati beli
    - **RSI = 50** → Garis tengah → tren seimbang
    - **RSI < 30** → Jenuh Jual → Harga kemungkinan naik / peluang beli
    - **Syarat BELI**: RSI di atas 50 tapi belum sampai 70 → tren naik sehat
    - **Syarat JUAL**: RSI di bawah 50 atau sudah di atas 75 → tren melemah

    > 💡 **Sekarang sinyal BELI baru muncul jika keempat indikator sepakat sekaligus → sinyal makin sedikit tapi makin berkualitas!**
    """)
