import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# Sayfa Yapılandırması (Geniş Ekran Modu)
st.set_page_config(
    page_title="Hibrit Portföy Komuta Merkezi",
    page_icon="📈",
    layout="wide"
)

# Başlık ve Bilgi Alanı
st.title("📈 Hibrit Portföy Komuta Merkezi")
st.markdown(f"**Tarama Zamanı:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} | **Durum:** Canlı Piyasa & Risk Motoru Aktif")

# Kenar Çubuğu (Ayarlar ve Kontroller)
st.sidebar.header("⚙️ Portföy & Risk Parametreleri")
bist_kasa = st.sidebar.number_input("BIST Sanal Kasa (TL)", value=100000, step=10000)
nasdaq_kasa = st.sidebar.number_input("NASDAQ Sanal Kasa ($)", value=10000, step=1000)
risk_orani = st.sidebar.slider("İşlem Başına Risk Oranı (%)", min_value=1.0, max_value=5.0, value=2.0, step=0.5) / 100.0

# Standart Takip Listesi
default_tickers = [
    "AAPL", "MSFT", "TSLA", "NVDA", "AMZN", "META", "INTC", "AMD", 
    "THYAO.IS", "FROTO.IS", "TOASO.IS", "MGROS.IS", "BIMAS.IS", "CCOLA.IS", "TUPRS.IS", "EREGL.IS", "ASELS.IS", "GARAN.IS"
]

selected_tickers = st.sidebar.multiselect("Takip Edilecek Varlıklar", default_tickers, default=default_tickers)

# --- ARAYÜZDEN ANLIK EK HİSSE EKLEME KUTUSU ---
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Anlık Hisse Ekle")
ek_hisse_input = st.sidebar.text_input("Eklemek istediğiniz kod(lar):", placeholder="Örn: AKBNK.IS, GOOGL")

# Eğer kullanıcı arayüzden yeni kod yazdıysa listeye dahil et
if ek_hisse_input:
    eklenenler = [h.strip().upper() for h in ek_hisse_input.replace(",", " ").split() if h.strip()]
    for h in eklenenler:
        if h not in selected_tickers:
            selected_tickers.append(h)
    st.sidebar.success(f"Eklendi: {', '.join(eklenenler)}")

