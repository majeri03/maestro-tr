
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests, random, time, re, os
from scipy.signal import find_peaks
from urllib.parse import quote
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ══════════════════════════════════════════════════════════════════════
# CONFIG & TEMA
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Maestro Trading Intelligence",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;600&display=swap');

:root {
    --bg:       #080c12;
    --bg2:      #0d1420;
    --bg3:      #111a2b;
    --border:   rgba(0,180,255,0.12);
    --accent:   #00c8ff;
    --green:    #00ff9d;
    --red:      #ff3d6e;
    --gold:     #ffd166;
    --text:     #e8edf5;
    --muted:    #5a6a82;
    --card-bg:  rgba(13,20,32,0.85);
}

* { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace;
    background: var(--bg) !important;
    color: var(--text);
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 2px; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * { font-family: 'JetBrains Mono', monospace !important; }

/* ── MAIN HEADER ── */
.maestro-header {
    display: flex; align-items: center; gap: 16px;
    padding: 28px 0 20px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
}
.maestro-logo {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, var(--accent), var(--green));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem; font-weight: 800; color: #080c12;
}
.maestro-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem; font-weight: 800;
    background: linear-gradient(90deg, var(--accent), var(--green));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    line-height: 1;
}
.maestro-sub { font-size: 0.72rem; color: var(--muted); margin-top: 3px; letter-spacing: 0.08em; }

/* ── METRIC CARDS ── */
.metric-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 20px; }
.metric-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px 18px;
    position: relative; overflow: hidden;
}
.metric-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--accent), transparent);
}
.metric-label { font-size: 0.65rem; color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 6px; }
.metric-value { font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 700; line-height: 1; }
.metric-delta { font-size: 0.72rem; margin-top: 4px; }
.metric-up   { color: var(--green); }
.metric-dn   { color: var(--red); }
.metric-neu  { color: var(--gold); }

/* ── SECTION HEADER ── */
.sec-header {
    font-family: 'Syne', sans-serif;
    font-size: 0.75rem; font-weight: 700;
    letter-spacing: 0.15em; text-transform: uppercase;
    color: var(--accent); margin: 28px 0 12px;
    display: flex; align-items: center; gap: 8px;
}
.sec-header::after {
    content: ''; flex: 1; height: 1px;
    background: var(--border);
}

/* ── PANEL ── */
.panel {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px;
}

/* ── TRADING PLAN CARDS ── */
.tp-card {
    border-radius: 10px; padding: 12px 16px;
    margin-bottom: 8px; font-size: 0.82rem;
    display: flex; justify-content: space-between; align-items: center;
}
.tp-buy  { background: rgba(0,255,157,0.07); border: 1px solid rgba(0,255,157,0.25); }
.tp-sell { background: rgba(255,61,110,0.07); border: 1px solid rgba(255,61,110,0.25); }
.tp-wait { background: rgba(255,209,102,0.05); border: 1px solid rgba(255,209,102,0.15); }
.tp-label { font-size: 0.65rem; letter-spacing: 0.1em; text-transform: uppercase; }
.tp-label-buy  { color: var(--green); }
.tp-label-sell { color: var(--red); }
.tp-label-wait { color: var(--gold); }
.tp-val { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1.0rem; }

/* ── SCHEDULE ROWS ── */
.sched-row {
    display: flex; align-items: center; gap: 12px;
    padding: 9px 12px; border-radius: 8px;
    margin-bottom: 6px; font-size: 0.78rem;
    border: 1px solid transparent;
}
.sched-day  { color: var(--muted); width: 90px; flex-shrink: 0; font-size: 0.7rem; }
.sched-buy  { background: rgba(0,255,157,0.06); border-color: rgba(0,255,157,0.2); }
.sched-sell { background: rgba(255,61,110,0.06); border-color: rgba(255,61,110,0.2); }
.sched-wait { background: rgba(255,255,255,0.02); border-color: transparent; }
.badge {
    font-size: 0.6rem; letter-spacing: 0.08em; padding: 2px 8px;
    border-radius: 20px; font-weight: 700; flex-shrink: 0;
}
.badge-buy  { background: rgba(0,255,157,0.15); color: var(--green); }
.badge-sell { background: rgba(255,61,110,0.15); color: var(--red); }
.badge-wait { background: rgba(255,255,255,0.06); color: var(--muted); }

/* ── FUNDAMENTAL GRID ── */
.fund-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.fund-row {
    display: flex; justify-content: space-between;
    padding: 8px 12px; background: rgba(255,255,255,0.03);
    border-radius: 8px; font-size: 0.78rem; border: 1px solid var(--border);
}
.fund-key { color: var(--muted); }
.fund-val { font-weight: 600; }
.fund-ok  { color: var(--green); }
.fund-mid { color: var(--gold); }
.fund-bad { color: var(--red); }

/* ── SKOR RING ── */
.skor-wrap { display: flex; align-items: center; gap: 16px; padding: 16px 0; }
.skor-ring {
    width: 80px; height: 80px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 800;
    flex-shrink: 0;
}
.skor-ok  { background: conic-gradient(var(--green) 0%, rgba(0,255,157,0.1) 0%); border: 3px solid var(--green); color: var(--green); }
.skor-mid { border: 3px solid var(--gold); color: var(--gold); }
.skor-bad { border: 3px solid var(--red);  color: var(--red); }

/* ── NEWS ── */
.news-item {
    padding: 10px 14px; border-radius: 8px; margin-bottom: 6px;
    font-size: 0.78rem; border-left: 3px solid;
}
.news-pos { border-color: var(--green); background: rgba(0,255,157,0.04); }
.news-neg { border-color: var(--red);   background: rgba(255,61,110,0.04); }
.news-neu { border-color: var(--muted); background: rgba(255,255,255,0.02); }
.news-badge { font-size: 0.6rem; font-weight: 700; letter-spacing: 0.08em; }
.news-src  { font-size: 0.65rem; color: var(--muted); margin-top: 3px; }

/* ── PLAN TABLE ── */
.plan-row {
    display: grid; grid-template-columns: 100px 80px 1fr 120px;
    gap: 12px; padding: 10px 14px; border-radius: 8px; margin-bottom: 4px;
    font-size: 0.78rem; align-items: center;
}
.plan-row-buy  { background: rgba(0,255,157,0.05); border: 1px solid rgba(0,255,157,0.15); }
.plan-row-sell { background: rgba(255,61,110,0.05); border: 1px solid rgba(255,61,110,0.15); }
.plan-header {
    display: grid; grid-template-columns: 100px 80px 1fr 120px;
    gap: 12px; padding: 6px 14px; margin-bottom: 8px;
    font-size: 0.62rem; color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase;
}

/* ── BANDARMOLOGI ── */
.bandar-card {
    border-radius: 10px; padding: 14px 18px;
    display: flex; align-items: center; gap: 14px;
}
.bandar-akum { background: rgba(0,255,157,0.08); border: 1px solid rgba(0,255,157,0.3); }
.bandar-dist { background: rgba(255,61,110,0.08); border: 1px solid rgba(255,61,110,0.3); }
.bandar-neu  { background: rgba(255,255,255,0.03); border: 1px solid var(--border); }
.bandar-dot  { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; }

