import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import os

# --- DOSYA TABANLI KALICI HAFIZA FONKSİYONLARI ---
TICKER_DOSYASI = "custom_tickers.txt"
PORTFOY_DOSYASI = "user_portfolio.csv"

def dosyadan_ticker_oku():
    if os.path.exists(TICKER_DOSYASI):
        with open(TICKER_DOSYASI, "r", encoding="utf-8") as f:
            t_list = [line.strip().upper() for line in f if line.strip()]
            if t_list:
                return t_list
    varsayilan = ["AAPL", "MSFT", "TSLA", "NVDA", "THYAO.IS", "FROTO.IS", "TOASO.IS"]
    dosyaya_ticker_yaz(varsayilan)
    return varsayilan

def dosyaya_ticker_yaz(t_list):
    with open(TICKER_DOSYASI, "w", encoding="utf-8") as f:
        for t in t_list:
            f.write(f"{t}\n")

def portfoy_dosyasindan_oku():
    if os.path.exists(PORTFOY_DOSYASI):
        try:
            return pd.read_csv(PORTFOY_DOSYASI)
        except:
            pass
    return pd.DataFrame(columns=["Varlık", "Adet", "Maliyet"])

def portfoy_dosyasina_yaz(df):
    df.to_csv(PORTFOY_DOSYASI, index=False)

# --- SESSİON STATE (HAFIZA) BAŞLATMA ---
if "tarama_durumu" not in st.session_state:
    st.session_state.tarama_durumu = False
if "sonuclar" not in st.session_state:
    st.session_state.sonuclar = []
if "ham_veriler" not in st.session_state:
    st.session_state.ham_veriler = {}
if "boga_sayisi" not in st.session_state:
    st.session_state.boga_sayisi = 0
if "alim_firsati" not in st.session_state:
    st.session_state.alim_firsati = 0

if "custom_tickers" not in st.session_state:
    st.session_state.custom_tickers = dosyadan_ticker_oku()

if "user_portfolio_df" not in st.session_state:
    st.session_state.user_portfolio_df = portfoy_dosyasindan_oku()

