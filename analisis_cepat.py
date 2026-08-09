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
st.info("💡 Akhiri dengan .JK untuk saham Indonesia (contoh: BUMI.JK)")

# ✅ Nilai bawaan: BUMI, DEWA, BNBR — TETAP BISA DIUBAH DI KOLOM DI BAWAH
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
    df['Sinyal'] = df['MACD'].ewm(span=p3, adjust=False).mean()
    df['Hist'] = df['MACD'] - df['Sinyal']
    return df

def ambil_data(kode):
    """Ambil data 30 menit — cari sampai cukup batang atau maksimal 30 hari"""
    for hari in [10, 15, 20, 30]:
        try:
            df = yf.download(kode, period=f"{hari}d", interval="30m", progress=False)
            if not df.empty:
                jumlah = len(df)
                st.info(f"📥 Data diterima: **{jumlah} batang 30 menit** (dari {hari} hari terakhir)")
                if jumlah >= 35:
                    return df
        except Exception:
            continue
    return pd.DataFrame()

def sinyal_trading(df):
    minimal = 35
    if len(df) < minimal:
        return "🔄 Data Kurang", [f"Perlu minimal {minimal} batang, saat ini hanya {len(df)}. Coba saat pasar aktif (Senin–Jumat)."], None
    
    d = df.iloc[-1]
    sma_vol = df['Volume'].rolling(20).mean().iloc[-1]
    alasan = []
    sinyal = "🔄 TUNGGU"
    
    try:
        if d['MACD'] > d['Sinyal'] and d['Close'] > d['SMA'] and d['Volume'] > sma_vol:
            sinyal = "✅ BELI"
            alasan = ["MACD di atas Garis Sinyal", "Harga di atas Rata-rata (SMA 20)", "Volume lebih tinggi dari rata-rata"]
        elif d['MACD'] < d['Sinyal'] and d['Close'] < d['SMA']:
            sinyal = "❌ JUAL"
            alasan = ["MACD di bawah Garis Sinyal", "Harga di bawah Rata-rata (SMA 20)"]
        else:
            alasan = ["Belum memenuhi syarat pasti BELI maupun JUAL"]
    except Exception:
        alasan = ["Indikator belum terbentuk sempurna, tunggu data berikutnya"]
    
    return sinyal, alasan, d

def buat_grafik(df, nama, kode):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 9), sharex=True,
                                         gridspec_kw={'height_ratios': [3, 2, 1]})
    ax1.plot(df.index, df['Close'], 'b-', linewidth=1.5, label='Harga Tutup')
    ax1.plot(df.index, df['SMA'], 'orange', linewidth=1.5, label='SMA 20')
    ax1.set_title(f"{nama} ({kode}) | Kerangka Waktu 30 Menit", fontweight='bold')
    ax1.set_ylabel("Harga"); ax1.legend(loc='upper left'); ax1.grid(alpha=0.3)

    ax2.plot(df.index, df['MACD'], 'g-', label='MACD')
    ax2.plot(df.index, df['Sinyal'], 'r-', label='Garis Sinyal')
    warna = ['g' if h >= 0 else 'r' for h in df['Hist']]
    ax2.bar(df.index, df['Hist'], color=warna, alpha=0.3, width=0.02)
    ax2.set_ylabel("MACD"); ax2.legend(loc='upper left'); ax2.grid(alpha=0.3)

    ax3.bar(df.index, df['Volume'], color='gray', alpha=0.5, width=0.02, label='Volume')
    ax3.plot(df.index, df['Volume'].rolling(20).mean(), 'purple', label='Rata-rata Volume')
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

        df = hitung_sma(df)
        df = hitung_macd(df)
        sinyal, alasan, d = sinyal_trading(df)

        st.subheader(f"Keputusan: {sinyal}")
        for a in alasan: st.write(f"- {a}")
        
        if d is not None:
            st.write(f"Harga Terakhir: **{d['Close']:,.2f}** | SMA 20: **{d['SMA']:,.2f}** | MACD: **{d['MACD']:.4f}** | Sinyal: **{d['Sinyal']:.4f}**")

        fig = buat_grafik(df, nama, kode)
        st.pyplot(fig)
        berkas = simpan_gambar(fig, fmt)
        st.download_button(f"📥 Unduh Grafik ({fmt})", berkas, f"{kode.replace('.','_')}.{fmt.lower()}", f"image/{fmt.lower()}")
        plt.close(fig)

    st.success("✅ Analisis selesai!")
else:
    st.info("Masukkan kode saham lalu tekan tombol di atas.")

# ---------------------- CATATAN PENTING ----------------------
with st.expander("ℹ️ Keterangan Penggunaan"):
    st.markdown("""
    - **Nilai bawaan**: Emiten 1 = BUMI.JK | Emiten 2 = DEWA.JK | Emiten 3 = BNBR.JK
    - **Bisa diganti kapan saja**: Langsung ketik kode lain di kolom input (contoh ganti menjadi: `TLKM.JK`, `ASII.JK`, dst)
    - **Waktu terbaik**: Tekan tombol saat **pasar buka — Senin–Jumat 09.00–16.00 WIB**
    - **Akhir pekan/libur**: Data terbatas dan indikator belum dapat dihitung
    - **Format gambar**: Pilih PNG atau JPEG lalu unduh grafik lengkap
    """)