/* ── SCREENER TABLE ── */
[data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden; }

/* ── SIDEBAR ITEMS ── */
.stRadio label { font-size: 0.8rem !important; }
.stTextInput input, .stSelectbox select {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stButton button {
    background: linear-gradient(135deg, var(--accent), var(--green)) !important;
    color: #080c12 !important; font-weight: 700 !important;
    border: none !important; border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    letter-spacing: 0.05em !important;
}
.stButton button:hover { opacity: 0.88 !important; }

/* ── HIDE STREAMLIT CHROME ── */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# KONSTANTA
# ══════════════════════════════════════════════════════════════════════
BROWSER_HEADERS = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
     "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.3 Safari/605.1.15",
     "Accept-Language": "id-ID,id;q=0.9"},
]
KATA_POSITIF = [
    # Bahasa Indonesia — Pergerakan & Kinerja
    "naik","untung","laba","profit","surplus","tumbuh","meningkat","menguat","melesat",
    "melompat","meroket","rebound","recover","bangkit","pulih","ekspansi","berkembang",
    "solid","kuat","optimis","prospek cerah","positif","harapan","peluang","potensi",
    "efisien","produktif","inovatif","bertumbuh","perbaikan","pemulihan","apresiasi",
    # Aksi Korporasi
    "dividen","buyback","akuisisi","merger","spin-off","rights issue","stock split",
    "ekspansi bisnis","kontrak baru","proyek baru","kemitraan","kolaborasi","investasi",
    # Pasar & Teknikal
    "bullish","breakout","all time high","ath","golden cross","uptrend","rally",
    "volume tinggi","akumulasi","demand tinggi","buy signal","oversold","support kuat",
    # Bahasa Inggris — Umum
    "gain","rise","up","beat","record","growth","outperform","upgrade","strong",
    "exceed","positive","boom","surge","jump","climb","advance","improve","recovery",
    "momentum","robust","resilient","optimistic","buy","accumulate","recommend",
]

KATA_NEGATIF = [
    # Bahasa Indonesia — Pergerakan & Kinerja
    "turun","rugi","loss","melemah","merosot","anjlok","tertekan","jatuh","ambles",
    "terpuruk","stagnan","koreksi","penurunan","kemerosotan","gagal","kerugian",
    "defisit","minus","negatif","pesimis","khawatir","risiko","ancaman","tekanan",
    "lesap","terkikis","menyusut","memburuk","tergelincir","tumbang","kolaps",
    # Aksi Korporasi & Hukum
    "bangkrut","pailit","delisting","suspensi","pembekuan","likuidasi","restrukturisasi",
    "gugatan","sanksi","denda","korupsi","skandal","fraud","manipulasi","penggelapan",
    "suap","investigasi","penyidikan","pemeriksaan","pelanggaran","sengketa","tuntutan",
    # Makro & Industri
    "resesi","inflasi tinggi","stagflasi","krisis","gejolak","ketidakpastian","volatile",
    "perang","konflik","lockdown","pandemi","bencana","banjir","gempa","gangguan",
    # Pasar & Teknikal
    "bearish","downtrend","death cross","breakdown","resistance kuat","overbought",
    "sell signal","distribusi","supply tinggi","panic selling","margin call","short",
    # Bahasa Inggris — Umum
    "drop","fall","down","miss","negative","weak","crash","plunge","decline","tumble",
    "underperform","downgrade","sell","loss","deficit","bankruptcy","default","risk",
    "warning","concern","pressure","volatile","uncertainty","layoff","cut","revision",
]

HARI_ID = {"Monday":"Senin","Tuesday":"Selasa","Wednesday":"Rabu",
           "Thursday":"Kamis","Friday":"Jumat","Saturday":"Sabtu","Sunday":"Minggu"}

# ══════════════════════════════════════════════════════════════════════
# FUNGSI DATA
# ══════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=600)
def tarik_data(ticker, period="1y"):
    ticker = ticker.strip().upper()
    is_jk  = ticker.endswith(".JK")
    df = None
    for _ in range(3):
        try:
            df = yf.download(ticker, period=period, interval="1d",
                             progress=False, auto_adjust=True)
            if not df.empty: break
            time.sleep(random.uniform(0.3, 0.7))
        except Exception:
            time.sleep(0.5)
    if df is None or df.empty:
        return None, None, 1.0
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
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
        for c in ["Open","High","Low","Close"]: df[c] = pd.to_numeric(df[c], errors="coerce") * kurs
    else:
        for c in ["Open","High","Low","Close"]: df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["Open","High","Low","Close"]: df[f"{c}_IDR"] = df[c]
    if "Volume" not in df.columns: df["Volume"] = 0.0
    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0)
    df = df.dropna(subset=["Close_IDR"]).sort_values("Date").reset_index(drop=True)
    df["Support"]    = df["Low_IDR"].rolling(20).min().shift(1)
    df["Resistance"] = df["High_IDR"].rolling(20).max().shift(1)
    vm = df["Volume"].rolling(20).mean()
    df["Vol_Spike"] = df["Volume"] > (vm * 1.5)
    df["Is_Up"]     = df["Close_IDR"] > df["Open_IDR"]
    df["Bandar"]    = df.apply(lambda r:
        "AKUMULASI" if r["Vol_Spike"] and r["Is_Up"] else
        ("DISTRIBUSI" if r["Vol_Spike"] and not r["Is_Up"] else "NETRAL"), axis=1)
    # ATR
    h = df["High_IDR"]; l = df["Low_IDR"]; c = df["Close_IDR"]; cp = c.shift(1)
    tr = pd.concat([h-l, (h-cp).abs(), (l-cp).abs()], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()
    return df, is_jk, kurs


@st.cache_data(ttl=3600)
def hitung_siklus(df):
    close = df["Close_IDR"].values
    dates = pd.to_datetime(df["Date"].values)
    pr    = close.max() - close.min()
    if pr == 0: pr = close.mean() * 0.1
    prom  = pr * 0.02
    peaks,   _ = find_peaks(close,  prominence=prom, distance=5)
    valleys, _ = find_peaks(-close, prominence=prom, distance=5)
    def get_cyc(idxs):
        if len(idxs) < 2: return None, None
        gaps = [(dates[idxs[i+1]] - dates[idxs[i]]).days for i in range(len(idxs)-1)]
        avg  = int(np.mean(gaps))
        ds   = (dates[-1] - dates[idxs[-1]]).days
        dtn  = avg - (ds % avg)
        nxt  = dates[-1] + pd.Timedelta(days=int(dtn))
        return avg, nxt
    ap, np_ = get_cyc(peaks)
    av, nv  = get_cyc(valleys)
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
            "EPS":    info.get("trailingEps"),
            "52H":    info.get("fiftyTwoWeekHigh"),
            "52L":    info.get("fiftyTwoWeekLow"),
            "MCap":   info.get("marketCap"),
            "Nama":   info.get("longName", ticker),
            "Sektor": info.get("sector", "--"),
            "Desk":   (info.get("longBusinessSummary","") or "")[:300],
        }
    except Exception: return {}