# --- 1. SAYFA YAPILANDIRMASI VE STİL ---
st.set_page_config(
    page_title="Hibrit Portföy Komuta Merkezi",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
    .kpi-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #333;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    .kpi-title { font-size: 13px; color: #AAAAAA; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-value { font-size: 26px; font-weight: bold; color: #FFFFFF; margin-top: 5px; }
    .kpi-subtext { font-size: 11px; color: #777777; margin-top: 4px; }
    .kpi-highlight-green { color: #00FF88; }
    .kpi-highlight-fire { color: #FF5555; }
    .action-box {
        background-color: #262626;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #00FF88;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 Hibrit Portföy Komuta Merkezi & Akıllı Rehber")
st.markdown(f"**Tarama Zamanı:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} | **Durum:** Canlı Piyasa & Portföy Motoru Aktif")
st.markdown("---")

# --- 2. KENAR ÇUBUĞU (AKORDEON YAPISI) ---
st.sidebar.header("⚙️ Kontrol Paneli")

with st.sidebar.expander("💰 Kasa and Risk Parametreleri", expanded=False):
    bist_kasa = st.number_input("BIST Sanal Kasa (TL)", value=100000, step=10000)
    nasdaq_kasa = st.number_input("NASDAQ Sanal Kasa ($)", value=10000, step=1000)
    risk_orani = st.slider("İşlem Başına Risk Oranı (%)", min_value=1.0, max_value=5.0, value=2.0, step=0.5) / 100.0

# --- HİSSE EKLEME CALLBACK FONKSİYONU ---
def hisse_ekle_callback():
    input_degeri = st.session_state.get("ek_hisse_input_field", "")
    if input_degeri.strip():
        eklenenler = [h.strip().upper() for h in input_degeri.replace(",", " ").split() if h.strip()]
        yeni_eklendi = False
        for h in eklenenler:
            if h not in st.session_state.custom_tickers:
                st.session_state.custom_tickers.append(h)
                yeni_eklendi = True
        
        if yeni_eklendi:
            dosyaya_ticker_yaz(st.session_state.custom_tickers)
            st.sidebar.success(f"Kalıcı olarak eklendi: {', '.join(eklenenler)}")
        
        st.session_state["ek_hisse_input_field"] = ""

with st.sidebar.expander("📋 Varlık Seçimi ve Profiller", expanded=True):
    preset_options = {
        "Kendi Seçimim (Standart)": st.session_state.custom_tickers,
        "BIST 30 (Ana Hisseler)": [
            "THYAO.IS", "GARAN.IS", "AKBNK.IS", "ISCTR.IS", "YKBNK.IS", 
            "EREGL.IS", "KRDMD.IS", "PETKM.IS", "TUPRS.IS", "FROTO.IS", 
            "TOASO.IS", "ARCLK.IS", "BIMAS.IS", "MGROS.IS", "SOKM.IS", 
            "ASELS.IS", "ENKAI.IS", "SISE.IS", "KCHOL.IS", "SAHOL.IS"
        ],
        "BIST 100 (Genişletilmiş Seçki)": [
            "THYAO.IS", "GARAN.IS", "AKBNK.IS", "ISCTR.IS", "YKBNK.IS", 
            "EREGL.IS", "KRDMD.IS", "PETKM.IS", "TUPRS.IS", "FROTO.IS", 
            "TOASO.IS", "ARCLK.IS", "BIMAS.IS", "MGROS.IS", "SOKM.IS", 
            "ASELS.IS", "ENKAI.IS", "SISE.IS", "KCHOL.IS", "SAHOL.IS",
            "PGSUS.IS", "ODAS.IS", "OYAKC.IS", "SASA.IS", 
            "HEKTS.IS", "KONTR.IS", "ASTOR.IS", "EUPWR.IS", "ALARK.IS"
        ],
        "ABD En Bilindik / Teknoloji (US)": [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", 
            "AMD", "INTC", "NFLX", "ADBE", "PYPL", "QCOM", "AMAT", "BA"
        ],
        "Küresel Emtialar (Ons Altın Dahil)": ["GC=F", "SLV", "CPER", "PALL", "BZ=F"]
    }

    secilen_kategori = st.selectbox("Hızlı Tarama Profili", list(preset_options.keys()))
    default_tickers = preset_options[secilen_kategori]
    
    selected_tickers = st.multiselect("Takip Edilecek Varlıklar", default_tickers, default=default_tickers)

    st.text_input(
        "Eklemek istediğiniz kod(lar):", 
        placeholder="Örn: KCHOL.IS, INTC", 
        key="ek_hisse_input_field", 
        on_change=hisse_ekle_callback
    )

# --- GERÇEK PORTFÖY TANIMLAMA ---
with st.sidebar.expander("💼 Gerçek Portföyüm (Varlıklarım)", expanded=True):
    st.markdown("Elindeki varlıkları ekle, sistem sana özel yol haritası çıkarsın:")
    
    p_varlik = st.text_input("Varlık Adı", placeholder="Örn: FROTO.IS veya AAPL")
    p_adet = st.number_input("Adet / Lot", min_value=1, value=100, step=1)
    p_maliyet = st.number_input("Ortalama Maliyet", min_value=0.0, value=100.0, step=1.0)
    
    if st.button("Portföye Ekle / Güncelle"):
        if p_varlik.strip():
            temiz_p = p_varlik.strip().upper()
            df_p = st.session_state.user_portfolio_df
            if temiz_p in df_p["Varlık"].values:
                df_p.loc[df_p["Varlık"] == temiz_p, ["Adet", "Maliyet"]] = [p_adet, p_maliyet]
            else:
                yeni_satir = pd.DataFrame([{"Varlık": temiz_p, "Adet": p_adet, "Maliyet": p_maliyet}])
                df_p = pd.concat([df_p, yeni_satir], ignore_index=True)
            
            st.session_state.user_portfolio_df = df_p
            portfoy_dosyasina_yaz(df_p)
            st.success(f"{temiz_p} portföye kaydedildi!")

    if not st.session_state.user_portfolio_df.empty:
        st.markdown("**Kayıtlı Varlıkların:**")
        st.dataframe(st.session_state.user_portfolio_df, use_container_width=True, hide_index=True)
        if st.button("Portföyü Temizle"):
            st.session_state.user_portfolio_df = pd.DataFrame(columns=["Varlık", "Adet", "Maliyet"])
            portfoy_dosyasina_yaz(st.session_state.user_portfolio_df)
            st.rerun()

st.sidebar.markdown("---")
tarama_tetiklendi = st.sidebar.button("🚀 Piyasayı Tara ve Raporu Oluştur", type="primary", use_container_width=True)

# --- 3. ANA TARAMA MOTORU ---
if tarama_tetiklendi:
    with st.spinner("Piyasa ve endeks verileri taranıyor, göstergeler hesaplanıyor..."):
        gecici_sonuclar = []
        gecici_ham_veriler = {}
        boga_sayisi = 0
        alim_firsati = 0

        if not st.session_state.user_portfolio_df.empty:
            portfoy_hisseleri = st.session_state.user_portfolio_df["Varlık"].tolist()
            for ph in portfoy_hisseleri:
                if ph not in selected_tickers:
                    selected_tickers.append(ph)

        try:
            bist_df = yf.Ticker("XU100.IS").history(period="1mo")
            bist_getiri = ((bist_df['Close'].iloc[-1] - bist_df['Close'].iloc[0]) / bist_df['Close'].iloc[0]) * 100 if not bist_df.empty else 0
            
            nasdaq_df = yf.Ticker("^IXIC").history(period="1mo")
            nasdaq_getiri = ((nasdaq_df['Close'].iloc[-1] - nasdaq_df['Close'].iloc[0]) / nasdaq_df['Close'].iloc[0]) * 100 if not nasdaq_df.empty else 0
        except:
            bist_getiri, nasdaq_getiri = 0, 0

        for ticker in selected_tickers:
            try:
                stock = yf.Ticker(ticker)
                
                df_weekly = stock.history(period="1y", interval="1wk")
                haftalik_trend_pozitif = True
                haftalik_durum = "Bilinmiyor"
                if not df_weekly.empty and len(df_weekly) >= 21:
                    df_weekly['EMA_9'] = df_weekly['Close'].ewm(span=9, adjust=False).mean()
                    df_weekly['EMA_21'] = df_weekly['Close'].ewm(span=21, adjust=False).mean()
                    haftalik_trend_pozitif = df_weekly['EMA_9'].iloc[-1] > df_weekly['EMA_21'].iloc[-1]
                    haftalik_durum = "Boğa 🟩" if haftalik_trend_pozitif else "Ayı 🟥"

                df_long = stock.history(period="1y")
                
                if isinstance(df_long.columns, pd.MultiIndex):
                    df_long.columns = df_long.columns.droplevel(1)
                    
                if df_long.empty or len(df_long) < 50:
                    continue
                    
                para_birimi = "TL" if ".IS" in ticker else "$"
                is_bist = ".IS" in ticker
                is_emtia = ticker in ["GC=F", "SLV", "CPER", "PALL", "BZ=F"]
                
                close_series = df_long['Close'].dropna()
                if close_series.empty:
                    continue
                    
                bugun_kapanis = close_series.iloc[-1]
                dun_kapanis = close_series.iloc[-2] if len(close_series) >= 2 else bugun_kapanis
                
                try:
                    onceki_kapanis = stock.info.get('regularMarketPreviousClose', dun_kapanis)
                    if not onceki_kapanis or pd.isna(onceki_kapanis):
                        onceki_kapanis = dun_kapanis
                except:
                    onceki_kapanis = dun_kapanis

                yuzde_degisim = ((bugun_kapanis - onceki_kapanis) / onceki_kapanis) * 100 if onceki_kapanis > 0 else 0.0

                son_1_ay_df = df_long.tail(21)
                hisse_1m_getiri = ((son_1_ay_df['Close'].iloc[-1] - son_1_ay_df['Close'].iloc[0]) / son_1_ay_df['Close'].iloc[0]) * 100 if not son_1_ay_df.empty else 0
                
                if is_bist:
                    goreceli_guc = hisse_1m_getiri - bist_getiri
                    karsilastirma = "BIST"
                elif is_emtia:
                    goreceli_guc = hisse_1m_getiri
                    karsilastirma = "Kendi"
                else:
                    goreceli_guc = hisse_1m_getiri - nasdaq_getiri
                    karsilastirma = "NASDAQ"

                df_long['EMA_9'] = df_long['Close'].ewm(span=9, adjust=False).mean()
                df_long['EMA_21'] = df_long['Close'].ewm(span=21, adjust=False).mean()
                df_long['SMA_200'] = df_long['Close'].rolling(window=200).mean()
                sma_200 = df_long['SMA_200'].iloc[-1] if len(df_long) >= 200 and not pd.isna(df_long['SMA_200'].iloc[-1]) else bugun_kapanis
                uzun_vade_trend = bugun_kapanis > sma_200

                delta = df_long['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df_long['RSI'] = 100 - (100 / (1 + rs))
                rsi = df_long['RSI'].iloc[-1]
                if pd.isna(rsi): rsi = 50.0
                
                gecici_ham_veriler[ticker] = df_long[['Close', 'Volume', 'RSI', 'EMA_9', 'EMA_21']].copy()
                
                macd_serisi = df_long['Close'].ewm(span=12).mean() - df_long['Close'].ewm(span=26).mean()
                macd = macd_serisi.iloc[-1] if not macd_serisi.empty else 0
                signal_val = macd_serisi.ewm(span=9).mean().iloc[-1] if not macd_serisi.empty else 0

                bb_mid = df_long['Close'].rolling(window=20).mean()
                bb_std = df_long['Close'].rolling(window=20).std()
                bb_alt = (bb_mid - (bb_std * 2)).iloc[-1]
                bb_ust = (bb_mid + (bb_std * 2)).iloc[-1]
                if pd.isna(bb_alt): bb_alt = bugun_kapanis * 0.95
                if pd.isna(bb_ust): bb_ust = bugun_kapanis * 1.05

                vol_sma_20 = df_long['Volume'].rolling(window=20).mean().iloc[-1] if 'Volume' in df_long else 0
                hacim_carpan = df_long['Volume'].iloc[-1] / vol_sma_20 if vol_sma_20 and vol_sma_20 > 0 else 1.0

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

                skor = 50
                e9 = df_long['EMA_9'].iloc[-1]
                e21 = df_long['EMA_21'].iloc[-1]
                if e9 > e21: skor += 15
                else: skor -= 15
                if macd > signal_val: skor += 15
                else: skor -= 15
                if rsi >= 70: skor -= 10
                elif rsi <= 30: skor += 10
                if bugun_kapanis < bb_alt: skor += 15 
                elif bugun_kapanis > bb_ust: skor -= 15 
                if haftalik_trend_pozitif: skor += 15
                else: skor -= 25 
                if uzun_vade_trend: skor += 15
                else: skor -= 20
                if goreceli_guc > 0: skor += 10
                elif goreceli_guc < -5: skor -= 10
                skor = max(0, min(100, skor))

                sinyal = "Nötr (İzle) ⚖️"
                if not haftalik_trend_pozitif and not uzun_vade_trend and skor < 40:
                    sinyal = "UZAK DUR! 🛑"
                elif bugun_kapanis > bb_ust and rsi >= 68:
                    sinyal = "KAR REALİZASYONU 🔴"
                elif bugun_kapanis <= bb_alt and rsi <= 35 and uzun_vade_trend:
                    sinyal = "KUSURSUZ ALIM 🟢"
                    alim_firsati += 1
                elif rsi <= 40 and uzun_vade_trend:
                    sinyal = "KADEMELİ ALIM 🔵"
                    alim_firsati += 1
                
                if uzun_vade_trend:
                    boga_sayisi += 1

                gorunen_ad = "Ons Altın (GC=F)" if ticker == "GC=F" else ticker
                aktif_kasa = bist_kasa if is_bist else nasdaq_kasa
                risk_tutar = aktif_kasa * risk_orani
                hisse_risk = bugun_kapanis - dinamik_stop
                lot = int(risk_tutar / hisse_risk) if hisse_risk > 0 else 0
                maliyet_hesabi = lot * bugun_kapanis

                gecici_sonuclar.append({
                    "Varlık": gorunen_ad,
                    "RawTicker": ticker,
                    "Fiyat": f"{bugun_kapanis:.2f} {para_birimi}",
                    "RawFiyat": bugun_kapanis,
                    "ParaBirimi": para_birimi,
                    "Günlük %": f"{yuzde_degisim:+.2f}%",
                    "Görec. Güç (1A)": f"{'+' if goreceli_guc > 0 else ''}{goreceli_guc:.2f}% ({karsilastirma})",
                    "Hacim": f"{hacim_carpan:.1f}x",
                    "Skor": f"%{skor}",
                    "Nihai Sinyal": sinyal,
                    "Haftalık Yön": haftalik_durum,
                    "200G Trend": "Boğa 🟩" if uzun_vade_trend else "Ayı 🟥",
                    "Destek / Direnç": f"D: {kisa_destek:.2f} / R: {kisa_direnc:.2f}",
                    "Dinamik Stop": f"{dinamik_stop:.2f} {para_birimi}",
                    "RawStop": dinamik_stop,
                    "Hedef 1 / 2": f"{hedef_1:.2f} / {hedef_2:.2f}",
                    "Önerilen Lot": f"{lot} Adet ({maliyet_hesabi:.0f} {para_birimi})"
                })
            except Exception as e:
                pass

        st.session_state.sonuclar = gecici_sonuclar
        st.session_state.ham_veriler = gecici_ham_veriler
        st.session_state.boga_sayisi = boga_sayisi
        st.session_state.alim_firsati = alim_firsati
        st.session_state.tarama_durumu = True

# --- 4. ARAYÜZÜ ÇİZ ---
if st.session_state.tarama_durumu and st.session_state.sonuclar:
    
    user_p_df = st.session_state.user_portfolio_df
    if not user_p_df.empty:
        st.subheader("🎯 Size Özel Portföy Yol Haritası ve Öneriler")
        
        tarama_dict = {s["RawTicker"]: s for s in st.session_state.sonuclar}
        toplam_portfoy_degeri = 0
        
        for index, row in user_p_df.iterrows():
            v_adi = row["Varlık"]
            v_adet = row["Adet"]
            v_maliyet = row["Maliyet"]
            
            if v_adi in tarama_dict:
                item = tarama_dict[v_adi]
                anlik_fiyat = item["RawFiyat"]
                p_birimi = item["ParaBirimi"]
                anlik_deger = v_adet * anlik_fiyat
                toplam_portfoy_degeri += anlik_deger
                
                # Hata veren yer düzeltildi (kar_zarar_yuzde)
                kar_zarar_yuzde = ((anlik_fiyat - v_maliyet) / v_maliyet) * 100 if v_maliyet > 0 else 0
                
                sinyal_metni = item["Nihai Sinyal"]
                stop_seviyesi = item["RawStop"]
                
                aksiyon_tipi = "Nötr / Takipte Kal ⚖️"
                renk_kodu = "#3498db"
                tavsiye = "Mevcut trendde pozisyonunuzu koruyabilirsiniz."
                
                if "KAR REALİZASYONU" in sinyal_metni or anlik_fiyat >= stop_seviyesi * 1.35 and kar_zarar_yuzde > 20:
                    aksiyon_tipi = "Kar Realizasyonu Önerilir 🔴"
                    renk_kodu = "#e74c3c"
                    tavsiye = f"Varlık direnç bölgesinde ve aşırı alımda (%{kar_zarar_yuzde:.1f} karda). Pozisyonun bir kısmını nakde çevirebilirsiniz."
                elif anlik_fiyat <= stop_seviyesi:
                    aksiyon_tipi = "ACİL STOP / ZARAR KES 🛑"
                    renk_kodu = "#c0392b"
                    tavsiye = f"Fiyat kritik dinamik stop seviyesinin ({stop_seviyesi:.2f} {p_birimi}) altına sarktı. Sermayenizi korumak için gözden geçirin."
                elif "KUSURSUZ ALIM" in sinyal_metni or "KADEMELİ ALIM" in sinyal_metni:
                    aksiyon_tipi = "Maliyet Düşürme / Ekleme Fırsatı 🔵"
                    renk_kodu = "#2ecc71"
                    tavsiye = f"Zaten portföyünüzde olan bu varlık şu an dip/destek bölgesinde. Kademeli alım ile ortalamanızı iyileştirebilirsiniz."

                st.markdown(f"""
                <div style="background-color: #1E1E1E; padding: 15px; border-radius: 8px; border-left: 5px solid {renk_kodu}; margin-bottom: 10px;">
                    <b>{v_adi}</b> | Adet: {v_adet} | Maliyet: {v_maliyet} {p_birimi} | Güncel Fiyat: {anlik_fiyat:.2f} {p_birimi} (<b>%{kar_zarar_yuzde:+.1f}</b>)<br>
                    <b>Stratejik Durum:</b> <span style="color:{renk_kodu};">{aksiyon_tipi}</span><br>
                    <span style="color: #AAAAAA; font-size: 13px;">💡 <b>Yol Haritası:</b> {tavsiye}</span>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown(f"**Toplam Portföy Piyasa Değeri Özeti:** ~{toplam_portfoy_degeri:,.2f} (Hesaplanan varlıklar üzerinden)")
        st.markdown("---")

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Taranan Varlık</div>
            <div class="kpi-value">{len(st.session_state.sonuclar)}</div>
            <div class="kpi-subtext">Aktif Takip Listesi</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Boğa Trendinde (200G)</div>
            <div class="kpi-value kpi-highlight-green">{st.session_state.boga_sayisi}</div>
            <div class="kpi-subtext">Uzun Vade Güçlü Yapı</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Alım Fırsatları</div>
            <div class="kpi-value kpi-highlight-fire">{"🔥 " + str(st.session_state.alim_firsati) if st.session_state.alim_firsati > 0 else "0"}</div>
            <div class="kpi-subtext">Kusursuz / Kademeli Sinyaller</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    df_sonuc = pd.DataFrame(st.session_state.sonuclar)
    
    sadece_alim = st.checkbox("🎯 Sadece Alım Fırsatlarını Göster (Kusursuz / Kademeli Sinyaller)", value=False)
    
    if sadece_alim and not df_sonuc.empty:
        df_sonuc = df_sonuc[df_sonuc['Nihai Sinyal'].str.contains("KUSURSUZ ALIM|KADEMELİ ALIM", case=False, na=False)]
    
    if df_sonuc.empty:
        st.warning("Seçtiğiniz kriterlere uygun alım fırsatı bulunamadı.")
    else:
        gosterge_df = df_sonuc.drop(columns=["RawTicker", "RawFiyat", "ParaBirimi", "RawStop"], errors='ignore')

        def color_dataframe(row):
            color = ''
            if '🟢' in str(row['Nihai Sinyal']) or '🔵' in str(row['Nihai Sinyal']):
                color = 'background-color: rgba(39, 174, 96, 0.15)'
            elif '🛑' in str(row['Nihai Sinyal']) or '🔴' in str(row['Nihai Sinyal']):
                color = 'background-color: rgba(192, 57, 43, 0.15)'
            return [color] * len(row)

        styled_df = gosterge_df.style.apply(color_dataframe, axis=1)
        st.dataframe(styled_df, use_container_width=True)
        
        st.markdown("---")
        
        st.subheader("📊 Varlık Detay Analizi")
        
        secili_grafik = st.selectbox("Grafiğini incelemek istediğiniz varlığı seçin:", [s["Varlık"] for s in st.session_state.sonuclar])
        
        aktif_ticker_anahtari = "GC=F" if "Ons Altın" in secili_grafik else secili_grafik
        
        if aktif_ticker_anahtari in st.session_state.ham_veriler:
            grafik_verisi = st.session_state.ham_veriler[aktif_ticker_anahtari]
            
            tab1, tab2, tab3 = st.tabs(["📉 Fiyat Hareketi (1 Yıl)", "📊 İşlem Hacmi", "⚡ RSI (Göreceli Güç Endeksi)"])
            
            with tab1:
                st.line_chart(
                    grafik_verisi[['Close', 'EMA_9', 'EMA_21']], 
                    use_container_width=True, 
                    color=["#00FF88", "#FF5555", "#FFB300"]
                )
                st.caption("🟢 Fiyat | 🔴 EMA-9 (Kısa Vade) | 🟠 EMA-21 (Orta Vade)")
                
            with tab2:
                st.bar_chart(grafik_verisi['Volume'], use_container_width=True, color="#3498db")
                
            with tab3:
                temiz_rsi = grafik_verisi['RSI'].dropna()
                st.line_chart(temiz_rsi, use_container_width=True, color="#FF5555")
                st.caption("RSI 70 Üzeri: Aşırı Alım | RSI 30 Altı: Aşırı Satım")

elif not st.session_state.tarama_durumu:
    st.info("👈 Başlamak için sol menüden kontrol panelini düzenleyebilir, kendi varlıklarınızı portföye ekleyebilir ve **'Piyasayı Tara'** butonuna tıklayabilirsiniz.")
