"""
SaaS Analytics Dashboard
CSV-based · 4 static tabs · Teal theme
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os, warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SaaS Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# DESIGN TOKENS — teal palette
# ─────────────────────────────────────────────
T = "#0097A7"       # teal primary
TL = "#00BCD4"      # teal light
TD = "#00695C"      # teal dark
BL = "#1C3D4F"      # dark blue-slate (text / sidebar)
SL = "#37474F"      # slate (secondary text)
GR = "#2E7D32"      # green (positive)
RD = "#C62828"      # red (negative)
OR = "#E65100"      # orange (warn)
BG = "#F5F8FA"      # page background
WH = "#FFFFFF"      # card background
BR = "#E0EAF0"      # border
MU = "#607D8B"      # muted text
PB = "#FAFCFD"      # plot background

PLAN_COLORS = {"FREE": TL, "PRO": T, "ENTERPRISE": BL}
MN = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
      7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif;}}
.stApp{{background:{BG};}}

/* ── Sidebar ── */
[data-testid="stSidebar"]{{
    background:{BL} !important;
    border-right:1px solid rgba(255,255,255,0.07);
}}
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stSelectbox label{{
    color:#A8D4DF!important;
    font-size:0.66rem!important;
    font-weight:700!important;
    letter-spacing:0.1em!important;
    text-transform:uppercase!important;
}}
[data-testid="stSidebar"] div[data-baseweb]{{
    background:rgba(255,255,255,0.07)!important;
    border-color:rgba(255,255,255,0.15)!important;
    border-radius:7px!important;
}}
[data-testid="stSidebar"] span[data-baseweb="tag"]{{
    background:rgba(0,188,212,0.35)!important;
    color:white!important;
}}

/* ── Tabs ── */
button[data-baseweb="tab"]{{
    font-family:'Inter',sans-serif!important;
    font-size:0.82rem!important;
    font-weight:600!important;
    color:{SL}!important;
    padding:10px 22px!important;
    border-radius:0!important;
}}
button[data-baseweb="tab"][aria-selected="true"]{{
    color:{T}!important;
    border-bottom:2px solid {T}!important;
}}
div[data-baseweb="tab-list"]{{
    border-bottom:1px solid {BR}!important;
    background:white!important;
    padding:0 8px!important;
    border-radius:0!important;
    gap:4px!important;
}}
div[data-baseweb="tab-panel"]{{
    padding-top:20px!important;
}}

/* ── KPI tile — FIXED height ── */
.kpi{{
    background:{WH};
    border-radius:10px;
    padding:14px 16px 12px;
    border-top:3px solid {T};
    box-shadow:0 1px 5px rgba(0,0,0,0.07);
    height:108px;
    display:flex;
    flex-direction:column;
    justify-content:space-between;
    overflow:hidden;
}}
.kpi-lbl{{
    font-size:0.66rem;
    font-weight:700;
    letter-spacing:0.09em;
    text-transform:uppercase;
    color:{MU};
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}}
.kpi-val{{
    font-size:1.6rem;
    font-weight:700;
    color:{BL};
    line-height:1.1;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}}
.kpi-d{{font-size:0.71rem;font-weight:600;}}
.kpi-d.up{{color:{GR};}}.kpi-d.dn{{color:{RD};}}.kpi-d.nt{{color:{MU};}}

/* ── Section header ── */
.sh{{
    font-size:0.9rem;font-weight:700;color:{BL};
    margin:24px 0 10px;padding-bottom:6px;
    border-bottom:2px solid {TL};
}}

/* ── Page header ── */
.ph{{margin-bottom:14px;}}
.pt{{font-size:1.45rem;font-weight:700;color:{BL};letter-spacing:-0.02em;}}
.ps{{font-size:0.8rem;color:{MU};margin-top:2px;}}

/* ── Filter pills ── */
.pill{{
    display:inline-block;
    background:rgba(0,151,167,0.09);
    color:{BL};
    border:1px solid rgba(0,151,167,0.22);
    border-radius:20px;
    padding:2px 10px;
    font-size:0.69rem;font-weight:600;
    margin:0 3px 8px 0;
}}

#MainMenu,footer,header{{visibility:hidden;}}
.block-container{{padding:1.6rem 2rem 2rem;}}
div[data-testid="stHorizontalBlock"]{{gap:10px;}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "exports")

@st.cache_data
def load_all():
    def read(fname):
        df = pd.read_csv(os.path.join(DATA_DIR, fname))
        df.columns = [c.upper() for c in df.columns]
        # normalise every key string column → UPPER, strip whitespace
        for col in ["PLAN","MRR_MOVEMENT_TYPE","CHURN_STAGE","PLATFORM",
                    "DEPTH_BUCKET","DURATION_BUCKET","FEATURE_NAME","NPS_CATEGORY",
                    "ENTRY_PAGE","EXIT_PAGE","LAST_FEATURE_USED","COUNTRY"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()
        return df
    return {
        "users":     read("dim_users_export.csv"),
        "mrr":       read("fct_mrr_export.csv"),
        "churn":     read("fct_churn_export.csv"),
        "retention": read("fct_retention_export.csv"),
        "sessions":  read("fct_sessions_agg.csv"),
        "features":  read("fct_feature_usage_agg.csv"),
        "payments":  read("payments_export.csv"),
    }

try:
    D = load_all()
except FileNotFoundError as e:
    st.error(f"Missing CSV: {e}")
    st.info("Export from Snowflake and save CSVs to data/exports/")
    st.stop()

# ─────────────────────────────────────────────
# FILTER HELPERS
# ─────────────────────────────────────────────
def fp(df, plans, col="PLAN"):
    return df[df[col].isin([p.upper() for p in plans])]

def fy(df, years, col):
    if col not in df.columns or not years: return df
    return df[df[col].isin(years)]

def fmo(df, months, col):
    if col not in df.columns or not months: return df
    return df[df[col].isin(months)]

def fu(df,p,y,m):  return fmo(fy(fp(df,p),y,"SIGNUP_YEAR"),m,"SIGNUP_MONTH_NUM")
def fm(df,p,y,m):  return fmo(fy(fp(df,p),y,"MRR_YEAR"),m,"MRR_MONTH_NUM")
def fc(df,p,y,m):  return fmo(fy(fp(df,p),y,"CHURN_YEAR"),m,"CHURN_MONTH_NUM")
def fse(df,p,y,m): return fmo(fy(fp(df,p),y,"SESSION_YEAR"),m,"SESSION_MONTH_NUM")
def ff(df,p,y,m):  return fmo(fy(fp(df,p),y,"EVENT_YEAR"),m,"EVENT_MONTH_NUM")

# ─────────────────────────────────────────────
# YoY DELTA
# ─────────────────────────────────────────────
def yoy(curr, prev, invert=False):
    if prev is None or prev == 0: return None, "nt"
    pct = (curr - prev) / abs(prev) * 100
    up = pct >= 0
    if invert: up = not up
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.1f}% vs prev yr", ("up" if up else "dn")

# ─────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────
def kpi_card(label, value, delta=None, ddir="nt", accent=None):
    ac = accent or T
    dh = ""
    if delta:
        arr = "▲" if ddir=="up" else ("▼" if ddir=="dn" else "–")
        dh = f'<div class="kpi-d {ddir}">{arr} {delta}</div>'
    st.markdown(f"""
    <div class="kpi" style="border-top-color:{ac}">
      <div class="kpi-lbl">{label}</div>
      <div class="kpi-val">{value}</div>
      {dh}
    </div>""", unsafe_allow_html=True)

def sh(title):
    st.markdown(f'<div class="sh">{title}</div>', unsafe_allow_html=True)

def ph(title, sub):
    st.markdown(f'<div class="ph"><div class="pt">{title}</div>'
                f'<div class="ps">{sub}</div></div>', unsafe_allow_html=True)

def pills(years, months, plans):
    parts = [f'<span class="pill">📅 {", ".join(str(y) for y in sorted(years))}</span>',
             f'<span class="pill">👤 {", ".join(p.capitalize() for p in sorted(plans))}</span>']
    if months:
        parts.append(f'<span class="pill">🗓 {", ".join(MN[m] for m in sorted(months))}</span>')
    st.markdown("".join(parts), unsafe_allow_html=True)

def fmt_usd(v):
    if pd.isna(v): return "$0"
    if abs(v)>=1e6: return f"${v/1e6:.2f}M"
    if abs(v)>=1e3: return f"${v/1e3:.1f}K"
    return f"${v:,.0f}"

def fmt_n(v):
    if pd.isna(v): return "0"
    if abs(v)>=1e6: return f"{v/1e6:.2f}M"
    if abs(v)>=1e3: return f"{v/1e3:.1f}K"
    return f"{int(v):,}"

CHART_FONT = dict(family="Inter, sans-serif", color=BL, size=12)

def style(fig, h=310):
    """Universal chart styler — dark labels, visible legends."""
    fig.update_layout(
        paper_bgcolor=WH, plot_bgcolor=PB,
        font=CHART_FONT,
        height=h,
        margin=dict(l=10, r=10, t=40, b=50),
        legend=dict(
            font=dict(size=11, color=BL),
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor=BR, borderwidth=1,
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
        ),
        xaxis=dict(
            tickfont=dict(size=11, color=BL),
            title_font=dict(size=12, color=SL),
            gridcolor=BR, linecolor=BR, zeroline=False,
        ),
        yaxis=dict(
            tickfont=dict(size=11, color=BL),
            title_font=dict(size=12, color=SL),
            gridcolor=BR, linecolor=BR, zeroline=False,
        ),
        coloraxis_colorbar=dict(
            tickfont=dict(size=10, color=BL),
            title_font=dict(size=11, color=BL),
        ),
    )
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
all_years = sorted(D["mrr"]["MRR_YEAR"].dropna().unique().astype(int).tolist())

with st.sidebar:
    st.markdown(f"""
    <div style="padding:16px 0 20px;">
      <div style="font-size:1.15rem;font-weight:700;color:white;letter-spacing:-0.02em;">
        📊 SaaS Analytics
      </div>
      <div style="font-size:0.66rem;color:#80CBC4;margin-top:3px;letter-spacing:0.04em;">
        dbt · Snowflake · Streamlit
      </div>
    </div>
    <hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin-bottom:14px;">
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:0.66rem;font-weight:700;letter-spacing:0.1em;'
                'color:#80CBC4;text-transform:uppercase;margin-bottom:8px;">Filters</div>',
                unsafe_allow_html=True)

    year_sel = st.multiselect("YEAR", options=all_years, default=[max(all_years)])
    if not year_sel: year_sel = [max(all_years)]

    mo_lbls  = st.multiselect("MONTH (optional)", options=list(MN.values()), default=[])
    mo_sel   = [k for k,v in MN.items() if v in mo_lbls]

    plan_sel = st.multiselect("PLAN", ["free","pro","enterprise"],
                              default=["free","pro","enterprise"])
    if not plan_sel: plan_sel = ["free","pro","enterprise"]

    prev_y = sorted(set(y-1 for y in year_sel))

    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.1);margin:12px 0;'>",
                unsafe_allow_html=True)
    yc = ", ".join(str(y) for y in sorted(year_sel))
    yp = ", ".join(str(y) for y in sorted(prev_y)) if prev_y else "—"
    st.markdown(f"""
    <div style="background:rgba(0,188,212,0.12);border-radius:8px;padding:10px 12px;">
      <div style="font-size:0.6rem;font-weight:700;color:#80CBC4;letter-spacing:0.08em;
                  text-transform:uppercase;margin-bottom:4px;">YoY Comparison</div>
      <div style="font-size:0.85rem;color:white;font-weight:600;">{yc}</div>
      <div style="font-size:0.71rem;color:#80CBC4;">vs {yp}</div>
    </div>
    <div style="font-size:0.6rem;color:#456269;text-align:center;margin-top:14px;">
      Snapshot · Snowflake marts
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 4 STATIC TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏠  Overview & Revenue",
    "📉  Churn & Retention",
    "👥  Engagement & Features",
    "ℹ️  About",
])

# ═════════════════════════════════════════════
# TAB 1 — OVERVIEW & REVENUE
# ═════════════════════════════════════════════
with tab1:
    ph("Overview & Revenue", "Users, signups, MRR movements and payment performance")
    pills(year_sel, mo_sel, plan_sel)

    u_c = fu(D["users"], plan_sel, year_sel, mo_sel)
    u_p = fu(D["users"], plan_sel, prev_y,   mo_sel)
    m_c = fm(D["mrr"],   plan_sel, year_sel, mo_sel)
    m_p = fm(D["mrr"],   plan_sel, prev_y,   mo_sel)

    # — User KPIs
    tot   = len(u_c);                    tot_p  = len(u_p) if len(u_p) else None
    paid  = len(u_c[u_c["PLAN"]!="FREE"]); paid_p = len(u_p[u_p["PLAN"]!="FREE"]) if len(u_p) else None
    mrrv  = u_c["MRR"].sum();            mrrv_p = u_p["MRR"].sum() if len(u_p) else None
    chr   = round(u_c["IS_CHURNED"].astype(bool).mean()*100,1) if len(u_c) else 0
    chr_p = round(u_p["IS_CHURNED"].astype(bool).mean()*100,1) if len(u_p) else None
    onb   = round(u_c["ONBOARDING_COMPLETED"].astype(bool).mean()*100,1) if len(u_c) else 0
    onb_p = round(u_p["ONBOARDING_COMPLETED"].astype(bool).mean()*100,1) if len(u_p) else None
    eng   = round(u_c["ENGAGEMENT_SCORE"].mean(),1) if len(u_c) else 0
    eng_p = round(u_p["ENGAGEMENT_SCORE"].mean(),1) if len(u_p) else None

    # — MRR KPIs (movement type already UPPER from load_all)
    def msum(df, t): return df[df["MRR_MOVEMENT_TYPE"]==t]["TOTAL_MRR"].sum()
    tot_mrr  = m_c[m_c["MRR_MOVEMENT_TYPE"]!="NEW_FREE"]["TOTAL_MRR"].sum()
    tot_mrr_p= m_p[m_p["MRR_MOVEMENT_TYPE"]!="NEW_FREE"]["TOTAL_MRR"].sum() if len(m_p) else None
    new_mrr  = msum(m_c,"NEW");          new_mrr_p = msum(m_p,"NEW") if len(m_p) else None
    chu_mrr  = abs(msum(m_c,"CHURN"));   chu_mrr_p = abs(msum(m_p,"CHURN")) if len(m_p) else None
    exp_mrr  = msum(m_c,"EXPANSION");    exp_mrr_p = msum(m_p,"EXPANSION") if len(m_p) else None

    sh("👤  User Metrics")
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    with k1: kpi_card("Total Users",      fmt_n(tot),   *yoy(tot,  tot_p),          TL)
    with k2: kpi_card("Paid Users",       fmt_n(paid),  *yoy(paid, paid_p),          T)
    with k3: kpi_card("MRR (cohort)",     fmt_usd(mrrv),*yoy(mrrv, mrrv_p),          T)
    with k4: kpi_card("Churn Rate",       f"{chr}%",    *yoy(chr,  chr_p,  True),    RD)
    with k5: kpi_card("Onboarding",       f"{onb}%",    *yoy(onb,  onb_p),           GR)
    with k6: kpi_card("Avg Engagement",   str(eng),     *yoy(eng,  eng_p),           OR)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    sh("💰  Revenue Metrics")
    r1,r2,r3,r4 = st.columns(4)
    with r1: kpi_card("Total MRR",     fmt_usd(tot_mrr), *yoy(tot_mrr, tot_mrr_p),        T)
    with r2: kpi_card("New MRR",       fmt_usd(new_mrr), *yoy(new_mrr, new_mrr_p),        GR)
    with r3: kpi_card("Churned MRR",   fmt_usd(chu_mrr), *yoy(chu_mrr, chu_mrr_p, True),  RD)
    with r4: kpi_card("Expansion MRR", fmt_usd(exp_mrr), *yoy(exp_mrr, exp_mrr_p),        TD)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # — Charts row 1
    c1,c2 = st.columns(2)
    with c1:
        sh("User Distribution by Plan")
        pd_ = (u_c.groupby("PLAN")
               .agg(USERS=("USER_ID","count"),MRR=("MRR","sum"))
               .reset_index())
        pd_["LABEL"] = pd_["PLAN"].str.capitalize()
        fig = px.pie(pd_, names="LABEL", values="USERS",
                     color="PLAN", color_discrete_map=PLAN_COLORS, hole=0.52)
        fig.update_traces(textposition="outside", textinfo="percent+label",
                          textfont=dict(size=12, color=BL),
                          marker=dict(line=dict(color="white",width=2)))
        style(fig, 290)

    with c2:
        sh("MRR by Plan")
        fig2 = px.bar(pd_, x="LABEL", y="MRR",
                      color="PLAN", color_discrete_map=PLAN_COLORS,
                      text="MRR")
        fig2.update_traces(texttemplate="$%{text:,.0f}", textposition="outside",
                           textfont=dict(size=11, color=BL))
        fig2.update_layout(showlegend=False, xaxis_title="", yaxis_title="MRR ($)")
        style(fig2, 290)

    sh("📈  User Signups Over Time")
    ua = fp(D["users"], plan_sel).copy()
    ua["MONTH_DT"] = pd.to_datetime(ua["SIGNUP_MONTH"])
    sg = ua.groupby(["MONTH_DT","PLAN"]).size().reset_index(name="USERS").sort_values("MONTH_DT")
    sg["PLAN_LBL"] = sg["PLAN"].str.capitalize()
    fig3 = px.area(sg, x="MONTH_DT", y="USERS", color="PLAN_LBL",
                   color_discrete_map={k.capitalize():v for k,v in {"free":TL,"pro":T,"enterprise":BL}.items()},
                   labels={"USERS":"New Users","MONTH_DT":"","PLAN_LBL":"Plan"})
    for yr in year_sel:
        fig3.add_vrect(x0=f"{yr}-01-01", x1=f"{yr}-12-31",
                       fillcolor=TL, opacity=0.06, line_width=0,
                       annotation_text=str(yr), annotation_position="top left",
                       annotation_font=dict(size=11, color=BL))
    fig3.update_layout(hovermode="x unified")
    style(fig3, 290)

    sh("💹  MRR Movements — Monthly")
    MC = {"NEW":GR,"EXPANSION":TD,"RETAINED":T,"CONTRACTION":OR,"CHURN":RD,"NEW_FREE":"#B0BEC5"}
    ma = fp(D["mrr"], plan_sel).copy()
    ma["MONTH_DATE"] = pd.to_datetime(ma["MONTH_DATE"])
    mg = ma.groupby(["MONTH_DATE","MRR_MOVEMENT_TYPE"]).agg(MRR=("TOTAL_MRR","sum")).reset_index()
    fig4 = px.bar(mg, x="MONTH_DATE", y="MRR", color="MRR_MOVEMENT_TYPE",
                  color_discrete_map=MC, barmode="relative",
                  labels={"MRR":"MRR ($)","MONTH_DATE":"","MRR_MOVEMENT_TYPE":"Movement"})
    for yr in year_sel:
        fig4.add_vrect(x0=f"{yr}-01-01", x1=f"{yr}-12-31",
                       fillcolor=TL, opacity=0.05, line_width=0)
    fig4.update_layout(hovermode="x unified")
    style(fig4, 310)

    c1,c2 = st.columns(2)
    with c1:
        sh("🌍  Top Countries by Users")
        co = (u_c.groupby("COUNTRY").agg(USERS=("USER_ID","count"),MRR=("MRR","sum"))
              .reset_index().sort_values("USERS",ascending=False).head(10))
        fig5 = px.bar(co, x="USERS", y="COUNTRY", orientation="h",
                      color="MRR", color_continuous_scale=["#B2EBF2",TD],
                      labels={"USERS":"Users","COUNTRY":"","MRR":"MRR ($)"})
        fig5.update_layout(yaxis=dict(autorange="reversed"))
        style(fig5, 330)

    with c2:
        sh("💳  Payment Success by Plan")
        pay = D["payments"].copy()
        paid_plans = [p for p in plan_sel if p != "free"]
        pay = pay[pay["PLAN"].isin([p.upper() for p in paid_plans])]
        if len(pay) == 0:
            st.info("ℹ️ No payment rows for selected plans. Free users have no payment records.")
        else:
            for _, row in pay.iterrows():
                tot_ = row["SUCCEEDED"]+row["FAILED"]+row["REFUNDED"]
                rate = round(row["SUCCEEDED"]/tot_*100,1) if tot_ > 0 else 0
                pname = str(row["PLAN"]).capitalize()
                ac = {"free":TL,"pro":T,"enterprise":BL}.get(pname.lower(), T)
                kpi_card(f"{pname} — Payment Success", f"{rate}%",
                         f"${row['REVENUE']:,.0f} collected", "up", ac)
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)


# ═════════════════════════════════════════════
# TAB 2 — CHURN & RETENTION
# ═════════════════════════════════════════════
with tab2:
    ph("Churn & Retention", "Who churns, when, and how well cohorts are retained over time")
    pills(year_sel, mo_sel, plan_sel)

    ch_c = fc(D["churn"], plan_sel, year_sel, mo_sel)
    ch_p = fc(D["churn"], plan_sel, prev_y,   mo_sel)

    def ck(df):
        return {
            "n":   len(df),
            "mrr": df["LOST_MRR"].sum()      if len(df) else 0,
            "d2c": int(df["DAYS_TO_CHURN"].mean()) if len(df) else 0,
            "ses": round(df["TOTAL_SESSIONS"].mean(),1) if len(df) else 0,
            "bnc": round(df["BOUNCE_RATE_PCT"].mean(),1) if len(df) else 0,
        }
    cc = ck(ch_c); cp = ck(ch_p) if len(ch_p) else None

    sh("📉  Churn KPIs")
    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: kpi_card("Churned Users",      fmt_n(cc["n"]),    *yoy(cc["n"],   cp["n"]   if cp else None, True), RD)
    with k2: kpi_card("Lost MRR",           fmt_usd(cc["mrr"]),*yoy(cc["mrr"],cp["mrr"] if cp else None, True), RD)
    with k3: kpi_card("Avg Days to Churn",  f"{cc['d2c']}d",   *yoy(cc["d2c"],cp["d2c"] if cp else None),       OR)
    with k4: kpi_card("Avg Pre-churn Sess", str(cc["ses"]),    *yoy(cc["ses"],cp["ses"] if cp else None),        T)
    with k5: kpi_card("Avg Bounce Rate",    f"{cc['bnc']}%",   *yoy(cc["bnc"],cp["bnc"] if cp else None, True), "#7B1FA2")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        sh("Churn by Stage & Plan")
        cs = (ch_c.groupby(["CHURN_STAGE","PLAN"])
              .agg(USERS=("USER_ID","count")).reset_index())
        cs["PLAN_LBL"] = cs["PLAN"].str.capitalize()
        fig = px.bar(cs, x="CHURN_STAGE", y="USERS", color="PLAN_LBL", barmode="group",
                     color_discrete_map={"Free":TL,"Pro":T,"Enterprise":BL},
                     category_orders={"CHURN_STAGE":["IMMEDIATE","EARLY","MID","LATE"]},
                     labels={"USERS":"Churned Users","CHURN_STAGE":"Stage","PLAN_LBL":"Plan"})
        style(fig, 290)

    with c2:
        sh("NPS of Churned Users")
        nps = (ch_c.dropna(subset=["NPS_CATEGORY"])
               .groupby("NPS_CATEGORY").size().reset_index(name="USERS"))
        NPC = {"DETRACTOR":RD,"PASSIVE":OR,"PROMOTER":GR}
        nps["LBL"] = nps["NPS_CATEGORY"].str.capitalize()
        fig2 = px.pie(nps, names="LBL", values="USERS",
                      color="NPS_CATEGORY", color_discrete_map=NPC, hole=0.5)
        fig2.update_traces(textposition="outside", textinfo="percent+label",
                           textfont=dict(size=12, color=BL))
        style(fig2, 290)

    sh("📊  Churn Trend — Current vs Previous Year")
    ct = fp(D["churn"], plan_sel).copy()
    ct["MONTH_DT"] = pd.to_datetime(ct["CHURNED_AT"]).dt.to_period("M").dt.to_timestamp()
    show_y = sorted(set(year_sel)|set(prev_y))
    ct2 = (ct[ct["CHURN_YEAR"].isin(show_y)]
           .groupby(["MONTH_DT","PLAN","CHURN_YEAR"]).size()
           .reset_index(name="CHURNED").sort_values("MONTH_DT"))
    ct2["PLAN_LBL"] = ct2["PLAN"].str.capitalize()
    ct2["YR_LBL"]   = ct2["CHURN_YEAR"].astype(str)
    fig3 = px.line(ct2, x="MONTH_DT", y="CHURNED", color="PLAN_LBL", line_dash="YR_LBL",
                   color_discrete_map={"Free":TL,"Pro":T,"Enterprise":BL},
                   markers=True,
                   labels={"CHURNED":"Churned Users","MONTH_DT":"","PLAN_LBL":"Plan","YR_LBL":"Year"})
    fig3.update_layout(hovermode="x unified")
    style(fig3, 290)

    c1,c2 = st.columns(2)
    with c1:
        sh("Last Feature Used Before Churn")
        lf = (ch_c.dropna(subset=["LAST_FEATURE_USED"])
              .groupby("LAST_FEATURE_USED").size()
              .reset_index(name="USERS").sort_values("USERS",ascending=False).head(10))
        fig4 = px.bar(lf, x="USERS", y="LAST_FEATURE_USED", orientation="h",
                      color_discrete_sequence=[RD],
                      labels={"USERS":"Churned Users","LAST_FEATURE_USED":""})
        fig4.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
        style(fig4, 300)

    with c2:
        sh("Lost MRR by Stage")
        sm = (ch_c.groupby("CHURN_STAGE")["LOST_MRR"].sum()
              .reset_index().sort_values("LOST_MRR",ascending=False))
        fig5 = px.bar(sm, x="CHURN_STAGE", y="LOST_MRR",
                      color="CHURN_STAGE",
                      color_discrete_sequence=[RD,OR,T,BL],
                      text="LOST_MRR",
                      labels={"LOST_MRR":"Lost MRR ($)","CHURN_STAGE":""})
        fig5.update_traces(texttemplate="$%{text:,.0f}", textposition="outside",
                           textfont=dict(size=11,color=BL))
        fig5.update_layout(showlegend=False)
        style(fig5, 300)

    # ── RETENTION section
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    sh("🔁  Cohort Retention")

    ret = D["retention"].copy()
    ret = fy(ret, year_sel, "COHORT_YEAR")
    ret["COHORT_MONTH"] = pd.to_datetime(ret["COHORT_MONTH"]).dt.strftime("%Y-%m")

    pv = ret.pivot(index="COHORT_MONTH", columns="MONTHS_SINCE_SIGNUP", values="RETENTION_PCT")
    fig6 = px.imshow(pv,
                     color_continuous_scale=["#FFEBEE","#E0F7FA",TD],
                     labels=dict(x="Months Since Signup", y="Cohort", color="Retention %"),
                     zmin=0, zmax=100, aspect="auto", text_auto=".0f")
    fig6.update_traces(textfont=dict(size=9, color=BL))
    fig6.update_layout(
        height=400,
        xaxis=dict(tickfont=dict(size=11,color=BL),title_font=dict(size=12,color=SL)),
        yaxis=dict(tickfont=dict(size=11,color=BL),title_font=dict(size=12,color=SL)),
        coloraxis_colorbar=dict(tickfont=dict(size=10,color=BL),title="Ret %"),
        margin=dict(l=10,r=10,t=40,b=50),
        paper_bgcolor=WH, plot_bgcolor=PB, font=CHART_FONT,
    )
    st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar":False})

    c1,c2 = st.columns(2)
    with c1:
        sh("Retention Curves — Top 6 Cohorts")
        top_c = ret.groupby("COHORT_MONTH")["ACTIVE_USERS"].sum().nlargest(6).index.tolist()
        fig7 = px.line(ret[ret["COHORT_MONTH"].isin(top_c)],
                       x="MONTHS_SINCE_SIGNUP", y="RETENTION_PCT", color="COHORT_MONTH",
                       markers=True,
                       labels={"RETENTION_PCT":"Retention %","MONTHS_SINCE_SIGNUP":"Months Since Signup"})
        fig7.update_layout(yaxis_range=[0,105])
        style(fig7, 290)

    with c2:
        sh("Avg Retention at Key Milestones")
        sa = ret[ret["MONTHS_SINCE_SIGNUP"].isin([1,3,6,12])].copy()
        sa = sa.groupby("MONTHS_SINCE_SIGNUP")["RETENTION_PCT"].mean().reset_index()
        sa.columns = ["MONTH","AVG_RET"]
        sa["AVG_RET"] = sa["AVG_RET"].round(1)
        sa["LBL"] = sa["MONTH"].apply(lambda m: f"Mo {m}")
        fig8 = px.bar(sa, x="LBL", y="AVG_RET",
                      color="AVG_RET",
                      color_continuous_scale=[RD,TL,TD],
                      text="AVG_RET",
                      labels={"AVG_RET":"Retention %","LBL":""})
        fig8.update_traces(texttemplate="%{text}%", textposition="outside",
                           textfont=dict(size=12,color=BL))
        fig8.update_layout(showlegend=False, yaxis_range=[0,115],
                           coloraxis_showscale=False)
        style(fig8, 290)


# ═════════════════════════════════════════════
# TAB 3 — ENGAGEMENT & FEATURES
# ═════════════════════════════════════════════
with tab3:
    ph("Engagement & Features", "Session behaviour, feature adoption and platform breakdown")
    pills(year_sel, mo_sel, plan_sel)

    se_c = fse(D["sessions"], plan_sel, year_sel, mo_sel)
    se_p = fse(D["sessions"], plan_sel, prev_y,   mo_sel)
    ft_c = ff(D["features"],  plan_sel, year_sel, mo_sel)
    ft_p = ff(D["features"],  plan_sel, prev_y,   mo_sel)

    # Session KPIs
    ts    = se_c["SESSIONS"].sum();    ts_p  = se_p["SESSIONS"].sum() if len(se_p) else None
    bc    = se_c["BOUNCE_COUNT"].sum(); bc_p  = se_p["BOUNCE_COUNT"].sum() if len(se_p) else None
    bnc   = round(bc/ts*100,1) if ts else 0
    bnc_p = round(bc_p/ts_p*100,1) if ts_p else None
    dur   = round(se_c["AVG_DURATION_MIN"].mean(),1) if len(se_c) else 0
    pgs   = round(se_c["AVG_PAGES"].mean(),1) if len(se_c) else 0
    fts_v = round(se_c["AVG_FEATURES"].mean(),1) if len(se_c) else 0
    # Feature KPIs
    te    = ft_c["EVENTS"].sum();      te_p  = ft_p["EVENTS"].sum() if len(ft_p) else None
    ud    = ft_c["UNIQUE_USERS"].sum(); ud_p  = ft_p["UNIQUE_USERS"].sum() if len(ft_p) else None

    sh("👥  Session KPIs")
    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: kpi_card("Total Sessions",      fmt_n(ts),     *yoy(ts,   ts_p),        BL)
    with k2: kpi_card("Avg Duration",        f"{dur} min",  None, "nt",              T)
    with k3: kpi_card("Avg Pages / Session", str(pgs),      None, "nt",              TL)
    with k4: kpi_card("Avg Features / Sess", str(fts_v),    None, "nt",              TD)
    with k5: kpi_card("Bounce Rate",         f"{bnc}%",     *yoy(bnc, bnc_p, True),  RD)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    sh("🔧  Feature KPIs")
    f1,f2,f3,f4 = st.columns(4)
    with f1: kpi_card("Total Feature Events", fmt_n(te),    *yoy(te, te_p),  BL)
    with f2: kpi_card("Unique User-Days",     fmt_n(ud),    *yoy(ud, ud_p),  T)
    with f3: kpi_card("Distinct Features",    str(ft_c["FEATURE_NAME"].nunique()), None,"nt", TL)
    with f4: kpi_card("Avg Duration",         f"{round(ft_c['AVG_DURATION_SEC'].mean(),1)}s", None,"nt", TD)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        sh("Sessions by Platform")
        pl = se_c.groupby(["PLATFORM","PLAN"])["SESSIONS"].sum().reset_index()
        pl["PLAN_LBL"] = pl["PLAN"].str.capitalize()
        fig = px.bar(pl, x="PLATFORM", y="SESSIONS", color="PLAN_LBL", barmode="group",
                     color_discrete_map={"Free":TL,"Pro":T,"Enterprise":BL},
                     labels={"SESSIONS":"Sessions","PLATFORM":"","PLAN_LBL":"Plan"})
        style(fig, 270)

    with c2:
        sh("Session Depth Distribution")
        dp = se_c.groupby("DEPTH_BUCKET")["SESSIONS"].sum().reset_index()
        od = ["1 PAGE (BOUNCE)","2-3 PAGES","4-7 PAGES","8+ PAGES (DEEP)"]
        fig2 = px.bar(dp, x="DEPTH_BUCKET", y="SESSIONS",
                      color_discrete_sequence=[T],
                      category_orders={"DEPTH_BUCKET":od},
                      labels={"SESSIONS":"Sessions","DEPTH_BUCKET":""})
        fig2.update_layout(showlegend=False)
        style(fig2, 270)

    sh("Session Duration by Plan")
    da = se_c.groupby(["DURATION_BUCKET","PLAN"])["SESSIONS"].sum().reset_index()
    da["PLAN_LBL"] = da["PLAN"].str.capitalize()
    od2 = ["< 1 MIN","1-5 MIN","5-15 MIN","15-60 MIN","1HR+"]
    fig3 = px.bar(da, x="DURATION_BUCKET", y="SESSIONS", color="PLAN_LBL", barmode="group",
                  color_discrete_map={"Free":TL,"Pro":T,"Enterprise":BL},
                  category_orders={"DURATION_BUCKET":od2},
                  labels={"SESSIONS":"Sessions","DURATION_BUCKET":"","PLAN_LBL":"Plan"})
    fig3.update_layout(hovermode="x unified")
    style(fig3, 270)

    c1,c2 = st.columns(2)
    with c1:
        sh("Top Entry Pages")
        ep = (se_c.groupby("ENTRY_PAGE")["SESSIONS"].sum()
              .reset_index().sort_values("SESSIONS",ascending=False).head(10))
        fig4 = px.bar(ep, x="SESSIONS", y="ENTRY_PAGE", orientation="h",
                      color_discrete_sequence=[T],
                      labels={"SESSIONS":"Sessions","ENTRY_PAGE":""})
        fig4.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
        style(fig4, 290)

    with c2:
        sh("Top Exit Pages")
        xp = (se_c.groupby("EXIT_PAGE")["SESSIONS"].sum()
              .reset_index().sort_values("SESSIONS",ascending=False).head(10))
        fig5 = px.bar(xp, x="SESSIONS", y="EXIT_PAGE", orientation="h",
                      color_discrete_sequence=[RD],
                      labels={"SESSIONS":"Sessions","EXIT_PAGE":""})
        fig5.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
        style(fig5, 290)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    sh("🔧  Feature Usage by Plan")
    fa = (ft_c.groupby(["FEATURE_NAME","PLAN"])
          .agg(EVENTS=("EVENTS","sum"),UNIQUE_USERS=("UNIQUE_USERS","sum")).reset_index())
    fa["PLAN_LBL"] = fa["PLAN"].str.capitalize()
    c1,c2 = st.columns(2)
    with c1:
        fig6 = px.bar(fa, x="FEATURE_NAME", y="EVENTS", color="PLAN_LBL", barmode="group",
                      color_discrete_map={"Free":TL,"Pro":T,"Enterprise":BL},
                      labels={"EVENTS":"Total Events","FEATURE_NAME":"","PLAN_LBL":"Plan"})
        fig6.update_layout(xaxis_tickangle=-35)
        style(fig6, 290)

    with c2:
        fig7 = px.bar(fa, x="FEATURE_NAME", y="UNIQUE_USERS", color="PLAN_LBL", barmode="group",
                      color_discrete_map={"Free":TL,"Pro":T,"Enterprise":BL},
                      labels={"UNIQUE_USERS":"Unique Users","FEATURE_NAME":"","PLAN_LBL":"Plan"})
        fig7.update_layout(xaxis_tickangle=-35)
        style(fig7, 290)

    sh("Feature Usage Trend — Top 5")
    ft_tr = ft_c.groupby(["EVENT_MONTH","FEATURE_NAME"])["EVENTS"].sum().reset_index()
    ft_tr["EVENT_MONTH"] = pd.to_datetime(ft_tr["EVENT_MONTH"])
    top5 = ft_tr.groupby("FEATURE_NAME")["EVENTS"].sum().nlargest(5).index.tolist()
    fig8 = px.line(ft_tr[ft_tr["FEATURE_NAME"].isin(top5)],
                   x="EVENT_MONTH", y="EVENTS", color="FEATURE_NAME", markers=True,
                   labels={"EVENTS":"Events","EVENT_MONTH":"","FEATURE_NAME":"Feature"})
    fig8.update_layout(hovermode="x unified")
    style(fig8, 290)

    sh("Feature × Platform Heatmap")
    fph = ft_c.groupby(["FEATURE_NAME","PLATFORM"])["EVENTS"].sum().reset_index()
    pvh = fph.pivot(index="FEATURE_NAME", columns="PLATFORM", values="EVENTS").fillna(0)
    fig9 = px.imshow(pvh, color_continuous_scale=["#E0F7FA",TD],
                     labels=dict(color="Events"), aspect="auto", text_auto=".0f")
    fig9.update_traces(textfont=dict(size=10, color=BL))
    fig9.update_layout(
        height=330,
        xaxis=dict(tickfont=dict(size=11,color=BL),title=""),
        yaxis=dict(tickfont=dict(size=11,color=BL),title=""),
        coloraxis_colorbar=dict(title="Events",tickfont=dict(size=10,color=BL)),
        margin=dict(l=10,r=10,t=40,b=50),
        paper_bgcolor=WH, plot_bgcolor=PB, font=CHART_FONT,
    )
    st.plotly_chart(fig9, use_container_width=True, config={"displayModeBar":False})


# ═════════════════════════════════════════════
# TAB 4 — ABOUT
# ═════════════════════════════════════════════
with tab4:
    ph("About This Dashboard", "Architecture, data sources, and tech stack")

    st.markdown(f"""
    <div style="background:white;border-radius:12px;padding:26px 30px;
                box-shadow:0 1px 5px rgba(0,0,0,0.07);margin-bottom:14px;">
      <div style="font-size:1rem;font-weight:700;color:{BL};margin-bottom:16px;">🏗 Tech Stack</div>
      <table style="width:100%;border-collapse:collapse;font-size:0.86rem;">
        <tr style="border-bottom:1px solid {BR};">
          <td style="padding:9px 0;color:{MU};font-weight:600;width:160px;">Data Generation</td>
          <td style="padding:9px 0;color:{BL};">Python · Synthetic B2B SaaS dataset (~45M rows)</td>
        </tr>
        <tr style="border-bottom:1px solid {BR};">
          <td style="padding:9px 0;color:{MU};font-weight:600;">Data Warehouse</td>
          <td style="padding:9px 0;color:{BL};">Snowflake · Raw → Staging → Mart layers</td>
        </tr>
        <tr style="border-bottom:1px solid {BR};">
          <td style="padding:9px 0;color:{MU};font-weight:600;">Transformation</td>
          <td style="padding:9px 0;color:{BL};">dbt · 16 models · 8 staging + 2 intermediate + 6 mart tables · 39 tests</td>
        </tr>
        <tr style="border-bottom:1px solid {BR};">
          <td style="padding:9px 0;color:{MU};font-weight:600;">Dashboard</td>
          <td style="padding:9px 0;color:{BL};">Streamlit + Plotly · Reads 7 pre-exported CSVs (no live DB connection)</td>
        </tr>
        <tr>
          <td style="padding:9px 0;color:{MU};font-weight:600;">Deployment</td>
          <td style="padding:9px 0;color:{BL};">Streamlit Cloud · Auto-redeploys on every git push</td>
        </tr>
      </table>
    </div>

    <div style="background:white;border-radius:12px;padding:26px 30px;
                box-shadow:0 1px 5px rgba(0,0,0,0.07);">
      <div style="font-size:1rem;font-weight:700;color:{BL};margin-bottom:16px;">📁 Data Files (7 CSVs)</div>
      <table style="width:100%;border-collapse:collapse;font-size:0.84rem;">
        <thead>
          <tr style="border-bottom:2px solid {T};">
            <th style="padding:8px 0;text-align:left;color:{MU};font-weight:600;">File</th>
            <th style="padding:8px 0;text-align:left;color:{MU};font-weight:600;">~Rows</th>
            <th style="padding:8px 0;text-align:left;color:{MU};font-weight:600;">Used in</th>
          </tr>
        </thead>
        <tbody>
          <tr style="border-bottom:1px solid {BR};"><td style="padding:7px 0;font-family:monospace;font-size:0.78rem;">dim_users_export.csv</td><td style="padding:7px 0;color:{MU};">40,000</td><td style="padding:7px 0;color:{MU};">Overview & Revenue</td></tr>
          <tr style="border-bottom:1px solid {BR};"><td style="padding:7px 0;font-family:monospace;font-size:0.78rem;">fct_mrr_export.csv</td><td style="padding:7px 0;color:{MU};">1,998</td><td style="padding:7px 0;color:{MU};">Overview & Revenue</td></tr>
          <tr style="border-bottom:1px solid {BR};"><td style="padding:7px 0;font-family:monospace;font-size:0.78rem;">fct_churn_export.csv</td><td style="padding:7px 0;color:{MU};">11,751</td><td style="padding:7px 0;color:{MU};">Churn & Retention</td></tr>
          <tr style="border-bottom:1px solid {BR};"><td style="padding:7px 0;font-family:monospace;font-size:0.78rem;">fct_retention_export.csv</td><td style="padding:7px 0;color:{MU};">600</td><td style="padding:7px 0;color:{MU};">Churn & Retention</td></tr>
          <tr style="border-bottom:1px solid {BR};"><td style="padding:7px 0;font-family:monospace;font-size:0.78rem;">fct_sessions_agg.csv</td><td style="padding:7px 0;color:{MU};">3,500</td><td style="padding:7px 0;color:{MU};">Engagement & Features</td></tr>
          <tr style="border-bottom:1px solid {BR};"><td style="padding:7px 0;font-family:monospace;font-size:0.78rem;">fct_feature_usage_agg.csv</td><td style="padding:7px 0;color:{MU};">4,320</td><td style="padding:7px 0;color:{MU};">Engagement & Features</td></tr>
          <tr><td style="padding:7px 0;font-family:monospace;font-size:0.78rem;">payments_export.csv</td><td style="padding:7px 0;color:{MU};">2</td><td style="padding:7px 0;color:{MU};">Overview & Revenue</td></tr>
        </tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)