def hitung_skor(fund):
    s = 0
    def to_float(v):
        try: return float(v)
        except (TypeError, ValueError): return None
    per = to_float(fund.get("PER"))
    if per and per > 0:
        s += 25 if per<10 else (20 if per<15 else (14 if per<20 else (8 if per<25 else 2)))
    else: s += 10
    pbv = to_float(fund.get("PBV"))
    if pbv and pbv > 0:
        s += 20 if pbv<1 else (15 if pbv<2 else (10 if pbv<3 else 4))
    else: s += 8
    roe = to_float(fund.get("ROE"))
    if roe: s += 25 if roe*100>=25 else (20 if roe*100>=15 else (12 if roe*100>=10 else 5))
    else: s += 8
    m = to_float(fund.get("Margin"))
    if m: s += 15 if m*100>=20 else (10 if m*100>=10 else (5 if m*100>=5 else 0))
    else: s += 5
    de = to_float(fund.get("DE"))
    if de is not None: s += 15 if de<30 else (10 if de<60 else (5 if de<100 else 0))
    else: s += 5
    return min(s, 100)


def fmt_mcap(v):
    if not v: return "--"
    if v >= 1e12: return f"Rp {v/1e12:.1f}T"
    if v >= 1e9:  return f"Rp {v/1e9:.1f}M"
    return f"Rp {v/1e6:.0f}jt"


@st.cache_data(ttl=900)
def ambil_berita(ticker):
    semua = []
    query = ticker.replace(".JK","").replace("-USD","").replace("=X","")
    try:
        q   = quote(f"{query} saham investasi")
        url = f"https://news.google.com/rss/search?q={q}&hl=id&gl=ID&ceid=ID:id"
        r   = requests.get(url, headers=random.choice(BROWSER_HEADERS), timeout=8)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml-xml")
            for item in soup.find_all("item")[:8]:
                t  = item.find("title")
                d  = item.find("pubDate")
                sr = item.find("source")
                if t: semua.append({
                    "judul":  t.text.strip()[:130],
                    "tgl":    d.text[:10] if d else "",
                    "sumber": sr.text.strip() if sr else "Google News"
                })
    except Exception: pass
    if len(semua) < 3:
        try:
            for item in (yf.Ticker(ticker).news or [])[:6]:
                c = item.get("content", {})
                t = c.get("title","") if isinstance(c, dict) else item.get("title","")
                p = c.get("provider",{}).get("displayName","Yahoo") if isinstance(c, dict) else item.get("publisher","Yahoo")
                if t: semua.append({"judul": t[:130], "tgl": "", "sumber": p})
        except Exception: pass
    return semua


def sentimen_teks(judul):
    j = judul.lower()
    p = sum(1 for k in KATA_POSITIF if k in j)
    n = sum(1 for k in KATA_NEGATIF if k in j)
    if p > n: return "pos"
    if n > p: return "neg"
    return "neu"


def buat_jadwal_30hari(np_, nv, ap, av):
    jadwal = []
    today  = pd.Timestamp.now().normalize()
    end    = today + pd.Timedelta(days=30)
    if np_ and ap:
        t = pd.Timestamp(np_)
        while t <= end:
            if t > today: jadwal.append({"tgl": t, "type": "peak"})
            t += pd.Timedelta(days=ap)
    if nv and av:
        t = pd.Timestamp(nv)
        while t <= end:
            if t > today: jadwal.append({"tgl": t, "type": "valley"})
            t += pd.Timedelta(days=av)
    return sorted(jadwal, key=lambda x: x["tgl"])


def hitung_sr_kuat(df, lookback=20):
    low  = df["Low_IDR"].values
    high = df["High_IDR"].values
    sups, ress = [], []
    for i in range(lookback, len(df)):
        sups.append(float(low[i-lookback:i].min()))
        ress.append(float(high[i-lookback:i].max()))
    def cluster(pts, n=3):
        if not pts: return []
        pts = sorted(set(round(p, -2) for p in pts))
        cls, used = [], set()
        for p in pts:
            if p in used: continue
            grp = [x for x in pts if abs(x-p)/max(p,1) < 0.02]
            cls.append(float(sum(grp)/len(grp)))
            for x in grp: used.add(x)
        return sorted(cls)[-n:]
    return cluster(sups), cluster(ress)

