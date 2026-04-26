
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import random
import time
import re
from scipy.signal import find_peaks
from urllib.parse import quote
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ── CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Maestro Trading",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown('''<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #0f111a; color: #f0f2f6; }
    .card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px; padding: 20px; margin: 10px 0;
    }
    .title-gradient {
        background: linear-gradient(135deg, #00ff88, #00b8ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 2rem; font-weight: 800;
    }
    .buy-card  { border-left: 4px solid #00ff88; background: rgba(0,255,136,0.05); padding: 10px; border-radius: 8px; margin: 4px 0; }
    .sell-card { border-left: 4px solid #ff3366; background: rgba(255,51,102,0.05); padding: 10px; border-radius: 8px; margin: 4px 0; }
    .wait-card { border-left: 4px solid #888; background: rgba(128,128,128,0.05); padding: 10px; border-radius: 8px; margin: 4px 0; }
    .pos-news  { color: #00ff88; font-weight: 600; }
    .neg-news  { color: #ff3366; font-weight: 600; }
    .neu-news  { color: #aaa; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>''', unsafe_allow_html=True)

# ── BROWSER HEADERS ──────────────────────────────────────────────────────
BROWSER_HEADERS = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
     "Accept-Language": "id-ID,id;q=0.9"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
     "Accept-Language": "id-ID,id;q=0.9"},
]

KATA_POSITIF = ["naik","untung","laba","profit","growth","bullish","rally","record",
                "gain","rise","up","beat","positive","optimis","tumbuh","surplus"]
KATA_NEGATIF = ["turun","rugi","loss","bearish","crash","drop","fall","down","miss",
                "negative","pesimis","bangkrut","delisting","skandal","defisit"]

# ── FUNGSI CORE ──────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def tarik_data(ticker, period="6mo"):
    ticker = ticker.strip().upper()
    is_jk = ticker.endswith('.JK')
    for attempt in range(3):
        try:
            df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
            if not df.empty:
                break
            time.sleep(random.uniform(0.3, 0.7))
        except Exception:
            time.sleep(0.5)
    if df.empty: return None, None, 1.0
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df = df.reset_index()
    if "Datetime" in df.columns: df.rename(columns={"Datetime": "Date"}, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()
    kurs = 1.0
    if not is_jk:
        try:
            kr = yf.download("IDR=X", period="5d", progress=False, auto_adjust=True)
            if isinstance(kr.columns, pd.MultiIndex): kr.columns = kr.columns.get_level_values(0)
            kurs = float(kr["Close"].dropna().iloc[-1])
            if kurs < 1000: kurs = 16200.0
        except Exception: kurs = 16200.0
        for col in ['Open','High','Low','Close']: df[col] = df[col] * kurs
    for col in ['Open','High','Low','Close']:
        df[col+"_IDR"] = pd.to_numeric(df[col], errors="coerce")
    if "Volume" not in df.columns: df["Volume"] = 0.0
    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0)
    df["Support"]    = df["Low_IDR"].rolling(20).min().shift(1)
    df["Resistance"] = df["High_IDR"].rolling(20).max().shift(1)
    vol_mean = df["Volume"].rolling(20).mean()
    df["Vol_Spike"]   = df["Volume"] > (vol_mean * 1.5)
    df["Is_Up"]       = df["Close_IDR"] > df["Open_IDR"]
    df["Bandarmologi"] = df.apply(lambda r: "[+] AKUMULASI" if r["Vol_Spike"] and r["Is_Up"]
                                 else ("[-] DISTRIBUSI" if r["Vol_Spike"] and not r["Is_Up"]
                                 else "[ ] Netral"), axis=1)
    return df.dropna(subset=["Close_IDR"]), is_jk, kurs


@st.cache_data(ttl=3600)
def hitung_siklus(df):
    close = df["Close_IDR"].values
    dates = pd.to_datetime(df["Date"].values)
    prom  = (close.max() - close.min()) * 0.02
    peaks,   _ = find_peaks(close,  prominence=prom, distance=5)
    valleys, _ = find_peaks(-close, prominence=prom, distance=5)
    def get_cycle(idxs):
        if len(idxs) < 2: return None, None
        gaps = [(dates[idxs[i+1]] - dates[idxs[i]]).days for i in range(len(idxs)-1)]
        avg  = int(np.mean(gaps))
        ds   = (dates[-1] - dates[idxs[-1]]).days
        dtn  = avg - (ds % avg)
        nxt  = dates[-1] + pd.Timedelta(days=int(dtn))
        return avg, nxt
    ap, np_ = get_cycle(peaks)
    av, nv  = get_cycle(valleys)
    return ap, np_, av, nv, peaks, valleys


@st.cache_data(ttl=3600)
def ambil_fundamental(ticker):
    try:
        info = yf.Ticker(ticker).info
        return {
            "PER":    info.get("trailingPE"),
            "PBV":    info.get("priceToBook"),
            "ROE":    info.get("returnOnEquity"),
            "Margin": info.get("profitMargins"),
            "DE":     info.get("debtToEquity"),
            "Beta":   info.get("beta"),
            "Div":    info.get("dividendYield"),
            "Nama":   info.get("longName", ticker),
            "Sektor": info.get("sector", "--"),
        }
    except Exception: return {}


def hitung_skor(fund):
    s = 0
    per = fund.get("PER")
    if per and per > 0: s += 25 if per<10 else (20 if per<15 else (14 if per<20 else (8 if per<25 else 2)))
    else: s += 10
    pbv = fund.get("PBV")
    if pbv and pbv > 0: s += 20 if pbv<1 else (15 if pbv<2 else (10 if pbv<3 else 4))
    else: s += 8
    roe = fund.get("ROE")
    if roe: s += 25 if roe*100>=25 else (20 if roe*100>=15 else (12 if roe*100>=10 else 5))
    else: s += 8
    m = fund.get("Margin")
    if m: s += 15 if m*100>=20 else (10 if m*100>=10 else (5 if m*100>=5 else 0))
    else: s += 5
    de = fund.get("DE")
    if de is not None: s += 15 if de<30 else (10 if de<60 else (5 if de<100 else 0))
    else: s += 5
    return min(s, 100)


@st.cache_data(ttl=900)
def ambil_berita(ticker):
    semua = []
    query = ticker.replace(".JK","").replace("-USD","").replace("=X","")
    try:
        q   = quote(f"{query} saham investasi")
        url = f"https://news.google.com/rss/search?q={q}&hl=id&gl=ID&ceid=ID:id"
        h   = random.choice(BROWSER_HEADERS)
        r   = requests.get(url, headers=h, timeout=8)
        if r.status_code == 200:
            soup  = BeautifulSoup(r.text, "lxml-xml")
            items = soup.find_all("item")
            for item in items[:6]:
                t = item.find("title")
                d = item.find("pubDate")
                if t: semua.append({"judul": t.text.strip()[:120], "tgl": d.text[:10] if d else ""})
    except Exception: pass
    if len(semua) < 3:
        try:
            news = yf.Ticker(ticker).news or []
            for item in news[:5]:
                c = item.get("content", {})
                t = c.get("title","") if isinstance(c, dict) else item.get("title","")
                if t: semua.append({"judul": t[:120], "tgl": ""})
        except Exception: pass
    return semua


def sentimen(judul):
    j = judul.lower()
    p = sum(1 for k in KATA_POSITIF if k in j)
    n = sum(1 for k in KATA_NEGATIF if k in j)
    if p > n: return "pos", "[+] POSITIF"
    elif n > p: return "neg", "[-] NEGATIF"
    return "neu", "[=] NETRAL"


def buat_jadwal_30hari(np_, nv, ap, av):
    jadwal = []
    today  = pd.Timestamp.now().normalize()
    end    = today + pd.Timedelta(days=30)
    if np_ and ap:
        t = pd.Timestamp(np_)
        while t <= end:
            jadwal.append({"tgl": t, "type": "peak"})
            t += pd.Timedelta(days=ap)
    if nv and av:
        t = pd.Timestamp(nv)
        while t <= end:
            jadwal.append({"tgl": t, "type": "valley"})
            t += pd.Timedelta(days=av)
    return sorted(jadwal, key=lambda x: x["tgl"])


# ── HEADER APP ────────────────────────────────────────────────────────────
st.markdown('<div class="title-gradient">MAESTRO Trading Intelligence</div>', unsafe_allow_html=True)
st.caption("Sistem Kuantitatif v3.0 | Time-Cycle | Bandarmologi | Berita Indonesia | Plan 1 Bulan")

# ── SIDEBAR ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Pusat Kendali")
    mode = st.radio("Mode Operasi", [
        "Analisis 1 Aset",
        "Screener Saham IDX",
        "Screener Crypto",
        "Screener Forex",
    ])
    st.divider()
    st.caption("Maestro v3.0 | Data: yfinance + Web")

# ======================================================================
# MODE 1: ANALISIS 1 ASET
# ======================================================================
if mode == "Analisis 1 Aset":
    with st.sidebar:
        ticker  = st.text_input("Kode Aset", "BBCA.JK",
                                help="Contoh: BBCA.JK, BTC-USD, EURUSD=X, AAPL").upper().strip()
        periode = st.selectbox("Periode Data", ["3mo","6mo","1y","2y"], index=2)
        run_btn = st.button("Analisis Sekarang", use_container_width=True, type="primary")

    if run_btn:
        with st.spinner(f"Menganalisis {ticker}..."):
            df, is_jk, kurs = tarik_data(ticker, periode)

        if df is None or df.empty:
            st.error(f"Gagal mengambil data untuk {ticker}. Periksa kode ticker.")
        else:
            harga  = float(df["Close_IDR"].iloc[-1])
            harga0 = float(df["Close_IDR"].iloc[-2]) if len(df) > 1 else harga
            pct    = (harga - harga0) / max(harga0, 1) * 100
            sup    = float(df["Support"].dropna().iloc[-1]) if not df["Support"].dropna().empty else harga * 0.95
            res    = float(df["Resistance"].dropna().iloc[-1]) if not df["Resistance"].dropna().empty else harga * 1.05
            bandar = df["Bandarmologi"].iloc[-1]
            fund   = ambil_fundamental(ticker)
            skor   = hitung_skor(fund)
            ap, np_, av, nv, peaks, valleys = hitung_siklus(df)

            # --- METRIK ATAS ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Harga", f"Rp {harga:,.0f}", f"{'+' if pct>=0 else ''}{pct:.2f}%")
            c2.metric("Skor Fundamental", f"{skor}/100")
            c3.metric("Bandarmologi", bandar.split()[0])
            c4.metric("1 Lot" if is_jk else "1 Unit",
                      f"Rp {harga*100:,.0f}" if is_jk else f"Rp {harga:,.0f}")

            # --- GRAFIK INTERAKTIF ---
            st.markdown("---")
            st.subheader("Chart Interaktif (TradingView Style)")
            fig = make_subplots(rows=2, cols=1, row_heights=[0.75, 0.25],
                                shared_xaxes=True, vertical_spacing=0.04)
            fig.add_trace(go.Scatter(
                x=list(df["Date"])+list(df["Date"][::-1]),
                y=list(df["Support"])+list(df["Support"]*0.97),
                fill="toself", fillcolor="rgba(0,255,136,0.08)",
                line=dict(color="rgba(0,0,0,0)"), name="Zona Beli"), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=list(df["Date"])+list(df["Date"][::-1]),
                y=list(df["Resistance"]*1.03)+list(df["Resistance"]),
                fill="toself", fillcolor="rgba(255,51,102,0.08)",
                line=dict(color="rgba(0,0,0,0)"), name="Zona Jual"), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Close_IDR"], mode="lines",
                line=dict(color="#4FC3F7", width=2.5),
                name=ticker), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Support"], mode="lines",
                line=dict(color="#00E676", width=1, dash="dot"), name="Support"), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Resistance"], mode="lines",
                line=dict(color="#FF5252", width=1, dash="dot"), name="Resistance"), row=1, col=1)
            if len(peaks): fig.add_trace(go.Scatter(
                x=df["Date"].iloc[peaks], y=df["Close_IDR"].iloc[peaks], mode="markers",
                marker=dict(symbol="triangle-down", color="#FF5252", size=10),
                name="Puncak"), row=1, col=1)
            if len(valleys): fig.add_trace(go.Scatter(
                x=df["Date"].iloc[valleys], y=df["Close_IDR"].iloc[valleys], mode="markers",
                marker=dict(symbol="triangle-up", color="#00E676", size=10),
                name="Lembah"), row=1, col=1)
            cv = ["#00E676" if df["Close_IDR"].iloc[i]>=df["Open_IDR"].iloc[i] else "#FF5252"
                  for i in range(len(df))]
            fig.add_trace(go.Bar(
                x=df["Date"], y=df["Volume"], marker_color=cv, name="Volume"), row=2, col=1)
            fig.update_layout(template="plotly_dark", height=600,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              hovermode="x unified", dragmode="pan",
                              xaxis_rangeslider_visible=False,
                              yaxis=dict(tickprefix="Rp ", tickformat=",.0f", side="right"),
                              margin=dict(l=10, r=80, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

            # --- 3 KOLOM: PLAN + FUNDAMENTAL + JADWAL ---
            col_a, col_b, col_c = st.columns(3)

            with col_a:
                st.markdown("**Trading Plan Eksekusi**")
                st.markdown(f'<div class="buy-card">BELI IDEAL<br>Rp {sup:,.0f} - Rp {sup*1.02:,.0f}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="buy-card">BUY BREAKOUT<br>Tembus Rp {res*1.01:,.0f}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="sell-card">TAKE PROFIT<br>Rp {res*0.98:,.0f}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="sell-card">CUT LOSS<br>Rp {sup*0.96:,.0f}</div>', unsafe_allow_html=True)

            with col_b:
                st.markdown("**Fundamental**")
                per = fund.get("PER")
                pbv = fund.get("PBV")
                roe = fund.get("ROE")
                div = fund.get("Div")
                st.write(f"PER: {f'{per:.1f}x' if per else '--'} | PBV: {f'{pbv:.2f}x' if pbv else '--'}")
                st.write(f"ROE: {f'{roe*100:.1f}%' if roe else '--'} | Div: {f'{div*100:.2f}%' if div else '--'}")
                st.write(f"Siklus Puncak : {ap or 'N/A'} hari")
                st.write(f"Siklus Lembah : {av or 'N/A'} hari")
                st.write(f"Skor Maestro  : {skor}/100")

            with col_c:
                st.markdown("**Jadwal 7 Hari")
                today = pd.Timestamp.now().normalize()
                hari_id = {"Monday":"Sen","Tuesday":"Sel","Wednesday":"Rab",
                           "Thursday":"Kam","Friday":"Jum","Saturday":"Sab","Sunday":"Min"}
                for i in range(1, 8):
                    h = today + pd.Timedelta(days=i)
                    nm = hari_id.get(h.strftime('%A'), h.strftime('%a'))
                    lbl = h.strftime(f'{nm} %d %b')
                    if nv and h == pd.Timestamp(nv).normalize():
                        st.markdown(f'<div class="buy-card">{lbl}: BELI (Prediksi Lembah)</div>', unsafe_allow_html=True)
                    elif np_ and h == pd.Timestamp(np_).normalize():
                        st.markdown(f'<div class="sell-card">{lbl}: JUAL (Prediksi Puncak)</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="wait-card">{lbl}: Wait & See</div>', unsafe_allow_html=True)

            # --- PLAN 1 BULAN ---
            st.markdown("---")
            st.subheader("Plan Trading 1 Bulan Ke Depan (Berbasis Siklus Data)")
            jadwal = buat_jadwal_30hari(np_, nv, ap, av)
            if not jadwal:
                st.info("Data siklus belum cukup. Coba gunakan periode 2y.")
            else:
                rows = []
                hari_id2 = {"Monday":"Senin","Tuesday":"Selasa","Wednesday":"Rabu",
                            "Thursday":"Kamis","Friday":"Jumat","Saturday":"Sabtu","Sunday":"Minggu"}
                for j in jadwal:
                    tipe  = "LEMBAH - BELI" if j["type"]=="valley" else "PUNCAK - JUAL"
                    harga_t = f"Rp {sup:,.0f}" if j["type"]=="valley" else f"Rp {res:,.0f}"
                    nm    = hari_id2.get(j["tgl"].strftime('%A'), "")
                    rows.append({"Tanggal": j["tgl"].strftime('%d %b %Y'),
                                 "Hari": nm, "Event": tipe, "Target Harga": harga_t})
                df_jadwal = pd.DataFrame(rows)
                st.dataframe(df_jadwal, use_container_width=True, hide_index=True)

            # --- BERITA & SENTIMEN ---
            st.markdown("---")
            st.subheader("Berita & Sentimen Terkini")
            with st.spinner("Mengakses berita Indonesia..."):
                berita = ambil_berita(ticker)
            if not berita:
                st.info("Berita tidak tersedia saat ini.")
            else:
                n_pos = n_neg = 0
                for b in berita:
                    label, txt = sentimen(b["judul"])
                    css = "pos-news" if label=="pos" else ("neg-news" if label=="neg" else "neu-news")
                    st.markdown(f'<span class="{css}">{txt}</span> {b["judul"]}', unsafe_allow_html=True)
                    if label=="pos": n_pos += 1
                    elif label=="neg": n_neg += 1
                overall = "BULLISH" if n_pos > n_neg else ("BEARISH" if n_neg > n_pos else "NETRAL")
                st.info(f"Sentimen Keseluruhan: {overall} ({n_pos} positif, {n_neg} negatif)")

# ======================================================================
# MODE 2: SCREENER SAHAM IDX
# ======================================================================
elif mode == "Screener Saham IDX":
    with st.sidebar:
        budget = st.number_input("Budget (Rp)", 10000, 100_000_000, 500_000, 50_000)
        run_btn = st.button("Scan LQ45", use_container_width=True, type="primary")

    st.subheader("Screener Saham IDX")
    LQ45 = [# ── BLUECHIP / LQ45 ──────────────────────────────────────────────
            "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK",
            "ASII.JK", "GOTO.JK", "AMMN.JK", "BREN.JK", "BRIS.JK",
            "UNVR.JK", "ICBP.JK", "PGAS.JK", "PTBA.JK", "ADRO.JK",
            "TPIA.JK", "MEDC.JK", "BRPT.JK", "KLBF.JK", "AKRA.JK",
            "AMRT.JK", "ESSA.JK", "HRUM.JK", "ITMG.JK", "MDKA.JK",
            "PGEO.JK", "SIDO.JK", "SRTG.JK", "BUKA.JK", "CPIN.JK",
            "EXCL.JK", "INDF.JK", "INKP.JK", "INTP.JK", "ISAT.JK",
            "MBMA.JK", "MTEL.JK", "MYOR.JK", "SMGR.JK", "TOWR.JK",
            "ARTO.JK", "SCMA.JK", "EMTK.JK", "ACES.JK", "INCO.JK",

            # ── PERBANKAN & KEUANGAN ─────────────────────────────────────────
            "BTPS.JK", "BJTM.JK", "BJBR.JK", "BNGA.JK", "BNLI.JK",
            "BDMN.JK", "BKSW.JK", "NISP.JK", "MEGA.JK", "AGRO.JK",
            "BBYB.JK", "BNBA.JK", "BMAS.JK", "DNAR.JK", "NAGA.JK",
            "NOBU.JK", "PNBS.JK", "RELI.JK", "SDRA.JK", "BANK.JK",

            # ── ASURANSI & MULTIFINANCE ──────────────────────────────────────
            "WOMF.JK", "BFIN.JK", "MFIN.JK", "VRNA.JK", "TRIM.JK",
            "PANS.JK", "ABMM.JK", "ADMF.JK", "CFIN.JK", "IMJS.JK",

            # ── TEKNOLOGI & DIGITAL ──────────────────────────────────────────
            "DMMX.JK", "FREN.JK", "LUCK.JK", "MIKA.JK", "MTDL.JK",
            "MLPT.JK", "ATIC.JK", "EDGE.JK", "MSTI.JK", "MSIN.JK",
            "AWAN.JK", "KOTA.JK", "AXIO.JK", "SONA.JK", "JADI.JK",

            # ── CONSUMER GOODS & RETAIL ──────────────────────────────────────
            "GGRM.JK", "HMSP.JK", "INDF.JK", "MAPI.JK", "RALS.JK",
            "HERO.JK", "MIDI.JK", "CSAP.JK", "ARGO.JK", "SSTM.JK",
            "AISA.JK", "CAMP.JK", "CEKA.JK", "DLTA.JK", "FOOD.JK",
            "GOOD.JK", "HOKI.JK", "KEJU.JK", "SKBM.JK", "ULTJ.JK",
            "BOBA.JK", "ALTO.JK", "TBLA.JK", "BUDI.JK", "MGNA.JK",

            # ── KESEHATAN & FARMASI ──────────────────────────────────────────
            "KAEF.JK", "MERK.JK", "PYFA.JK", "SIDO.JK", "TSPC.JK",
            "DVLA.JK", "INAF.JK", "HEAL.JK", "MIKA.JK", "SILO.JK",
            "PRDA.JK", "SAME.JK", "BMHS.JK", "OMED.JK", "RSGK.JK",

            # ── PROPERTI & KONSTRUKSI ────────────────────────────────────────
            "BSDE.JK", "CTRA.JK", "LPKR.JK", "PWON.JK", "SMRA.JK",
            "APLN.JK", "ARMY.JK", "ASRI.JK", "BKSL.JK", "CAKK.JK",
            "DILD.JK", "ELTY.JK", "FORZ.JK", "GMTD.JK", "GPRA.JK",
            "JRPT.JK", "KIJA.JK", "LPCK.JK", "MDLN.JK", "MKPI.JK",
            "MTLA.JK", "MMLP.JK", "NIRO.JK", "PLIN.JK", "PPRO.JK",
            "RDTX.JK", "RODA.JK", "SMDM.JK", "TARA.JK", "WIKA.JK",
            "WSKT.JK", "ADHI.JK", "PTPP.JK", "TOTL.JK", "ACST.JK",

            # ── ENERGI & PERTAMBANGAN ────────────────────────────────────────
            "ANTM.JK", "ITMG.JK", "BUMI.JK", "ENRG.JK", "DEWA.JK",
            "GEMS.JK", "KKGI.JK", "MYOH.JK", "PKPK.JK", "SMMT.JK",
            "TOBA.JK", "DOID.JK", "BOSS.JK", "MBAP.JK", "FIRE.JK",
            "GTBO.JK", "APEX.JK", "SMRU.JK", "ELSA.JK", "RUIS.JK",
            "ARTI.JK", "BIPI.JK", "LSIP.JK", "SIMP.JK", "TAPG.JK",

            # ── MINYAK SAWIT & AGRIBISNIS ────────────────────────────────────
            "AALI.JK", "BWPT.JK", "DSNG.JK", "GZCO.JK", "JAWA.JK",
            "PALM.JK", "SGRO.JK", "SMAR.JK", "SSMS.JK", "TGRA.JK",
            "MAGP.JK", "ANJT.JK", "BNRS.JK", "GOLL.JK", "INDO.JK",

            # ── INFRASTRUKTUR & UTILITAS ─────────────────────────────────────
            "JSMR.JK", "WTON.JK", "WEGE.JK", "META.JK", "TBIG.JK",
            "SUPR.JK", "KPIG.JK", "IPCC.JK", "TLKM.JK", "IPCM.JK",
            "BIRD.JK", "BLTZ.JK", "GIAA.JK", "NELY.JK", "SAFE.JK",

            # ── MANUFAKTUR & INDUSTRI ────────────────────────────────────────
            "AUTO.JK", "GJTL.JK", "INDS.JK", "NIPS.JK", "PRAS.JK",
            "SMSM.JK", "ADMG.JK", "IMAS.JK", "LPIN.JK", "MASA.JK",
            "SRIL.JK", "RICY.JK", "POLY.JK", "ERTX.JK", "ARGO.JK",
            "BATA.JK", "IKBI.JK", "KBLM.JK", "SCCO.JK", "VOKS.JK",
            "ALKA.JK", "ALMI.JK", "BTON.JK", "GDST.JK", "ISSP.JK",
            "JKSW.JK", "KRAS.JK", "LION.JK", "TBMS.JK", "ZINC.JK",

            # ── SEMEN & MATERIAL ─────────────────────────────────────────────
            "SMBR.JK", "JECC.JK", "ARNA.JK", "MARK.JK", "MLIA.JK",
            "TOTO.JK", "KIAS.JK", "AMFG.JK", "CANGK.JK","IFII.JK",

            # ── HIDDEN GEM — KAPITALISASI KECIL-MENENGAH ────────────────────
            "OILS.JK", "ANDI.JK", "CUAN.JK", "PNLF.JK", "LPGI.JK",
            "YELO.JK", "UCID.JK", "UFOE.JK", "MSKY.JK", "VICI.JK",
            "SWAT.JK", "GAMA.JK", "LABA.JK", "BHAT.JK", "BPTR.JK",
            "RCCC.JK", "MNCN.JK", "KBLV.JK", "PBSA.JK", "HATM.JK",
            "MABA.JK", "GRIA.JK", "BPII.JK", "HILL.JK", "TGUK.JK",
            "PMMP.JK", "DMAS.JK", "URBN.JK", "NASI.JK", "RAFI.JK",

            # ── MEDIA & ENTERTAINMENT ────────────────────────────────────────
            "FILM.JK", "IPTV.JK", "KREN.JK", "LINK.JK", "MDIA.JK",
            "MSIN.JK", "NFCX.JK", "CENT.JK", "ABBA.JK", "RIMO.JK",
            "SIMA.JK", "SRNA.JK", "VIVA.JK", "VINS.JK", "VRNA.JK",
            "SCMA.JK", "EMTK.JK", "ARTO.JK", "SONA.JK", "JADI.JK",
        ]
    if run_btn:
        hasil = []
        bar   = st.progress(0)
        for i, tk in enumerate(LQ45):
            df, is_jk, kurs = tarik_data(tk, "3mo")
            if df is not None and not df.empty:
                h = float(df["Close_IDR"].iloc[-1])
                lot = h * 100 if is_jk else h
                if lot <= budget:
                    f  = ambil_fundamental(tk)
                    sk = hitung_skor(f)
                    sup = float(df["Support"].dropna().iloc[-1]) if not df["Support"].dropna().empty else h*0.95
                    hasil.append({"Ticker": tk, "Nama": (f.get("Nama") or tk)[:25],
                                  "Harga": h, "Min Beli": lot, "Skor": sk,
                                  "Support": sup, "Sektor": f.get("Sektor","--")})
            bar.progress((i+1)/len(LQ45))
        if hasil:
            df_h = pd.DataFrame(hasil).sort_values("Skor", ascending=False).reset_index(drop=True)
            df_h.index += 1
            st.dataframe(df_h.style.format({"Harga":"Rp {:,.0f}","Min Beli":"Rp {:,.0f}",
                                             "Support":"Rp {:,.0f}","Skor":"{:.0f}"}),
                         use_container_width=True)
        else:
            st.warning(f"Tidak ada saham yang lolos budget Rp {budget:,.0f}.")

# ======================================================================
# MODE 3: SCREENER CRYPTO
# ======================================================================
elif mode == "Screener Crypto":
    with st.sidebar:
        budget = st.number_input("Budget (Rp)", 10000, 100_000_000, 1_000_000, 100_000)
        run_btn = st.button("Scan Crypto", use_container_width=True, type="primary")

    st.subheader("Screener Cryptocurrency")
    CRYPTO = [# ── LARGE CAP ───────────────────────────────────────
            "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD",
            "ADA-USD", "AVAX-USD", "DOGE-USD", "TRX-USD", "TON-USD",
            # ── MID CAP POPULER ─────────────────────────────────
            "LINK-USD", "DOT-USD", "MATIC-USD", "LTC-USD", "ATOM-USD",
            "UNI-USD", "NEAR-USD", "APT-USD", "OP-USD", "ARB-USD",
            "IMX-USD", "INJ-USD", "SUI-USD", "SEI-USD", "JUP-USD",
            # ── HIDDEN GEM POTENSIAL ─────────────────────────────
            "FET-USD", "RENDER-USD", "WLD-USD", "ONDO-USD", "PENDLE-USD",
            "STRK-USD", "PYTH-USD", "JTO-USD", "ETHFI-USD", "EIGEN-USD",
            "MANTA-USD", "ALT-USD", "PORTAL-USD", "PIXEL-USD", "SAFE-USD",
            # ── DEFI & UTILITY ──────────────────────────────────
            "AAVE-USD", "MKR-USD", "CRV-USD", "LDO-USD", "RPL-USD",
            "SNX-USD", "BAL-USD", "COMP-USD", "SUSHI-USD", "1INCH-USD",
            # ── KOMODITAS CRYPTO ────────────────────────────────
            "PAXG-USD", "GOLD-USD", "SILVER-USD", "OIL-USD", "COPPER-USD",]
    if run_btn:
        hasil = []
        bar   = st.progress(0)
        for i, tk in enumerate(CRYPTO):
            df, _, kurs = tarik_data(tk, "3mo")
            if df is not None and not df.empty:
                h = float(df["Close_IDR"].iloc[-1])
                if h <= budget:
                    hasil.append({"Ticker": tk, "Harga (Rp)": h,
                                  "Jumlah dg Budget": f"{budget/h:.4f} unit"})
            bar.progress((i+1)/len(CRYPTO))
        if hasil:
            df_h = pd.DataFrame(hasil).sort_values("Harga (Rp)").reset_index(drop=True)
            df_h.index += 1
            st.dataframe(df_h.style.format({"Harga (Rp)":"Rp {:,.2f}"}),
                         use_container_width=True)
        else:
            st.warning(f"Semua crypto melebihi budget Rp {budget:,.0f}.")

# ======================================================================
# MODE 4: SCREENER FOREX
# ======================================================================
elif mode == "Screener Forex":
    with st.sidebar:
        budget = st.number_input("Budget (Rp)", 10000, 100_000_000, 2_000_000, 500_000)
        run_btn = st.button("Scan Forex", use_container_width=True, type="primary")

    st.subheader("Screener Forex & Komoditas")
    FOREX = [# ── MAJOR PAIRS ─────────────────────────────────────
            "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCHF=X",
            "USDCAD=X", "NZDUSD=X", "EURGBP=X", "EURJPY=X", "GBPJPY=X",
            # ── ASIAN & EM PAIRS ────────────────────────────────
            "USDIDR=X", "USDSGD=X", "USDMYR=X", "USDTHB=X", "USDPHP=X",
            "USDCNY=X", "USDINR=X", "USDKRW=X", "USDVND=X", "USDBRL=X",
            # ── KOMODITAS ───────────────────────────────────────
            "XAUUSD=X",  # Emas
            "XAGUSD=X",  # Perak
            "XPTUSD=X",  # Platinum
            "XPDUSD=X",  # Palladium
            # ── KOMODITAS VIA ETF/FUTURES YFINANCE ──────────────
            "CL=F",      # Crude Oil WTI
            "BZ=F",      # Brent Crude Oil
            "GC=F",      # Gold Futures
            "SI=F",      # Silver Futures
            "HG=F",      # Copper Futures
            "NG=F",      # Natural Gas
            "ZC=F",      # Corn Futures
            "ZW=F",      # Wheat Futures
            "ZS=F",      # Soybean Futures
            "KC=F",      # Coffee Futures
            "CC=F",      # Cocoa Futures
            "SB=F",      # Sugar Futures
            "CT=F",      # Cotton Futures
            "OJ=F",      # Orange Juice Futures]
    if run_btn:
        hasil = []
        bar   = st.progress(0)
        for i, tk in enumerate(FOREX):
            df, _, kurs = tarik_data(tk, "3mo")
            if df is not None and not df.empty:
                h = float(df["Close_IDR"].iloc[-1])
                hasil.append({"Pasangan": tk, "Harga (Rp)": h,
                               "Budget Cukup?": "[v] Ya" if h <= budget else "[x] Tidak"})
            bar.progress((i+1)/len(FOREX))
        if hasil:
            df_h = pd.DataFrame(hasil).reset_index(drop=True)
            df_h.index += 1
            st.dataframe(df_h.style.format({"Harga (Rp)":"Rp {:,.2f}"}),
                         use_container_width=True)