# Çalıştır Butonu
if st.sidebar.button("🚀 Piyasayı Tara ve Raporu Oluştur", type="primary"):
    
    with st.spinner("Piyasa verileri çekiliyor, teknik göstergeler hesaplanıyor... Lütfen bekleyin."):
        
        sonuclar = []

        for ticker in selected_tickers:
            try:
                stock = yf.Ticker(ticker)
                
                # 1. Haftalık Trend (MTF)
                df_weekly = stock.history(period="1y", interval="1wk")
                haftalik_trend_pozitif = True
                haftalik_durum = "Bilinmiyor"
                if not df_weekly.empty and len(df_weekly) >= 21:
                    df_weekly['EMA_9'] = df_weekly['Close'].ewm(span=9, adjust=False).mean()
                    df_weekly['EMA_21'] = df_weekly['Close'].ewm(span=21, adjust=False).mean()
                    haftalik_trend_pozitif = df_weekly['EMA_9'].iloc[-1] > df_weekly['EMA_21'].iloc[-1]
                    haftalik_durum = "Boğa 🟩" if haftalik_trend_pozitif else "Ayı 🟥"

                # 2. Günlük Veriler
                df_long = stock.history(period="1y")
                
                # MultiIndex koruması
                if isinstance(df_long.columns, pd.MultiIndex):
                    df_long.columns = df_long.columns.droplevel(1)
                    
                if df_long.empty or len(df_long) < 50:
                    continue
                    
                para_birimi = "TL" if ".IS" in ticker else "$"
                is_bist = ".IS" in ticker
                
                close_series = df_long['Close'].dropna()
                if close_series.empty:
                    continue
                    
                bugun_kapanis = close_series.iloc[-1]
                dun_kapanis = close_series.iloc[-2] if len(close_series) >= 2 else bugun_kapanis
                yuzde_degisim = ((bugun_kapanis - dun_kapanis) / dun_kapanis) * 100 if dun_kapanis > 0 else 0.0

                # İndikatörler
                df_long['EMA_9'] = df_long['Close'].ewm(span=9, adjust=False).mean()
                df_long['EMA_21'] = df_long['Close'].ewm(span=21, adjust=False).mean()
                df_long['SMA_200'] = df_long['Close'].rolling(window=200).mean()
                sma_200 = df_long['SMA_200'].iloc[-1] if len(df_long) >= 200 and not pd.isna(df_long['SMA_200'].iloc[-1]) else bugun_kapanis
                uzun_vade_trend = bugun_kapanis > sma_200

                delta = df_long['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = (100 - (100 / (1 + rs))).iloc[-1]
                if pd.isna(rsi): rsi = 50.0
                
                macd_serisi = df_long['Close'].ewm(span=12).mean() - df_long['Close'].ewm(span=26).mean()
                macd = macd_serisi.iloc[-1] if not macd_serisi.empty else 0
                signal = macd_serisi.ewm(span=9).mean().iloc[-1] if not macd_serisi.empty else 0

                # Bollinger
                bb_mid = df_long['Close'].rolling(window=20).mean()
                bb_std = df_long['Close'].rolling(window=20).std()
                bb_alt = (bb_mid - (bb_std * 2)).iloc[-1]
                bb_ust = (bb_mid + (bb_std * 2)).iloc[-1]
                if pd.isna(bb_alt): bb_alt = bugun_kapanis * 0.95
                if pd.isna(bb_ust): bb_ust = bugun_kapanis * 1.05

                # Hacim
                vol_sma_20 = df_long['Volume'].rolling(window=20).mean().iloc[-1] if 'Volume' in df_long else 0
                hacim_carpan = df_long['Volume'].iloc[-1] / vol_sma_20 if vol_sma_20 and vol_sma_20 > 0 else 1.0
                hacim_onay = df_long['Volume'].iloc[-1] > vol_sma_20 if vol_sma_20 else False

                # ATR & Risk
                high_low = df_long['High'] - df_long['Low']
                high_close = np.abs(df_long['High'] - df_long['Close'].shift())
                low_close = np.abs(df_long['Low'] - df_long['Close'].shift())
                atr_serisi = np.max(pd.concat([high_low, high_close, low_close], axis=1), axis=1).rolling(14).mean()
                atr = atr_serisi.iloc[-1] if not atr_serisi.empty and not pd.isna(atr_serisi.iloc[-1]) else (bugun_kapanis * 0.03)
                
                dinamik_stop = bugun_kapanis - (atr * 1.5)
                hedef_1 = bugun_kapanis + (atr * 2.0)
                hedef_2 = bugun_kapanis + (atr * 4.0)

                son_bir_ay = df_long.tail(30)
                kisa_direnc = son_bir_ay['High'].max() if not son_bir_ay.empty else bugun_kapanis * 1.05
                kisa_destek = son_bir_ay['Low'].min() if not son_bir_ay.empty else bugun_kapanis * 0.95

                # Skorlama
                skor = 50
                e9 = df_long['EMA_9'].iloc[-1]
                e21 = df_long['EMA_21'].iloc[-1]
                if e9 > e21: skor += 15
                else: skor -= 15
                if macd > signal: skor += 15
                else: skor -= 15
                if rsi >= 70: skor -= 10
                elif rsi <= 30: skor += 10
                if hacim_onay: skor += 10
                else: skor -= 10
                if bugun_kapanis < bb_alt: skor += 15 
                elif bugun_kapanis > bb_ust: skor -= 15 
                if haftalik_trend_pozitif: skor += 15
                else: skor -= 25 
                if uzun_vade_trend: skor += 15
                else: skor -= 20
                skor = max(0, min(100, skor))

                # Sinyal
                sinyal = "Nötr (İzle) ⚖️"
                if not haftalik_trend_pozitif and not uzun_vade_trend and skor < 40:
                    sinyal = "UZAK DUR! 🛑"
                elif bugun_kapanis > bb_ust and rsi >= 68:
                    sinyal = "KAR REALİZASYONU 🔴"
                elif bugun_kapanis <= bb_alt and rsi <= 35 and uzun_vade_trend:
                    sinyal = "KUSURSUZ ALIM 🟢"
                elif rsi <= 40 and uzun_vade_trend:
                    sinyal = "KADEMELİ ALIM 🔵"

                # Lot Hesap
                aktif_kasa = bist_kasa if is_bist else nasdaq_kasa
                risk_tutar = aktif_kasa * risk_orani
                hisse_risk = bugun_kapanis - dinamik_stop
                lot = int(risk_tutar / hisse_risk) if hisse_risk > 0 else 0
                maliyet = lot * bugun_kapanis

                sonuclar.append({
                    "Varlık": ticker,
                    "Fiyat": f"{bugun_kapanis:.2f} {para_birimi}",
                    "Günlük %": f"{yuzde_degisim:+.2f}%",
                    "Hacim": f"{hacim_carpan:.1f}x",
                    "Skor": f"%{skor}",
                    "Nihai Sinyal": sinyal,
                    "Haftalık Yön": haftalik_durum,
                    "200G Trend": "Boğa 🟩" if uzun_vade_trend else "Ayı 🟥",
                    "Destek / Direnç": f"D: {kisa_destek:.2f} / R: {kisa_direnc:.2f}",
                    "Dinamik Stop": f"{dinamik_stop:.2f} {para_birimi}",
                    "Hedef 1 / 2": f"{hedef_1:.2f} / {hedef_2:.2f}",
                    "Önerilen Lot": f"{lot} Adet ({maliyet:.0f} {para_birimi})"
                })
            except Exception as e:
                st.error(f"{ticker} analiz hatası: {e}")

        if sonuclar:
            df_sonuc = pd.DataFrame(sonuclar)
            st.success("Tarama başarıyla tamamlandı!")
            st.dataframe(df_sonuc, use_container_width=True)
else:
    st.info("👈 Başlamak için sol menüden varlıkları seçebilir, anlık hisse ekleyebilir ve ardından **'Piyasayı Tara'** butonuna tıklayabilirsin.")