# ══════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGASI
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='padding:16px 0 20px;'>
      <div style='font-family:Syne,sans-serif;font-size:1.1rem;font-weight:800;
                  background:linear-gradient(90deg,#00c8ff,#00ff9d);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
        ▲ MAESTRO
      </div>
      <div style='font-size:0.65rem;color:#5a6a82;letter-spacing:0.1em;margin-top:2px;'>
        TRADING INTELLIGENCE v3.0
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.65rem;color:#5a6a82;letter-spacing:0.1em;margin-bottom:6px;'>MODE OPERASI</div>", unsafe_allow_html=True)
    mode = st.radio("", [
        "▲  Analisis 1 Aset",
        "◈  Screener Saham IDX",
        "◎  Screener Crypto",
        "◇  Screener Forex",
    ], label_visibility="collapsed")

    st.divider()

    if "Analisis" in mode:
        st.markdown("<div style='font-size:0.65rem;color:#5a6a82;letter-spacing:0.1em;margin-bottom:6px;'>KODE ASET</div>", unsafe_allow_html=True)
        ticker  = st.text_input("", "BBCA.JK", label_visibility="collapsed",
                                placeholder="cth: BBCA.JK, BTC-USD, EURUSD=X").upper().strip()

        st.markdown("<div style='font-size:0.65rem;color:#5a6a82;letter-spacing:0.1em;margin:10px 0 6px;'>PERIODE DATA</div>", unsafe_allow_html=True)
        # ── UBAH PERIODE DI SINI ─────────────────────────────────────────
        # Tambah / hapus opsi sesuai kebutuhan: "1mo","2mo","3mo","6mo","1y","2y","5y"
        # index=3 artinya default = "1y" (hitungan dari 0)
        periode = st.selectbox("", ["1mo","2mo","3mo","6mo","1y","2y","5y"],
                               index=0, label_visibility="collapsed")
        # ─────────────────────────────────────────────────────────────────

        run = st.button("ANALISIS SEKARANG", use_container_width=True)

    elif "Saham" in mode:
        st.markdown("<div style='font-size:0.65rem;color:#5a6a82;letter-spacing:0.1em;margin-bottom:6px;'>BUDGET (Rp)</div>", unsafe_allow_html=True)
        budget = st.number_input("", 10000, 100_000_000, 500_000, 50_000, label_visibility="collapsed")
        run    = st.button("SCAN SAHAM IDX", use_container_width=True)

    elif "Crypto" in mode:
        st.markdown("<div style='font-size:0.65rem;color:#5a6a82;letter-spacing:0.1em;margin-bottom:6px;'>BUDGET (Rp)</div>", unsafe_allow_html=True)
        budget = st.number_input("", 10000, 100_000_000, 1_000_000, 100_000, label_visibility="collapsed")
        run    = st.button("SCAN CRYPTO", use_container_width=True)

    elif "Forex" in mode:
        st.markdown("<div style='font-size:0.65rem;color:#5a6a82;letter-spacing:0.1em;margin-bottom:6px;'>BUDGET (Rp)</div>", unsafe_allow_html=True)
        budget = st.number_input("", 10000, 100_000_000, 2_000_000, 500_000, label_visibility="collapsed")
        run    = st.button("SCAN FOREX", use_container_width=True)

    st.divider()
    st.markdown("<div style='font-size:0.62rem;color:#5a6a82;'>Data: yfinance + Google News<br>Refresh: setiap 10 menit</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# HEADER UTAMA
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="maestro-header">
  <div class="maestro-logo">M</div>
  <div>
    <div class="maestro-title">MAESTRO Trading Intelligence</div>
    <div class="maestro-sub">QUANTITATIVE SYSTEM · TIME-CYCLE · BANDARMOLOGI · BERITA INDONESIA</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# MODE: ANALISIS 1 ASET
# ══════════════════════════════════════════════════════════════════════
if "Analisis" in mode:
    if not run:
        st.markdown("""
        <div style='text-align:center;padding:80px 20px;color:#5a6a82;'>
          <div style='font-family:Syne,sans-serif;font-size:2rem;font-weight:800;margin-bottom:12px;'>
            Masukkan kode aset & klik Analisis
          </div>
          <div style='font-size:0.85rem;'>
            Saham IDX: BBCA.JK · TLKM.JK &nbsp;|&nbsp;
            Crypto: BTC-USD · ETH-USD &nbsp;|&nbsp;
            Forex: EURUSD=X · XAUUSD=X &nbsp;|&nbsp;
            US: AAPL · NVDA
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        with st.spinner(f"Menganalisis {ticker}..."):
            df, is_jk, kurs = tarik_data(ticker, periode)

        if df is None or df.empty:
            st.error(f"Gagal mengambil data untuk **{ticker}**. Periksa kode ticker dan koneksi internet.")
        else:
            harga  = float(df["Close_IDR"].iloc[-1])
            harga0 = float(df["Close_IDR"].iloc[-2]) if len(df) > 1 else harga
            pct    = (harga - harga0) / max(harga0, 1) * 100
            sup    = float(df["Support"].dropna().iloc[-1])    if not df["Support"].dropna().empty    else harga*0.95
            res    = float(df["Resistance"].dropna().iloc[-1]) if not df["Resistance"].dropna().empty else harga*1.05
            atr_v  = float(df["ATR"].dropna().iloc[-1])        if not df["ATR"].dropna().empty        else (res-sup)*0.3
            bandar = df["Bandar"].iloc[-1]
            vol_l  = float(df["Volume"].iloc[-1])
            vol_m  = float(df["Volume"].rolling(20).mean().iloc[-1]) if len(df) >= 20 else vol_l

            fund   = ambil_fundamental(ticker)
            skor   = hitung_skor(fund)
            ap, np_, av, nv, peaks, valleys = hitung_siklus(df)
            sup_levels, res_levels = hitung_sr_kuat(df)

            # Risk/Reward
            rr_num = (res*0.98 - sup) / max(sup - sup*0.96, 1)

            # ── METRIC CARDS ──────────────────────────────────────────
            pct_cls = "metric-up" if pct >= 0 else "metric-dn"
            pct_sym = "▲" if pct >= 0 else "▼"
            ban_cls = "metric-up" if bandar=="AKUMULASI" else ("metric-dn" if bandar=="DISTRIBUSI" else "metric-neu")
            vol_ratio = vol_l / max(vol_m, 1)

            lot_str = f"Rp {harga*100:,.0f}" if is_jk else f"Rp {harga:,.2f}"
            lot_lbl = "1 LOT (100 LBR)" if is_jk else "1 UNIT"

            st.markdown(f"""
            <div class="metric-grid">
              <div class="metric-card">
                <div class="metric-label">Harga Terakhir</div>
                <div class="metric-value">Rp {harga:,.0f}</div>
                <div class="metric-delta {pct_cls}">{pct_sym} {abs(pct):.2f}% hari ini</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Skor Fundamental</div>
                <div class="metric-value" style="color:{'#00ff9d' if skor>=70 else ('#ffd166' if skor>=45 else '#ff3d6e')}">{skor}<span style="font-size:0.8rem;color:#5a6a82">/100</span></div>
                <div class="metric-delta metric-neu">{'EXCELLENT' if skor>=75 else ('GOOD' if skor>=55 else ('FAIR' if skor>=35 else 'WEAK'))}</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Bandarmologi</div>
                <div class="metric-value {ban_cls}" style="font-size:1rem;">{bandar}</div>
                <div class="metric-delta metric-neu">Vol {vol_ratio:.1f}x avg</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">ATR (14)</div>
                <div class="metric-value" style="font-size:1.1rem;">Rp {atr_v:,.0f}</div>
                <div class="metric-delta metric-neu">Volatilitas harian</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">{lot_lbl}</div>
                <div class="metric-value" style="font-size:1.0rem;">{lot_str}</div>
                <div class="metric-delta metric-neu">Kurs Rp {kurs:,.0f}/USD</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # ── CHART INTERAKTIF ──────────────────────────────────────
            st.markdown('<div class="sec-header">Chart Interaktif</div>', unsafe_allow_html=True)

            fig = make_subplots(rows=2, cols=1, row_heights=[0.78, 0.22],
                                shared_xaxes=True, vertical_spacing=0.03)

            # Zona beli & jual
            fig.add_trace(go.Scatter(
                x=list(df["Date"])+list(df["Date"][::-1]),
                y=list(df["Support"])+list((df["Support"]*0.97)[::-1]),
                fill="toself", fillcolor="rgba(0,255,157,0.07)",
                line=dict(color="rgba(0,0,0,0)"), name="Zona Beli"), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=list(df["Date"])+list(df["Date"][::-1]),
                y=list(df["Resistance"]*1.03)+list(df["Resistance"][::-1]),
                fill="toself", fillcolor="rgba(255,61,110,0.07)",
                line=dict(color="rgba(0,0,0,0)"), name="Zona Jual"), row=1, col=1)

            # Harga utama
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Close_IDR"], mode="lines",
                line=dict(color="#00c8ff", width=2.2),
                name=ticker,
                hovertemplate="<b>%{x|%d %b %Y}</b><br>Rp %{y:,.0f}<extra></extra>"), row=1, col=1)

            # Support & Resistance dinamis
            fig.add_trace(go.Scatter(x=df["Date"], y=df["Support"], mode="lines",
                line=dict(color="#00ff9d", width=1, dash="dot"), name="Support"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df["Date"], y=df["Resistance"], mode="lines",
                line=dict(color="#ff3d6e", width=1, dash="dot"), name="Resistance"), row=1, col=1)

            # Garis S/R kuat horizontal
            x0, x1 = df["Date"].iloc[0], df["Date"].iloc[-1]
            for i, sv in enumerate(sup_levels):
                fig.add_shape(type="line", x0=x0, x1=x1, y0=sv, y1=sv,
                              xref="x", yref="y", line=dict(color="#00ff9d", dash="dashdot", width=1.5))
                fig.add_annotation(x=x1, y=sv, xref="x", yref="y",
                                   text=f"  S{i+1} Rp {sv:,.0f}", showarrow=False,
                                   font=dict(color="#00ff9d", size=9), xanchor="left")
            for i, rv in enumerate(res_levels):
                fig.add_shape(type="line", x0=x0, x1=x1, y0=rv, y1=rv,
                              xref="x", yref="y", line=dict(color="#ff3d6e", dash="dashdot", width=1.5))
                fig.add_annotation(x=x1, y=rv, xref="x", yref="y",
                                   text=f"  R{i+1} Rp {rv:,.0f}", showarrow=False,
                                   font=dict(color="#ff3d6e", size=9), xanchor="left")

            # Puncak & Lembah historis
            if len(peaks):
                fig.add_trace(go.Scatter(
                    x=df["Date"].iloc[peaks], y=df["Close_IDR"].iloc[peaks], mode="markers",
                    marker=dict(symbol="triangle-down", color="#ff3d6e", size=11,
                                line=dict(color="white", width=1)), name="Puncak"), row=1, col=1)
            if len(valleys):
                fig.add_trace(go.Scatter(
                    x=df["Date"].iloc[valleys], y=df["Close_IDR"].iloc[valleys], mode="markers",
                    marker=dict(symbol="triangle-up", color="#00ff9d", size=11,
                                line=dict(color="white", width=1)), name="Lembah"), row=1, col=1)

            # Garis prediksi siklus
            def vline(fig, xdate, color, label):
                xs = pd.Timestamp(xdate).strftime("%Y-%m-%d")
                fig.add_shape(type="line", x0=xs, x1=xs, y0=0, y1=1,
                              yref="paper", xref="x", line=dict(color=color, dash="dash", width=1.2))
                fig.add_annotation(x=xs, y=1.02, yref="paper", xref="x",
                                   text=label, showarrow=False,
                                   font=dict(color=color, size=9), xanchor="center")
            if np_: vline(fig, np_, "#ff3d6e", f"Puncak ~{pd.Timestamp(np_).strftime('%d %b')}")
            if nv:  vline(fig, nv,  "#00ff9d", f"Lembah ~{pd.Timestamp(nv).strftime('%d %b')}")

            # Volume
            cv = ["#00ff9d" if df["Close_IDR"].iloc[i] >= df["Open_IDR"].iloc[i] else "#ff3d6e"
                  for i in range(len(df))]
            fig.add_trace(go.Bar(x=df["Date"], y=df["Volume"], marker_color=cv,
                                 name="Volume", opacity=0.7), row=2, col=1)

            fig.update_layout(
                template="plotly_dark", height=580,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(8,12,18,1)",
                hovermode="x unified", dragmode="pan",
                legend=dict(orientation="h", y=1.01, x=0, font=dict(size=10)),
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)",
                           rangeslider=dict(visible=False), type="date"),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                           tickprefix="Rp ", tickformat=",.0f", side="right"),
                xaxis2=dict(showgrid=False, type="date"),
                yaxis2=dict(showgrid=False, title=""),
                margin=dict(l=10, r=120, t=40, b=10),
            )
            st.plotly_chart(fig, use_container_width=True,
                            config=dict(scrollZoom=True, displayModeBar=True,
                                        modeBarButtonsToAdd=["drawline","eraseshape"]))

            # ── 3 KOLOM UTAMA ─────────────────────────────────────────
            col1, col2, col3 = st.columns([1, 1, 1])

            # ── COL 1: TRADING PLAN ───────────────────────────────────
            with col1:
                st.markdown('<div class="sec-header">Trading Plan</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="tp-card tp-buy">
                  <div><div class="tp-label tp-label-buy">AREA BELI IDEAL</div>
                  <div class="tp-val">Rp {sup:,.0f} – Rp {sup*1.02:,.0f}</div></div>
                </div>
                <div class="tp-card tp-buy">
                  <div><div class="tp-label tp-label-buy">BUY BREAKOUT</div>
                  <div class="tp-val">Tembus Rp {res*1.01:,.0f}</div></div>
                </div>
                <div class="tp-card tp-sell">
                  <div><div class="tp-label tp-label-sell">TAKE PROFIT</div>
                  <div class="tp-val">Rp {res*0.98:,.0f}</div></div>
                </div>
                <div class="tp-card tp-sell">
                  <div><div class="tp-label tp-label-sell">CUT LOSS</div>
                  <div class="tp-val">Rp {sup*0.96:,.0f}</div></div>
                </div>
                <div class="tp-card tp-wait">
                  <div><div class="tp-label tp-label-wait">RISK / REWARD</div>
                  <div class="tp-val">1 : {rr_num:.1f}</div></div>
                </div>
                """, unsafe_allow_html=True)

            # ── COL 2: FUNDAMENTAL ────────────────────────────────────
            with col2:
                st.markdown('<div class="sec-header">Fundamental</div>', unsafe_allow_html=True)

                def fval(v, fmt=".1f", suffix=""):
                    return f"{v:{fmt}}{suffix}" if v is not None else "--"
                def fcls(v, lo, hi):
                    if v is None: return "fund-mid"
                    return "fund-ok" if v<=lo else ("fund-mid" if v<=hi else "fund-bad")
                def fclsR(v, lo, hi):  # reversed (higher=better)
                    if v is None: return "fund-mid"
                    return "fund-ok" if v>=hi else ("fund-mid" if v>=lo else "fund-bad")

                per_v = fund.get("PER"); pbv_v = fund.get("PBV")
                roe_v = fund.get("ROE"); mar_v = fund.get("Margin")
                de_v  = fund.get("DE");  bet_v = fund.get("Beta")
                div_v = fund.get("Div"); eps_v = fund.get("EPS")
                h52h  = fund.get("52H"); h52l  = fund.get("52L")
                mc    = fund.get("MCap"); desk = fund.get("Desk","")

                st.markdown(f"""
                <div class="fund-grid">
                  <div class="fund-row"><span class="fund-key">PER</span>
                    <span class="fund-val {fcls(per_v,15,25)}">{fval(per_v,".1f","x") if per_v else "--"}</span></div>
                  <div class="fund-row"><span class="fund-key">PBV</span>
                    <span class="fund-val {fcls(pbv_v,1,3)}">{fval(pbv_v,".2f","x") if pbv_v else "--"}</span></div>
                  <div class="fund-row"><span class="fund-key">ROE</span>
                    <span class="fund-val {fclsR(roe_v*100 if roe_v else None,10,20)}">{f"{roe_v*100:.1f}%" if roe_v else "--"}</span></div>
                  <div class="fund-row"><span class="fund-key">Net Margin</span>
                    <span class="fund-val {fclsR(mar_v*100 if mar_v else None,5,15)}">{f"{mar_v*100:.1f}%" if mar_v else "--"}</span></div>
                  <div class="fund-row"><span class="fund-key">Debt/EQ</span>
                    <span class="fund-val {fcls(de_v,60,120)}">{fval(de_v,".0f","%") if de_v is not None else "--"}</span></div>
                  <div class="fund-row"><span class="fund-key">Beta</span>
                    <span class="fund-val fund-mid">{fval(bet_v,".2f") if bet_v else "--"}</span></div>
                  <div class="fund-row"><span class="fund-key">EPS</span>
                    <span class="fund-val fund-mid">{fval(eps_v,".2f") if eps_v else "--"}</span></div>
                  <div class="fund-row"><span class="fund-key">Div Yield</span>
                    <span class="fund-val fund-ok">{f"{div_v*100:.2f}%" if div_v else "--"}</span></div>
                  <div class="fund-row"><span class="fund-key">52W High</span>
                    <span class="fund-val fund-neu">{f"Rp {h52h:,.0f}" if h52h else "--"}</span></div>
                  <div class="fund-row"><span class="fund-key">52W Low</span>
                    <span class="fund-val fund-neu">{f"Rp {h52l:,.0f}" if h52l else "--"}</span></div>
                  <div class="fund-row"><span class="fund-key">Market Cap</span>
                    <span class="fund-val fund-mid">{fmt_mcap(mc)}</span></div>
                  <div class="fund-row"><span class="fund-key">Siklus Puncak</span>
                    <span class="fund-val fund-mid">{f"{ap} hari" if ap else "--"}</span></div>
                  <div class="fund-row"><span class="fund-key">Siklus Lembah</span>
                    <span class="fund-val fund-mid">{f"{av} hari" if av else "--"}</span></div>
                  <div class="fund-row"><span class="fund-key">ATR Harian</span>
                    <span class="fund-val fund-mid">Rp {atr_v:,.0f}</span></div>
                </div>
                """, unsafe_allow_html=True)

                # Skor ring
                sk_cls = "skor-ok" if skor>=70 else ("skor-mid" if skor>=45 else "skor-bad")
                sk_lbl = "EXCELLENT" if skor>=75 else ("GOOD" if skor>=55 else ("FAIR" if skor>=35 else "WEAK"))
                st.markdown(f"""
                <div class="skor-wrap" style="margin-top:12px;">
                  <div class="skor-ring {sk_cls}">{skor}</div>
                  <div>
                    <div style="font-family:Syne,sans-serif;font-weight:700;font-size:1rem;">{sk_lbl}</div>
                    <div style="font-size:0.72rem;color:#5a6a82;">Skor Fundamental Maestro /100</div>
                    {'<div style="font-size:0.72rem;color:#5a6a82;margin-top:6px;">'+desk[:120]+"...</div>" if desk else ""}
                  </div>
                </div>
                """, unsafe_allow_html=True)

            # ── COL 3: JADWAL 7 HARI ─────────────────────────────────
            with col3:
                st.markdown('<div class="sec-header">Jadwal 7 Hari</div>', unsafe_allow_html=True)
                today_ts = pd.Timestamp.now().normalize()
                for i in range(1, 8):
                    h_ts   = today_ts + pd.Timedelta(days=i)
                    nm     = HARI_ID.get(h_ts.strftime("%A"), h_ts.strftime("%a"))
                    tgl_s  = h_ts.strftime(f"{nm}, %d %b")
                    is_buy = nv  and h_ts == pd.Timestamp(nv).normalize()
                    is_sel = np_ and h_ts == pd.Timestamp(np_).normalize()
                    if is_buy:
                        row_cls  = "sched-row sched-buy"
                        badge_cl = "badge badge-buy"; badge_t = "BELI"
                        aksi = f"Prediksi Lembah → area Rp {sup:,.0f}"
                    elif is_sel:
                        row_cls  = "sched-row sched-sell"
                        badge_cl = "badge badge-sell"; badge_t = "JUAL"
                        aksi = f"Prediksi Puncak → area Rp {res:,.0f}"
                    else:
                        row_cls  = "sched-row sched-wait"
                        badge_cl = "badge badge-wait"; badge_t = "WAIT"
                        aksi = "Pantau pergerakan"
                    st.markdown(f"""
                    <div class="{row_cls}">
                      <span class="sched-day">{tgl_s}</span>
                      <span class="{badge_cl}">{badge_t}</span>
                      <span style="font-size:0.76rem;">{aksi}</span>
                    </div>""", unsafe_allow_html=True)

            # ── BANDARMOLOGI DETAIL ───────────────────────────────────
            st.markdown('<div class="sec-header">Bandarmologi — Jejak Institusi</div>', unsafe_allow_html=True)
            b_cls = ("bandar-card bandar-akum" if bandar=="AKUMULASI"
                     else ("bandar-card bandar-dist" if bandar=="DISTRIBUSI"
                     else "bandar-card bandar-neu"))
            b_dot = ("#00ff9d" if bandar=="AKUMULASI" else ("#ff3d6e" if bandar=="DISTRIBUSI" else "#5a6a82"))
            b_desc = {
                "AKUMULASI": "Volume spike + candle bullish — tanda institusi/bandar sedang masuk & mengumpulkan posisi.",
                "DISTRIBUSI": "Volume spike + candle bearish — tanda institusi/bandar sedang melepas & menjual posisi.",
                "NETRAL":     "Volume normal, tidak ada tanda aktivitas institusi signifikan hari ini.",
            }
            last5 = df[["Date","Close_IDR","Volume","Bandar"]].tail(5).copy()
            last5["Close_IDR"] = last5["Close_IDR"].map(lambda x: f"Rp {x:,.0f}")
            last5["Volume"]    = last5["Volume"].map(lambda x: f"{x:,.0f}")
            last5["Date"]      = last5["Date"].dt.strftime("%d %b %Y")
            last5.columns      = ["Tanggal","Harga","Volume","Status Bandar"]

            bc1, bc2 = st.columns([1, 2])
            with bc1:
                st.markdown(f"""
                <div class="{b_cls}">
                  <div class="bandar-dot" style="background:{b_dot};box-shadow:0 0 10px {b_dot};"></div>
                  <div>
                    <div style="font-family:Syne,sans-serif;font-weight:700;font-size:1.1rem;">{bandar}</div>
                    <div style="font-size:0.75rem;color:#a0aec0;margin-top:4px;">{b_desc[bandar]}</div>
                    <div style="font-size:0.72rem;color:#5a6a82;margin-top:6px;">
                      Volume hari ini: {vol_l:,.0f} ({vol_ratio:.1f}x rata-rata)
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with bc2:
                st.dataframe(last5, use_container_width=True, hide_index=True)

            # ── PLAN TRADING 1 BULAN ──────────────────────────────────
            st.markdown('<div class="sec-header">Plan Trading 1 Bulan Ke Depan</div>', unsafe_allow_html=True)
            jadwal = buat_jadwal_30hari(np_, nv, ap, av)
            if not jadwal:
                st.info("Data siklus belum cukup untuk proyeksi 1 bulan. Coba gunakan periode data 1y atau 2y.")
            else:
                # Summary stats
                n_beli = sum(1 for j in jadwal if j["type"]=="valley")
                n_jual = sum(1 for j in jadwal if j["type"]=="peak")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Event", f"{len(jadwal)} event")
                m2.metric("Sinyal Beli", f"{n_beli}x", delta="Potensi entry")
                m3.metric("Sinyal Jual", f"{n_jual}x", delta="Potensi exit")
                m4.metric("Siklus Avg", f"{ap or '--'} / {av or '--'} hari", delta="Puncak / Lembah")

                # Header tabel
                st.markdown("""
                <div class="plan-header">
                  <span>TANGGAL</span><span>HARI</span><span>EVENT & AKSI</span><span>TARGET HARGA</span>
                </div>""", unsafe_allow_html=True)

                for j in jadwal:
                    tgl_s  = j["tgl"].strftime("%d %b %Y")
                    nm_h   = HARI_ID.get(j["tgl"].strftime("%A"), j["tgl"].strftime("%a"))
                    is_v   = j["type"] == "valley"
                    ev_txt = "LEMBAH — Area Beli & Akumulasi" if is_v else "PUNCAK — Area Jual & Take Profit"
                    hg_txt = f"Rp {sup:,.0f}" if is_v else f"Rp {res:,.0f}"
                    row_cl = "plan-row plan-row-buy" if is_v else "plan-row plan-row-sell"
                    color  = "#00ff9d" if is_v else "#ff3d6e"
                    st.markdown(f"""
                    <div class="{row_cl}">
                      <span style="font-weight:600;">{tgl_s}</span>
                      <span style="color:#5a6a82;">{nm_h}</span>
                      <span style="color:{color};">{ev_txt}</span>
                      <span style="font-weight:700;">{hg_txt}</span>
                    </div>""", unsafe_allow_html=True)

                # Strategi rangkuman
                st.markdown(f"""
                <div class="panel" style="margin-top:16px;">
                  <div style="font-family:Syne,sans-serif;font-weight:700;margin-bottom:12px;font-size:0.9rem;">Strategi Global 1 Bulan</div>
                  <div class="fund-grid">
                    <div class="fund-row"><span class="fund-key">Modal per Entry</span><span class="fund-val">Max 2% dari portofolio</span></div>
                    <div class="fund-row"><span class="fund-key">Stop Loss Global</span><span class="fund-val fund-bad">Rp {sup*0.95:,.0f}</span></div>
                    <div class="fund-row"><span class="fund-key">Target Konservatif</span><span class="fund-val fund-ok">Rp {res*0.97:,.0f}</span></div>
                    <div class="fund-row"><span class="fund-key">Target Agresif</span><span class="fund-val fund-ok">Rp {res*1.03:,.0f}</span></div>
                    <div class="fund-row"><span class="fund-key">Risk/Reward Ratio</span><span class="fund-val fund-mid">1 : {rr_num:.1f}</span></div>
                    <div class="fund-row"><span class="fund-key">Review Mingguan</span><span class="fund-val">Pantau volume spike</span></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            # ── BERITA & SENTIMEN ─────────────────────────────────────
            st.markdown('<div class="sec-header">Berita & Sentimen Pasar</div>', unsafe_allow_html=True)
            with st.spinner("Mengambil berita terkini..."):
                berita = ambil_berita(ticker)

            if not berita:
                st.info("Berita tidak tersedia saat ini.")
            else:
                n_pos = n_neg = n_neu = 0
                for b in berita:
                    s = sentimen_teks(b["judul"])
                    if s == "pos": n_pos += 1
                    elif s == "neg": n_neg += 1
                    else: n_neu += 1
                    cls = {"pos":"news-pos","neg":"news-neg","neu":"news-neu"}[s]
                    badge_t = {"pos":"POSITIF","neg":"NEGATIF","neu":"NETRAL"}[s]
                    badge_c = {"pos":"#00ff9d","neg":"#ff3d6e","neu":"#5a6a82"}[s]
                    st.markdown(f"""
                    <div class="news-item {cls}">
                      <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                        <span class="news-badge" style="color:{badge_c};">{badge_t}</span>
                        <span class="news-src">{b.get("sumber","")} · {b.get("tgl","")}</span>
                      </div>
                      <div>{b["judul"]}</div>
                    </div>""", unsafe_allow_html=True)

                # Sentimen summary
                total = n_pos + n_neg + n_neu
                overall = "BULLISH" if n_pos > n_neg else ("BEARISH" if n_neg > n_pos else "NETRAL")
                ov_col  = "#00ff9d" if overall=="BULLISH" else ("#ff3d6e" if overall=="BEARISH" else "#ffd166")
                st.markdown(f"""
                <div class="panel" style="margin-top:12px;display:flex;align-items:center;gap:20px;">
                  <div style="font-family:Syne,sans-serif;font-size:1.2rem;font-weight:800;color:{ov_col};">
                    {overall}
                  </div>
                  <div style="font-size:0.8rem;color:#5a6a82;">
                    Dari {total} berita: &nbsp;
                    <span style="color:#00ff9d;">{n_pos} positif</span> &nbsp;|&nbsp;
                    <span style="color:#ff3d6e;">{n_neg} negatif</span> &nbsp;|&nbsp;
                    <span style="color:#5a6a82;">{n_neu} netral</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            # ── RINGKASAN AKHIR ───────────────────────────────────────
            st.markdown('<div class="sec-header">Kesimpulan Maestro</div>', unsafe_allow_html=True)
            over_c = "#00ff9d" if n_pos > n_neg else ("#ff3d6e" if n_neg > n_pos else "#ffd166")
            st.markdown(f"""
            <div class="panel">
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;">
                <div>
                  <div class="metric-label">Aset</div>
                  <div style="font-family:Syne,sans-serif;font-size:1.3rem;font-weight:800;">{ticker}</div>
                  <div style="font-size:0.75rem;color:#5a6a82;">{'Saham IDX' if is_jk else ('Crypto' if '-USD' in ticker else ('Forex' if '=X' in ticker else 'Saham US'))}</div>
                </div>
                <div>
                  <div class="metric-label">Harga & Perubahan</div>
                  <div style="font-family:Syne,sans-serif;font-size:1.1rem;font-weight:700;">Rp {harga:,.0f}</div>
                  <div style="color:{'#00ff9d' if pct>=0 else '#ff3d6e'};font-size:0.8rem;">{'▲' if pct>=0 else '▼'} {abs(pct):.2f}%</div>
                </div>
                <div>
                  <div class="metric-label">Sentimen Pasar</div>
                  <div style="font-family:Syne,sans-serif;font-size:1.1rem;font-weight:700;color:{over_c};">{overall}</div>
                </div>
                <div>
                  <div class="metric-label">Puncak Berikutnya</div>
                  <div style="font-weight:600;color:#ff3d6e;">{pd.Timestamp(np_).strftime('%d %b %Y') if np_ else 'N/A'}</div>
                </div>
                <div>
                  <div class="metric-label">Lembah Berikutnya</div>
                  <div style="font-weight:600;color:#00ff9d;">{pd.Timestamp(nv).strftime('%d %b %Y') if nv else 'N/A'}</div>
                </div>
                <div>
                  <div class="metric-label">Rekomendasi</div>
                  <div style="font-weight:700;color:{'#00ff9d' if skor>=60 else ('#ffd166' if skor>=40 else '#ff3d6e')};">
                    {'LAYAK DIPERTIMBANGKAN' if skor>=60 else ('MONITOR' if skor>=40 else 'HINDARI')}
                  </div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# MODE: SCREENER SAHAM IDX
# ══════════════════════════════════════════════════════════════════════
elif "Saham" in mode:
    if not run:
        st.markdown("<div style='color:#5a6a82;padding:40px 0;'>Masukkan budget dan klik SCAN.</div>", unsafe_allow_html=True)
    else:
        LQ45 = [
            # ── BLUECHIP / LQ45 ──────────────────────────────────────────────
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
        ]
        hasil = []
        bar   = st.progress(0, text="Scanning saham...")
        for i, tk in enumerate(LQ45):
            df, is_jk, _ = tarik_data(tk, "6mo")
            if df is not None and not df.empty:
                h   = float(df["Close_IDR"].iloc[-1])
                lot = h * 100
                if lot <= budget:
                    f   = ambil_fundamental(tk)
                    sk  = hitung_skor(f)
                    sup = float(df["Support"].dropna().iloc[-1]) if not df["Support"].dropna().empty else h*0.95
                    res = float(df["Resistance"].dropna().iloc[-1]) if not df["Resistance"].dropna().empty else h*1.05
                    pct = (h - float(df["Close_IDR"].iloc[-2]))/max(float(df["Close_IDR"].iloc[-2]),1)*100 if len(df)>1 else 0
                    hasil.append({"Rank":"","Ticker":tk,
                                  "Nama":(f.get("Nama") or tk)[:22],
                                  "Harga (Rp)":h, "1 Lot (Rp)":lot,
                                  "Chg%":round(pct,2), "Skor":sk,
                                  "PER":round(float(f["PER"]),1) if f.get("PER") else None,
                                  "PBV":round(float(f["PBV"]),2) if f.get("PBV") else None,
                                  "ROE%":round(float(f["ROE"])*100,1) if f.get("ROE") else None,
                                  "Support":sup,"Resistance":res,
                                  "Sektor":f.get("Sektor","--")})
            bar.progress((i+1)/len(LQ45), text=f"Scanning {tk}...")
        bar.empty()
        if hasil:
            df_h = pd.DataFrame(hasil).sort_values("Skor",ascending=False).reset_index(drop=True)
            df_h.index += 1; df_h.index.name = "Rank"
            st.markdown(f'<div class="sec-header">Hasil Screener — {len(df_h)} saham lolos budget Rp {budget:,.0f}</div>', unsafe_allow_html=True)
            st.dataframe(df_h.style.format({
                "Harga (Rp)":"Rp {:,.0f}","1 Lot (Rp)":"Rp {:,.0f}",
                "Support":"Rp {:,.0f}","Resistance":"Rp {:,.0f}",
                "Chg%":"{:+.2f}%","Skor":"{:.0f}",
                "PER":lambda x: f"{x:.1f}x" if x else "--",
                "PBV":lambda x: f"{x:.2f}x" if x else "--",
                "ROE%":lambda x: f"{x:.1f}%" if x else "--",
            }), use_container_width=True)
        else:
            st.warning(f"Tidak ada saham yang lolos budget Rp {budget:,.0f}. Coba naikkan budget.")

# ══════════════════════════════════════════════════════════════════════
# MODE: SCREENER CRYPTO
# ══════════════════════════════════════════════════════════════════════
elif "Crypto" in mode:
    if not run:
        st.markdown("<div style='color:#5a6a82;padding:40px 0;'>Masukkan budget dan klik SCAN.</div>", unsafe_allow_html=True)
    else:
        CRYPTO = [
                  # ── LARGE CAP ───────────────────────────────────────
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
                  "PAXG-USD", "GOLD-USD", "SILVER-USD", "OIL-USD", "NGAS-USD",]
        hasil = []
        bar   = st.progress(0, text="Scanning crypto...")
        for i, tk in enumerate(CRYPTO):
            df, _, kurs = tarik_data(tk, "6mo")
            if df is not None and not df.empty:
                h   = float(df["Close_IDR"].iloc[-1])
                pct = (h - float(df["Close_IDR"].iloc[-2]))/max(float(df["Close_IDR"].iloc[-2]),1)*100 if len(df)>1 else 0
                ap, np_, av, nv, _, _ = hitung_siklus(df)
                hasil.append({"Ticker":tk, "Harga (Rp)":h,
                              "Chg%":round(pct,2),
                              "Budget?":"[v] Ya" if h<=budget else "[x] Tidak",
                              "Jumlah dg Budget":f"{budget/h:.4f} unit" if h<=budget else "--",
                              "Siklus Puncak":f"{ap} hari" if ap else "--",
                              "Siklus Lembah":f"{av} hari" if av else "--",
                              "Next Peak":pd.Timestamp(np_).strftime('%d %b') if np_ else "--",
                              "Next Valley":pd.Timestamp(nv).strftime('%d %b') if nv else "--"})
            bar.progress((i+1)/len(CRYPTO), text=f"Scanning {tk}...")
        bar.empty()
        df_h = pd.DataFrame(hasil).sort_values("Harga (Rp)").reset_index(drop=True)
        df_h.index += 1
        st.markdown(f'<div class="sec-header">Hasil Screener Crypto — {len(df_h)} aset</div>', unsafe_allow_html=True)
        st.dataframe(df_h.style.format({"Harga (Rp)":"Rp {:,.2f}","Chg%":"{:+.2f}%"}),
                     use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# MODE: SCREENER FOREX
# ══════════════════════════════════════════════════════════════════════
elif "Forex" in mode:
    if not run:
        st.markdown("<div style='color:#5a6a82;padding:40px 0;'>Masukkan budget dan klik SCAN.</div>", unsafe_allow_html=True)
    else:
        FOREX = [
                # ── MAJOR PAIRS ─────────────────────────────────────
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
                "SB=F",]
        hasil = []
        bar   = st.progress(0, text="Scanning forex...")
        for i, tk in enumerate(FOREX):
            df, _, kurs = tarik_data(tk, "6mo")
            if df is not None and not df.empty:
                h   = float(df["Close_IDR"].iloc[-1])
                pct = (h - float(df["Close_IDR"].iloc[-2]))/max(float(df["Close_IDR"].iloc[-2]),1)*100 if len(df)>1 else 0
                hasil.append({"Instrumen":tk, "Harga (Rp)":h,
                              "Chg%":round(pct,2),
                              "Budget?":"[v] Ya" if h<=budget else "[x] Tidak"})
            bar.progress((i+1)/len(FOREX), text=f"Scanning {tk}...")
        bar.empty()
        df_h = pd.DataFrame(hasil).sort_values("Harga (Rp)").reset_index(drop=True)
        df_h.index += 1
        st.markdown(f'<div class="sec-header">Hasil Screener Forex & Komoditas</div>', unsafe_allow_html=True)
        st.dataframe(df_h.style.format({"Harga (Rp)":"Rp {:,.2f}","Chg%":"{:+.2f}%"}),
                     use_container_width=True)
