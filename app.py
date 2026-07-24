import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Ana sayfa ayarı
st.set_page_config(page_title="Karar Destek Sistemi", layout="wide")

# --- KULLANICI ARAYÜZÜ İSİMLENDİRMELERİ ---
TICKER_ISIMLERI = {
    "FROTO.IS": "Ford Otosan (FROTO)",
    "GC=F": "Ons Altın (Global)",
    "XU100.IS": "BIST 100 Endeksi",
    "THYAO.IS": "Türk Hava Yolları"
}

# --- SESSION STATE (Sayfa yenilenince sıfırlanmayı önlemek için) ---
if 'secili_varlik' not in st.session_state:
    st.session_state['secili_varlik'] = "FROTO.IS"

# Sekmeleri oluşturuyoruz
tab1, tab2 = st.tabs(["📊 Anlık Takip ve RSI", "⚙️ Strateji Backtesti"])

# ==========================================
# SEKME 1: ANA UYGULAMA (Fiyat ve RSI)
# ==========================================
with tab1:
    st.header("Anlık Piyasa Verileri ve Teknik Analiz")
    
    # Kullanıcı seçimi (Format func ile ekranda güzel isimleri gösteriyoruz)
    secim = st.selectbox(
        "Analiz Edilecek Varlığı Seçin", 
        options=list(TICKER_ISIMLERI.keys()), 
        format_func=lambda x: TICKER_ISIMLERI[x],
        index=list(TICKER_ISIMLERI.keys()).index(st.session_state['secili_varlik'])
    )
    st.session_state['secili_varlik'] = secim
    
    if st.button("Verileri Getir"):
        with st.spinner("Piyasa verileri çekiliyor..."):
            # Son 3 aylık veriyi çek
            df_main = yf.download(st.session_state['secili_varlik'], period="3mo")
            
            if not df_main.empty:
                # Son fiyatı ve günlük değişimi al
                son_fiyat = float(df_main['Close'].iloc[-1])
                onceki_fiyat = float(df_main['Close'].iloc[-2])
                degisim = ((son_fiyat - onceki_fiyat) / onceki_fiyat) * 100
                
                # RSI Hesaplama (14 Günlük)
                delta = df_main['Close'].diff()
                kazanc = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                kayip = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = kazanc / kayip
                df_main['RSI'] = 100 - (100 / (1 + rs))
                son_rsi = float(df_main['RSI'].iloc[-1])
                
                # Metrikleri Ekrana Bas
                colA, colB = st.columns(2)
                colA.metric(
                    label=f"Güncel Fiyat ({TICKER_ISIMLERI[st.session_state['secili_varlik']]})", 
                    value=f"{son_fiyat:.2f}", 
                    delta=f"% {degisim:.2f}"
                )
                colB.metric(
                    label="RSI (14 Günlük)", 
                    value=f"{son_rsi:.2f}",
                    delta="Aşırı Alım Bölgesi!" if son_rsi > 70 else ("Aşırı Satım Bölgesi!" if son_rsi < 30 else "Nötr"),
                    delta_color="inverse" if (son_rsi > 70 or son_rsi < 30) else "off"
                )
                
                st.subheader("Son 3 Aylık Fiyat ve RSI Trendi")
                st.line_chart(df_main[['Close']])
                st.area_chart(df_main[['RSI']])

# ==========================================
# SEKME 2: BACKTEST MOTORU
# ==========================================
with tab2:
    st.header("📈 SMA Kesişimi Backtest Motoru")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        test_ticker = st.text_input("Test Edilecek Sembol (Örn: FROTO.IS)", value="FROTO.IS")
    with col2:
        kisa_sma = st.number_input("Kısa Periyot (Gün)", value=20, step=1)
    with col3:
        uzun_sma = st.number_input("Uzun Periyot (Gün)", value=50, step=1)

    if st.button("Backtesti Başlat"):
        with st.spinner("Geçmiş veriler analiz ediliyor..."):
            df_bt = yf.download(test_ticker, period="1y")
            
            if not df_bt.empty:
                df_bt['Kisa_SMA'] = df_bt['Close'].rolling(window=kisa_sma).mean()
                df_bt['Uzun_SMA'] = df_bt['Close'].rolling(window=uzun_sma).mean()
                df_bt['Sinyal'] = np.where(df_bt['Kisa_SMA'] > df_bt['Uzun_SMA'], 1, 0)
                df_bt['Pozisyon'] = df_bt['Sinyal'].shift(1)
                df_bt['Gunluk_Getiri'] = df_bt['Close'].pct_change()
                df_bt['Strateji_Getirisi'] = df_bt['Gunluk_Getiri'] * df_bt['Pozisyon']
                df_bt['Al_Tut_Kümülatif'] = (1 + df_bt['Gunluk_Getiri']).cumprod()
                df_bt['Strateji_Kümülatif'] = (1 + df_bt['Strateji_Getirisi']).cumprod()
                
                df_bt.dropna(inplace=True)

                st.subheader(f"{test_ticker} - Geriye Dönük Performans Özeti")
                
                metrik1, metrik2 = st.columns(2)
                al_tut_son = (df_bt['Al_Tut_Kümülatif'].iloc[-1] - 1) * 100
                strateji_son = (df_bt['Strateji_Kümülatif'].iloc[-1] - 1) * 100
                
                metrik1.metric(label="Pasif Bekleme Getirisi (Al-Tut)", value=f"% {al_tut_son:.2f}")
                metrik2.metric(label="Algoritma Getirisi", value=f"% {strateji_son:.2f}")
                
                st.line_chart(df_bt[['Al_Tut_Kümülatif', 'Strateji_Kümülatif']])
