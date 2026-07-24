import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.header("📈 Strateji Backtest Motoru (SMA Kesişimi)")

# 1. Parametreleri Belirleme
col1, col2, col3 = st.columns(3)
with col1:
    ticker = st.text_input("Test Edilecek Sembol", value="FROTO.IS")
with col2:
    kisa_sma = st.number_input("Kısa Periyot (Gün)", value=20, step=1)
with col3:
    uzun_sma = st.number_input("Uzun Periyot (Gün)", value=50, step=1)

if st.button("Backtesti Başlat"):
    with st.spinner("Geçmiş veriler analiz ediliyor..."):
        # 2. Veriyi Çekme
        df = yf.download(ticker, period="1y")
        
        # 3. Strateji Hesaplamaları
        df['Kisa_SMA'] = df['Close'].rolling(window=kisa_sma).mean()
        df['Uzun_SMA'] = df['Close'].rolling(window=uzun_sma).mean()
        
        # Sinyal Üretimi: Kısa > Uzun ise 1 (Al), değilse 0 (Sat/Bekle)
        df['Sinyal'] = np.where(df['Kisa_SMA'] > df['Uzun_SMA'], 1, 0)
        
        # Sinyalin bir gün sonraki getiriyi etkilemesi için kaydırma (shift)
        df['Pozisyon'] = df['Sinyal'].shift(1)
        
        # 4. Getiri Hesaplamaları
        # Günlük standart getiri (Al ve Tut stratejisi)
        df['Gunluk_Getiri'] = df['Close'].pct_change()
        
        # Bizim stratejimizin getirisi (Sadece pozisyondayken getiri yaz)
        df['Strateji_Getirisi'] = df['Gunluk_Getiri'] * df['Pozisyon']
        
        # Kümülatif (Toplam) Getirileri Hesaplama
        df['Al_Tut_Kümülatif'] = (1 + df['Gunluk_Getiri']).cumprod()
        df['Strateji_Kümülatif'] = (1 + df['Strateji_Getirisi']).cumprod()
        
        # İlk NaN satırları temizle
        df.dropna(inplace=True)

        # 5. Sonuçları Ekrana Yazdırma
        st.subheader(f"{ticker} - Geriye Dönük Performans Özeti")
        
        # Metrik Kartları
        metrik1, metrik2 = st.columns(2)
        al_tut_son = (df['Al_Tut_Kümülatif'].iloc[-1] - 1) * 100
        strateji_son = (df['Strateji_Kümülatif'].iloc[-1] - 1) * 100
        
        metrik1.metric(label="Pasif Bekleme Getirisi (Al-Tut)", value=f"% {al_tut_son:.2f}")
        metrik2.metric(label="Algoritma Getirisi", value=f"% {strateji_son:.2f}")
        
        # 6. Performans Grafiği
        st.line_chart(df[['Al_Tut_Kümülatif', 'Strateji_Kümülatif']])
