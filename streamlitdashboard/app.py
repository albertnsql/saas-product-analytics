"""
SaaS Analytics Dashboard — 4 pages, static sidebar nav, no debug panel
MRR FIX: fct_mrr.sql exports CHURNED_MRR and EXPANSION_MRR as dedicated columns.
         For churn rows: total_mrr=0, mrr_change<0 → use CHURNED_MRR / EXPANSION_MRR directly.
         If those columns don't exist, fall back to NET_MRR_CHANGE.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import os, warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="SaaS Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Colour tokens ─────────────────────────────────────
SB  = "#1E3A5F"
MID = "#2E6DA4"
ACC = "#00B4D8"
GRN = "#2ECC71"
RED = "#E74C3C"
ORG = "#F39C12"
PUR = "#8E44AD"
BG  = "#F0F4F8"
WH  = "#FFFFFF"
MU  = "#6B8CAE"
BR  = "#E4EAF0"
PLT = "#F8FAFC"

PC  = {"Free": ACC, "Pro": MID, "Enterprise": SB}
PCU = {"FREE": ACC, "PRO": MID, "ENTERPRISE": SB}
MN  = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
       7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

# 4 pages: Overview | Revenue & MRR | Churn & Engagement | Retention & Features
PAGES = ["Overview", "Revenue & MRR", "Churn & Engagement", "Retention & Features"]
PICO  = {"Overview":"🏠", "Revenue & MRR":"💰",
         "Churn & Engagement":"📉", "Retention & Features":"🔁"}

if "page" not in st.session_state:
    st.session_state.page = "Overview"

# ══════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{{font-family:'Inter','Segoe UI',sans-serif!important;}}
.stApp{{background:{BG}!important;}}

/* ── sidebar shell ── */
section[data-testid="stSidebar"]{{
  background:{SB}!important;
  width:220px!important;min-width:220px!important;
  border-right:1px solid rgba(255,255,255,0.07)!important;
}}
section[data-testid="stSidebar"]>div:first-child{{padding:0!important;overflow-x:hidden!important;}}
section[data-testid="stSidebar"] .block-container{{padding:0!important;}}

/* ── sidebar buttons as nav rows ── */
section[data-testid="stSidebar"] .stButton{{margin:0!important;padding:0!important;}}
section[data-testid="stSidebar"] .stButton button{{
  width:100%!important; text-align:left!important;
  background:transparent!important; border:none!important;
  border-left:3px solid transparent!important; border-radius:0!important;
  padding:10px 20px!important; font-size:12.5px!important; font-weight:600!important;
  color:#A8C8E8!important; box-shadow:none!important;
  transition:background 0.15s,color 0.15s!important;
}}
section[data-testid="stSidebar"] .stButton button:hover{{
  background:rgba(255,255,255,0.06)!important; color:white!important;
  border-left:3px solid rgba(0,180,216,0.5)!important;
}}
section[data-testid="stSidebar"] .stButton button:focus{{
  outline:none!important; box-shadow:none!important;
}}

/* ── sidebar multiselects ── */
section[data-testid="stSidebar"] .element-container{{margin:0!important;padding:0!important;}}
section[data-testid="stSidebar"] .stMarkdown{{margin:0!important;padding:0!important;}}
section[data-testid="stSidebar"] [data-testid="stMultiSelect"]>label{{display:none!important;}}
section[data-testid="stSidebar"] [data-testid="stMultiSelect"] div[data-baseweb="select"]>div{{
  background:rgba(255,255,255,0.07)!important;
  border:1px solid rgba(255,255,255,0.15)!important;
  border-radius:7px!important; min-height:32px!important;
}}
section[data-testid="stSidebar"] [data-testid="stMultiSelect"] span[data-baseweb="tag"]{{
  background:{ACC}!important; color:white!important;
  border-radius:10px!important; font-size:11px!important; font-weight:700!important;
}}
section[data-testid="stSidebar"] [data-testid="stMultiSelect"] input{{color:#C8DDF0!important;font-size:11px!important;}}
section[data-testid="stSidebar"] [data-testid="stMultiSelect"] svg{{fill:#7EB8D8!important;}}

/* ── sidebar checkboxes ── */
section[data-testid="stSidebar"] [data-testid="stCheckbox"]{{padding:3px 20px!important;}}
section[data-testid="stSidebar"] [data-testid="stCheckbox"] label,
section[data-testid="stSidebar"] [data-testid="stCheckbox"] label span{{
  font-size:12px!important; font-weight:600!important; color:#C8DDF0!important;
}}

/* ── main page header ── */
.ptitle{{font-size:1.55rem;font-weight:800;color:{SB};letter-spacing:-0.03em;line-height:1.1;}}
.psub{{font-size:12px;color:{MU};margin-top:3px;margin-bottom:14px;}}

/* ── filter pills ── */
.fpill{{
  display:inline-block;background:rgba(0,180,216,0.12);color:{SB};
  border-radius:20px;padding:3px 10px;font-size:10px;font-weight:600;
  margin-right:4px;margin-bottom:12px;
}}

/* ── KPI card ── */
.kcard{{
  background:{WH};border-radius:10px;padding:14px 16px 12px;
  border-left:4px solid {ACC};
  box-shadow:0 2px 10px rgba(0,0,0,0.07);
  height:104px;display:flex;flex-direction:column;
  justify-content:space-between;overflow:hidden;
}}
.klbl{{font-size:9px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{MU};
       white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.kval{{font-size:1.42rem;font-weight:800;color:{SB};line-height:1;
       white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.kdelta{{font-size:10px;font-weight:600;margin-top:3px;}}
.kdelta.up{{color:{GRN};}} .kdelta.dn{{color:{RED};}} .kdelta.nt{{color:{MU};}}

/* ── section header ── */
.sec{{
  font-size:13px;font-weight:700;color:{SB};
  margin:22px 0 10px;padding-bottom:6px;
  border-bottom:2px solid {ACC};
}}

/* ── chart container card ── */
.chart-card{{
  background:{WH};border-radius:10px;
  padding:16px 16px 4px;
  box-shadow:0 2px 8px rgba(0,0,0,0.05);
  margin-bottom:4px;
}}

/* ── tighten bar gaps ── */
.js-plotly-plot .plotly .barlayer .point path{{shape-rendering:crispEdges;}}

/* ── layout ── */
#MainMenu,footer,header{{visibility:hidden;}}
.block-container{{padding:1.6rem 2rem 3rem!important;max-width:100%!important;}}
div[data-testid="stHorizontalBlock"]{{gap:14px!important;}}
</style>
""", unsafe_allow_html=True)

# ── Active nav button CSS (injected per-render) ───────
def inject_active_nav(active_page):
    idx = PAGES.index(active_page)
    st.markdown(f"""
    <style>
    section[data-testid="stSidebar"] .stButton:nth-of-type({idx+1}) button{{
      background:rgba(0,180,216,0.18)!important;
      border-left:3px solid {ACC}!important;
      color:white!important;
    }}
    </style>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════
#DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "exports")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "exports")

@st.cache_data
def load_all():
    def rd(f):
        df = pd.read_csv(os.path.join(DATA_DIR, f))
        df.columns = [c.upper() for c in df.columns]
        for c in ["PLAN","MRR_MOVEMENT_TYPE","CHURN_STAGE","PLATFORM",
                  "DEPTH_BUCKET","DURATION_BUCKET","FEATURE_NAME",
                  "NPS_CATEGORY","ENTRY_PAGE","EXIT_PAGE","COUNTRY"]:
            if c in df.columns:
                df[c] = df[c].astype(str).str.strip().str.upper()
        return df
    D = {
        "users":     rd("dim_users_export.csv"),
        "mrr":       rd("fct_mrr_export.csv"),
        "churn":     rd("fct_churn_export.csv"),
        "retention": rd("fct_retention_export.csv"),
        "sessions":  rd("fct_sessions_agg.csv"),
        "features":  rd("fct_feature_usage_agg.csv"),
        "payments":  rd("payments_export.csv"),
    }
    # Numeric coerce all MRR columns
    for col in ["TOTAL_MRR","NET_MRR_CHANGE","NEW_MRR","EXPANSION_MRR",
                "CONTRACTION_MRR","CHURNED_MRR","RETAINED_MRR"]:
        if col in D["mrr"].columns:
            D["mrr"][col] = pd.to_numeric(D["mrr"][col], errors="coerce").fillna(0)
    return D

try:
    D = load_all()
except FileNotFoundError as e:
    st.error(f"❌ Missing CSV: {e}"); st.stop()

# Detect which MRR columns are available
_mc = D["mrr"].columns.tolist()
HAS_DEDICATED = "CHURNED_MRR" in _mc  # fct_mrr has dedicated pre-agg columns
HAS_NET       = "NET_MRR_CHANGE" in _mc
ALL_YEARS     = sorted(D["mrr"]["MRR_YEAR"].dropna().unique().astype(int).tolist())

# ══════════════════════════════════════════════════════
# MRR helpers — use dedicated columns when available
# ══════════════════════════════════════════════════════
def _sum_mrr_col(df, col):
    return df[col].sum() if col in df.columns else 0

def total_mrr(df):
    # Sum of new + expansion + retained (positive movements)
    if "NEW_MRR" in df.columns:
        return (_sum_mrr_col(df,"NEW_MRR") +
                _sum_mrr_col(df,"EXPANSION_MRR") +
                _sum_mrr_col(df,"RETAINED_MRR"))
    # Fallback: filter rows
    return df[df["MRR_MOVEMENT_TYPE"].isin(["NEW","EXPANSION","RETAINED"])]["TOTAL_MRR"].sum()

def churned_mrr(df):
    if HAS_DEDICATED:
        # CHURNED_MRR is negative (mrr_change for churn rows)  → abs()
        return abs(_sum_mrr_col(df, "CHURNED_MRR"))
    if HAS_NET:
        rows = df[df["MRR_MOVEMENT_TYPE"]=="CHURN"]
        return abs(rows["NET_MRR_CHANGE"].sum())
    return 0

def expansion_mrr(df):
    if HAS_DEDICATED:
        return _sum_mrr_col(df, "EXPANSION_MRR")
    if HAS_NET:
        rows = df[df["MRR_MOVEMENT_TYPE"]=="EXPANSION"]
        return rows["NET_MRR_CHANGE"].sum()
    return 0

def new_mrr(df):
    if "NEW_MRR" in df.columns:
        return _sum_mrr_col(df, "NEW_MRR")
    rows = df[df["MRR_MOVEMENT_TYPE"]=="NEW"]
    return rows["TOTAL_MRR"].sum()

# ══════════════════════════════════════════════════════
# Filter helpers
# ══════════════════════════════════════════════════════
def fp(df,p):    return df[df["PLAN"].isin([x.upper() for x in p])]
def fy(df,y,c):  return df if not y or c not in df.columns else df[df[c].isin(y)]
def fm(df,m,c):  return df if not m or c not in df.columns else df[df[c].isin(m)]
def fu(df,p,y,mo):  return fm(fy(fp(df,p),y,"SIGNUP_YEAR"), mo,"SIGNUP_MONTH_NUM")
def fmr(df,p,y,mo): return fm(fy(fp(df,p),y,"MRR_YEAR"),    mo,"MRR_MONTH_NUM")
def fch(df,p,y,mo): return fm(fy(fp(df,p),y,"CHURN_YEAR"),  mo,"CHURN_MONTH_NUM")
def fse(df,p,y,mo): return fm(fy(fp(df,p),y,"SESSION_YEAR"),mo,"SESSION_MONTH_NUM")
def ffe(df,p,y,mo): return fm(fy(fp(df,p),y,"EVENT_YEAR"),  mo,"EVENT_MONTH_NUM")

def yoy(c, p, inv=False):
    if p is None or p == 0: return None,"nt"
    pct = (c-p)/abs(p)*100
    up  = (pct>=0) if not inv else (pct<0)
    return f"{'+'if pct>=0 else''}{pct:.1f}% vs prev year", "up" if up else "dn"

def fd(v):
    if pd.isna(v) or v==0: return "$0"
    if abs(v)>=1e6: return f"${v/1e6:.2f}M"
    if abs(v)>=1e3: return f"${v/1e3:.1f}K"
    return f"${v:,.0f}"
def fn(v):
    if pd.isna(v): return "0"
    if abs(v)>=1e6: return f"{v/1e6:.2f}M"
    if abs(v)>=1e3: return f"{v/1e3:.1f}K"
    return f"{int(v):,}"

# ══════════════════════════════════════════════════════
# UI helpers
# ══════════════════════════════════════════════════════
def kpi(label, value, delta=None, ddir="nt", acc=None):
    a  = acc or ACC
    dh = ""
    if delta:
        arr = "▲" if ddir=="up" else ("▼" if ddir=="dn" else "–")
        dh  = f'<div class="kdelta {ddir}">{arr} {delta}</div>'
    st.markdown(
        f'<div class="kcard" style="border-left-color:{a}">'
        f'<div class="klbl">{label}</div>'
        f'<div class="kval">{value}</div>{dh}</div>',
        unsafe_allow_html=True)

def sec(t):
    st.markdown(f'<div class="sec">{t}</div>', unsafe_allow_html=True)

def pills(years, months, plans):
    mo = ", ".join(MN[m] for m in sorted(months)) if months else "All months"
    st.markdown(
        f'<div style="margin-bottom:12px;">'
        f'<span class="fpill">Plans: {", ".join(p.capitalize() for p in sorted(plans))}</span>'
        f'<span class="fpill">Years: {", ".join(str(y) for y in sorted(years))}</span>'
        f'<span class="fpill">Months: {mo}</span></div>',
        unsafe_allow_html=True)

CFONT = dict(family="Inter,Segoe UI,sans-serif", color=SB, size=11)
HL    = dict(bgcolor=WH, font=dict(family="Inter",size=12,color=SB), bordercolor=BR, namelength=-1)

def rs(fig, h=300, unified=True, bar_gap=0.15):
    fig.update_layout(
        paper_bgcolor=WH, plot_bgcolor=PLT, font=CFONT, height=h,
        margin=dict(l=6,r=6,t=38,b=48),
        hovermode="x unified" if unified else "closest", hoverlabel=HL,
        bargap=bar_gap, bargroupgap=0.05,
        legend=dict(font=dict(size=11,color=SB), bgcolor="rgba(255,255,255,0.95)",
                    bordercolor=BR, borderwidth=1, orientation="h",
                    yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(tickfont=dict(size=10,color=SB), title_font=dict(size=11,color=MU),
                   gridcolor=BR, linecolor=BR, zeroline=False),
        yaxis=dict(tickfont=dict(size=10,color=SB), title_font=dict(size=11,color=MU),
                   gridcolor=BR, linecolor=BR, zeroline=False),
    )
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

# ══════════════════════════════════════════════════════
# SIDEBAR  (static — no rerun buttons, just HTML nav)
# ══════════════════════════════════════════════════════
with st.sidebar:

    # Logo
    st.markdown(f"""
    <div style="padding:20px 20px 16px;border-bottom:1px solid rgba(255,255,255,0.08);
                display:flex;align-items:center;gap:10px;">
      <span style="font-size:22px;line-height:1;">📊</span>
      <div>
        <div style="font-size:14px;font-weight:800;color:white;line-height:1.15;">SaaS Analytics</div>
        <div style="font-size:10px;color:#7EB8D8;margin-top:2px;">Powered by dbt + Snowflake</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # NAVIGATION label
    st.markdown("""
    <div style="padding:14px 20px 6px;font-size:9px;font-weight:700;
                letter-spacing:0.13em;color:#7EB8D8;text-transform:uppercase;">
      Navigation
    </div>
    """, unsafe_allow_html=True)

    # Nav buttons
    for p in PAGES:
        if st.button(f"{PICO[p]}  {p}", key=f"nav_{p}", use_container_width=True):
            st.session_state.page = p
            st.rerun()

    # Inject active highlight
    inject_active_nav(st.session_state.page)

    # Divider
    st.markdown(
        '<div style="height:1px;background:rgba(255,255,255,0.09);margin:10px 0;"></div>',
        unsafe_allow_html=True)

    # YEAR label + widget
    st.markdown("""
    <div style="padding:8px 20px 5px;font-size:9px;font-weight:700;
                letter-spacing:0.13em;color:#7EB8D8;text-transform:uppercase;">Year</div>
    """, unsafe_allow_html=True)
    year_sel = st.multiselect("_yr", ALL_YEARS, default=[max(ALL_YEARS)],
                              label_visibility="collapsed")
    if not year_sel: year_sel = [max(ALL_YEARS)]

    # MONTH label + widget
    st.markdown("""
    <div style="padding:10px 20px 5px;font-size:9px;font-weight:700;
                letter-spacing:0.13em;color:#7EB8D8;text-transform:uppercase;">
      Month <span style="font-weight:400;color:#4A7A9B;">(optional)</span>
    </div>
    """, unsafe_allow_html=True)
    mo_lbls = st.multiselect("_mo", list(MN.values()), default=[],
                             label_visibility="collapsed")
    mo_sel  = [k for k,v in MN.items() if v in mo_lbls]

    # PLAN label + checkboxes
    st.markdown("""
    <div style="padding:10px 20px 6px;font-size:9px;font-weight:700;
                letter-spacing:0.13em;color:#7EB8D8;text-transform:uppercase;">Plan</div>
    """, unsafe_allow_html=True)
    pl_free = st.checkbox("Free",       value=True, key="pl_free")
    pl_pro  = st.checkbox("Pro",        value=True, key="pl_pro")
    pl_ent  = st.checkbox("Enterprise", value=True, key="pl_ent")
    plan_sel = (["free"] if pl_free else []) + \
               (["pro"]  if pl_pro  else []) + \
               (["enterprise"] if pl_ent else [])
    if not plan_sel: plan_sel = ["free","pro","enterprise"]

    # YoY badge
    prev_y = sorted(set(y-1 for y in year_sel))
    yc = ", ".join(str(y) for y in sorted(year_sel))
    yp = ", ".join(str(y) for y in sorted(prev_y)) if prev_y else "—"
    st.markdown(f"""
    <div style="margin:14px 16px 4px;background:rgba(0,180,216,0.13);
                border-radius:8px;padding:10px 12px;">
      <div style="font-size:9px;font-weight:700;color:#7EB8D8;
                  letter-spacing:0.09em;text-transform:uppercase;margin-bottom:3px;">
        YOY COMPARISON</div>
      <div style="font-size:13px;color:white;font-weight:700;">{yc} vs {yp}</div>
      <div style="font-size:9px;color:#4A7A9B;margin-top:2px;">All KPI cards show delta</div>
    </div>
    <div style="padding:10px 20px 8px;font-size:9px;color:#4A7A9B;">
      Data snapshot from Snowflake marts
    </div>
    """, unsafe_allow_html=True)

page = st.session_state.page

# ══════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════
if page == "Overview":
    st.markdown('<div class="ptitle">Executive Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="psub">Key metrics across your entire SaaS business</div>', unsafe_allow_html=True)
    pills(year_sel, mo_sel, plan_sel)

    u_c = fu(D["users"],plan_sel,year_sel,mo_sel)
    u_p = fu(D["users"],plan_sel,prev_y,mo_sel)
    tot    = len(u_c);   tot_p   = len(u_p)   if len(u_p) else None
    paid   = len(u_c[u_c["PLAN"]!="FREE"])
    paid_p = len(u_p[u_p["PLAN"]!="FREE"]) if len(u_p) else None
    mrrv   = u_c["MRR"].sum();   mrrv_p = u_p["MRR"].sum() if len(u_p) else None
    chr_   = round(u_c["IS_CHURNED"].astype(bool).mean()*100,1) if len(u_c) else 0
    chr_p  = round(u_p["IS_CHURNED"].astype(bool).mean()*100,1) if len(u_p) else None
    onb    = round(u_c["ONBOARDING_COMPLETED"].astype(bool).mean()*100,1) if len(u_c) else 0
    onb_p  = round(u_p["ONBOARDING_COMPLETED"].astype(bool).mean()*100,1) if len(u_p) else None
    eng    = round(u_c["ENGAGEMENT_SCORE"].mean(),1) if len(u_c) else 0
    eng_p  = round(u_p["ENGAGEMENT_SCORE"].mean(),1) if len(u_p) else None

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    with k1: kpi("New Users",      fn(tot),    *yoy(tot,  tot_p),       SB)
    with k2: kpi("Paid Users",     fn(paid),   *yoy(paid, paid_p),      MID)
    with k3: kpi("MRR (cohort)",   fd(mrrv),   *yoy(mrrv, mrrv_p),     ACC)
    with k4: kpi("Churn Rate",     f"{chr_}%", *yoy(chr_, chr_p, True), RED)
    with k5: kpi("Onboarding %",   f"{onb}%",  *yoy(onb,  onb_p),      GRN)
    with k6: kpi("Avg Engagement", str(eng),   *yoy(eng,  eng_p),       ORG)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        sec("User Distribution by Plan")
        pd_ = u_c.groupby("PLAN").agg(N=("USER_ID","count"),MRR=("MRR","sum")).reset_index()
        pd_["LBL"] = pd_["PLAN"].str.capitalize()
        fig = px.pie(pd_,names="LBL",values="N",color="PLAN",color_discrete_map=PCU,hole=0.52)
        fig.update_traces(textposition="outside",textinfo="percent+label",
                          textfont=dict(size=11,color=SB),
                          marker=dict(line=dict(color=WH,width=2)),
                          hovertemplate="<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>")
        rs(fig,295,unified=False)
    with c2:
        sec("MRR by Plan")
        fig2 = px.bar(pd_,x="LBL",y="MRR",color="PLAN",color_discrete_map=PCU,text="MRR")
        fig2.update_traces(texttemplate="$%{text:,.0f}",textposition="outside",
                           textfont=dict(size=10,color=SB),
                           hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>")
        fig2.update_layout(showlegend=False,xaxis_title="",yaxis_title="MRR ($)")
        rs(fig2,295,unified=False,bar_gap=0.4)

    sec("User Signups Over Time")
    ua = fp(D["users"],plan_sel).copy()
    ua["MONTH_DT"] = pd.to_datetime(ua["SIGNUP_MONTH"])
    sg = ua.groupby(["MONTH_DT","PLAN"]).size().reset_index(name="N").sort_values("MONTH_DT")
    sg["LBL"] = sg["PLAN"].str.capitalize()
    fig3 = px.area(sg,x="MONTH_DT",y="N",color="LBL",color_discrete_map=PC,
                   labels={"N":"New Users","MONTH_DT":"","LBL":"Plan"})
    fig3.update_traces(hovertemplate="<b>%{fullData.name}</b>: %{y:,}<extra></extra>")
    rs(fig3,265)

    c1,c2 = st.columns(2)
    with c1:
        sec("Top Countries by Users")
        co = (u_c.groupby("COUNTRY")["USER_ID"].count()
              .reset_index(name="N").sort_values("N",ascending=False).head(8))
        fig4 = px.bar(co,x="N",y="COUNTRY",orientation="h",
                      color_discrete_sequence=[MID],labels={"N":"Users","COUNTRY":""})
        fig4.update_traces(hovertemplate="<b>%{y}</b>: %{x:,}<extra></extra>")
        fig4.update_layout(yaxis=dict(autorange="reversed"),showlegend=False)
        rs(fig4,260,unified=False,bar_gap=0.3)
    with c2:
        sec("Onboarding Completion by Plan")
        ob = u_c.groupby("PLAN")["ONBOARDING_COMPLETED"].apply(
            lambda x: round(x.astype(bool).mean()*100,1)).reset_index(name="PCT")
        ob["LBL"] = ob["PLAN"].str.capitalize()
        fig5 = px.bar(ob,x="LBL",y="PCT",color="PLAN",color_discrete_map=PCU,text="PCT")
        fig5.update_traces(texttemplate="%{text}%",textposition="outside",
                           textfont=dict(size=11,color=SB),
                           hovertemplate="<b>%{x}</b>: %{y:.1f}%<extra></extra>")
        fig5.update_layout(showlegend=False,xaxis_title="",yaxis_title="Completion %",
                           yaxis_range=[0,115])
        rs(fig5,260,unified=False,bar_gap=0.4)


# ══════════════════════════════════════════════════════
# PAGE 2 — REVENUE & MRR
# ══════════════════════════════════════════════════════
elif page == "Revenue & MRR":
    st.markdown('<div class="ptitle">Revenue & MRR</div>', unsafe_allow_html=True)
    st.markdown('<div class="psub">Monthly recurring revenue movements, growth and payment health</div>', unsafe_allow_html=True)
    pills(year_sel, mo_sel, plan_sel)

    m_c = fmr(D["mrr"],plan_sel,year_sel,mo_sel)
    m_p = fmr(D["mrr"],plan_sel,prev_y,mo_sel)

    tm  = total_mrr(m_c);     tm_p = total_mrr(m_p)    if len(m_p) else None
    nm  = new_mrr(m_c);       nm_p = new_mrr(m_p)       if len(m_p) else None
    cm  = churned_mrr(m_c);   cm_p = churned_mrr(m_p)   if len(m_p) else None
    em  = expansion_mrr(m_c); em_p = expansion_mrr(m_p) if len(m_p) else None
    net = nm - cm + em
    net_p = (nm_p - cm_p + em_p) if nm_p is not None else None

    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: kpi("Total MRR",     fd(tm),  *yoy(tm, tm_p),        ACC)
    with k2: kpi("New MRR",       fd(nm),  *yoy(nm, nm_p),        GRN)
    with k3: kpi("Churned MRR",   fd(cm),  *yoy(cm, cm_p,  True), RED)
    with k4: kpi("Expansion MRR", fd(em),  *yoy(em, em_p),        MID)
    with k5: kpi("Net New MRR",   fd(net), *yoy(net,net_p),       ORG)

    sec("Payment Success by Plan")
    ppay = D["payments"][D["payments"]["PLAN"].isin([p.upper() for p in plan_sel if p!="free"])]
    if len(ppay)==0:
        st.info("No payment records for selected plans.")
    else:
        cols = st.columns(len(ppay))
        for i,(_,row) in enumerate(ppay.iterrows()):
            t_   = row["SUCCEEDED"]+row["FAILED"]+row["REFUNDED"]
            rate = round(row["SUCCEEDED"]/t_*100,1) if t_>0 else 0
            pn   = str(row["PLAN"]).lower()
            ac   = {"pro":MID,"enterprise":SB}.get(pn,ACC)
            with cols[i]:
                kpi(f"{pn.capitalize()} — Success Rate",f"{rate}%",
                    f"${row['REVENUE']:,.0f} collected","up",ac)

    sec("MRR Waterfall — Monthly Movements")
    MC = {"NEW":GRN,"EXPANSION":ACC,"RETAINED":MID,"CONTRACTION":ORG,"CHURN":RED,"NEW_FREE":"#95A5A6"}
    ma = fp(D["mrr"],plan_sel).copy()
    ma["MONTH_DATE"] = pd.to_datetime(ma["MONTH_DATE"])
    mg = ma.groupby(["MONTH_DATE","MRR_MOVEMENT_TYPE"]).agg(V=("TOTAL_MRR","sum")).reset_index()
    fig = px.bar(mg,x="MONTH_DATE",y="V",color="MRR_MOVEMENT_TYPE",
                 color_discrete_map=MC,barmode="relative",
                 labels={"V":"MRR ($)","MONTH_DATE":"","MRR_MOVEMENT_TYPE":"Movement"})
    fig.update_traces(hovertemplate="<b>%{fullData.name}</b> %{x|%b %Y}: $%{y:,.0f}<extra></extra>")
    rs(fig,295,bar_gap=0.2)

    c1,c2 = st.columns(2)
    with c1:
        sec("New vs Churned MRR — YoY")
        nv = fp(D["mrr"],plan_sel).copy()
        nv = nv[nv["MRR_MOVEMENT_TYPE"].isin(["NEW","CHURN"])].copy()
        nv["MONTH_DATE"] = pd.to_datetime(nv["MONTH_DATE"])
        nv = nv[nv["MRR_YEAR"].isin(sorted(set(year_sel)|set(prev_y)))]
        # Use correct MRR values: NEW → total_mrr, CHURN → abs(net_mrr_change)
        if HAS_NET:
            nv["PLOT"] = nv.apply(lambda r: r["TOTAL_MRR"] if r["MRR_MOVEMENT_TYPE"]=="NEW"
                                  else abs(r["NET_MRR_CHANGE"]), axis=1)
        else:
            nv["PLOT"] = nv["TOTAL_MRR"].abs()
        nv2 = nv.groupby(["MONTH_DATE","MRR_MOVEMENT_TYPE"]).agg(MRR=("PLOT","sum")).reset_index()
        nv2["LBL"] = nv2["MRR_MOVEMENT_TYPE"].str.capitalize()
        fig2 = px.line(nv2,x="MONTH_DATE",y="MRR",color="LBL",
                       color_discrete_map={"New":GRN,"Churn":RED},markers=True,
                       labels={"MRR":"MRR ($)","MONTH_DATE":"","LBL":"Type"})
        fig2.update_traces(hovertemplate="<b>%{fullData.name}</b> %{x|%b %Y}: $%{y:,.0f}<extra></extra>")
        rs(fig2,275)

    with c2:
        sec("MRR Growth Rate (Month-over-Month)")
        gr = ma.copy()
        gr = gr[gr["MRR_MOVEMENT_TYPE"].isin(["NEW","EXPANSION","RETAINED"])].copy()
        gr_m = gr.groupby("MONTH_DATE")["TOTAL_MRR"].sum().reset_index().sort_values("MONTH_DATE")
        gr_m["PREV"] = gr_m["TOTAL_MRR"].shift(1)
        gr_m["GR"]   = ((gr_m["TOTAL_MRR"] - gr_m["PREV"]) / gr_m["PREV"].abs() * 100).round(1)
        gr_m = gr_m.dropna(subset=["GR"])
        fig3 = px.bar(gr_m,x="MONTH_DATE",y="GR",
                      color_discrete_sequence=[ACC],
                      labels={"GR":"MoM Growth %","MONTH_DATE":""})
        fig3.update_traces(hovertemplate="%{x|%b %Y}: %{y:+.1f}%<extra></extra>",
                           marker_color=[GRN if v>=0 else RED for v in gr_m["GR"]])
        fig3.update_layout(showlegend=False)
        rs(fig3,275,bar_gap=0.2)

    


# ══════════════════════════════════════════════════════
# PAGE 3 — CHURN & ENGAGEMENT
# ══════════════════════════════════════════════════════
elif page == "Churn & Engagement":
    st.markdown('<div class="ptitle">Churn & Engagement</div>', unsafe_allow_html=True)
    st.markdown('<div class="psub">Who churns, why, and how users engage with your product</div>', unsafe_allow_html=True)
    pills(year_sel, mo_sel, plan_sel)

    ch_c = fch(D["churn"],plan_sel,year_sel,mo_sel)
    ch_p = fch(D["churn"],plan_sel,prev_y,mo_sel)
    se_c = fse(D["sessions"],plan_sel,year_sel,mo_sel)
    se_p = fse(D["sessions"],plan_sel,prev_y,mo_sel)

    def ck(df): return {
        "n":  len(df), "mrr": df["LOST_MRR"].sum() if len(df) else 0,
        "d2c":int(df["DAYS_TO_CHURN"].mean()) if len(df) else 0,
        "ses":round(df["TOTAL_SESSIONS"].mean(),1) if len(df) else 0,
        "bnc":round(df["BOUNCE_RATE_PCT"].mean(),1) if len(df) else 0,
    }
    cc=ck(ch_c); cp=ck(ch_p) if len(ch_p) else None
    ts    = se_c["SESSIONS"].sum();     ts_p  = se_p["SESSIONS"].sum()     if len(se_p) else None
    bc    = se_c["BOUNCE_COUNT"].sum(); bc_p  = se_p["BOUNCE_COUNT"].sum() if len(se_p) else None
    bnc   = round(bc/ts*100,1) if ts else 0
    bnc_p = round(bc_p/ts_p*100,1) if ts_p else None
    dur   = round(se_c["AVG_DURATION_MIN"].mean(),1) if len(se_c) else 0

    # KPI row — churn + engagement combined
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    with k1: kpi("Total Churned",     fn(cc["n"]),    *yoy(cc["n"],  cp["n"]  if cp else None,True),RED)
    with k2: kpi("Lost MRR",          fd(cc["mrr"]),  *yoy(cc["mrr"],cp["mrr"] if cp else None,True),RED)
    with k3: kpi("Avg Days to Churn", f"{cc['d2c']}d",*yoy(cc["d2c"],cp["d2c"] if cp else None),     ORG)
    with k4: kpi("Total Sessions",    fn(ts),         *yoy(ts, ts_p),                                SB)
    with k5: kpi("Avg Duration",      f"{dur}min",    None,"nt",                                     ACC)
    with k6: kpi("Bounce Rate",       f"{bnc}%",      *yoy(bnc,bnc_p,True),                          PUR)

    # Churn section
    sec("Churn Analysis")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("**Churn by Stage & Plan**")
        cs = ch_c.groupby(["CHURN_STAGE","PLAN"]).agg(N=("USER_ID","count")).reset_index()
        cs["LBL"] = cs["PLAN"].str.capitalize()
        fig = px.bar(cs,x="CHURN_STAGE",y="N",color="LBL",barmode="group",
                     color_discrete_map=PC,
                     category_orders={"CHURN_STAGE":["IMMEDIATE","EARLY","MID","LATE"]},
                     labels={"N":"Churned","CHURN_STAGE":"","LBL":"Plan"})
        fig.update_traces(hovertemplate="<b>%{fullData.name}</b> %{x}: %{y:,}<extra></extra>")
        rs(fig,270,bar_gap=0.2)
    with c2:
        st.markdown("**NPS of Churned Users**")
        nps = ch_c.dropna(subset=["NPS_CATEGORY"]).groupby("NPS_CATEGORY").size().reset_index(name="N")
        nps["LBL"] = nps["NPS_CATEGORY"].str.capitalize()
        fig2 = px.pie(nps,names="LBL",values="N",color="NPS_CATEGORY",
                      color_discrete_map={"DETRACTOR":RED,"PASSIVE":ORG,"PROMOTER":GRN},hole=0.5)
        fig2.update_traces(textposition="outside",textinfo="percent+label",
                           textfont=dict(size=11,color=SB),
                           marker=dict(line=dict(color=WH,width=2)),
                           hovertemplate="<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>")
        rs(fig2,270,unified=False)

    sec("Churn Trend — Current vs Previous Year")
    ct = fp(D["churn"],plan_sel).copy()
    ct["MONTH_DT"] = pd.to_datetime(ct["CHURNED_AT"]).dt.to_period("M").dt.to_timestamp()
    ct2 = (ct[ct["CHURN_YEAR"].isin(sorted(set(year_sel)|set(prev_y)))]
           .groupby(["MONTH_DT","PLAN","CHURN_YEAR"]).size()
           .reset_index(name="N").sort_values("MONTH_DT"))
    ct2["LBL"] = ct2["PLAN"].str.capitalize()
    ct2["YRBL"] = ct2["CHURN_YEAR"].astype(str)
    fig3 = px.line(ct2,x="MONTH_DT",y="N",color="LBL",line_dash="YRBL",
                   color_discrete_map=PC,markers=True,
                   labels={"N":"Churned","MONTH_DT":"","LBL":"Plan","YRBL":"Year"})
    fig3.update_traces(hovertemplate="<b>%{fullData.name}</b> %{x|%b %Y}: %{y:,}<extra></extra>")
    rs(fig3,260)

    # Engagement section
    sec("Engagement Deep Dive")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("**Sessions by Platform**")
        pl = se_c.groupby(["PLATFORM","PLAN"])["SESSIONS"].sum().reset_index()
        pl["LBL"] = pl["PLAN"].str.capitalize()
        fig4 = px.bar(pl,x="PLATFORM",y="SESSIONS",color="LBL",barmode="group",
                      color_discrete_map=PC,labels={"SESSIONS":"Sessions","PLATFORM":"","LBL":"Plan"})
        fig4.update_traces(hovertemplate="<b>%{fullData.name}</b> %{x}: %{y:,}<extra></extra>")
        rs(fig4,265,bar_gap=0.2)
    with c2:
        st.markdown("**Session Depth Distribution**")
        dp = se_c.groupby("DEPTH_BUCKET")["SESSIONS"].sum().reset_index()
        fig5 = px.bar(dp,x="DEPTH_BUCKET",y="SESSIONS",color_discrete_sequence=[ACC],
                      category_orders={"DEPTH_BUCKET":["1 PAGE (BOUNCE)","2-3 PAGES","4-7 PAGES","8+ PAGES (DEEP)"]},
                      labels={"SESSIONS":"Sessions","DEPTH_BUCKET":""})
        fig5.update_traces(hovertemplate="<b>%{x}</b>: %{y:,}<extra></extra>")
        fig5.update_layout(showlegend=False)
        rs(fig5,265,unified=False,bar_gap=0.25)


# ══════════════════════════════════════════════════════
# PAGE 4 — RETENTION & FEATURES
# ══════════════════════════════════════════════════════
elif page == "Retention & Features":
    st.markdown('<div class="ptitle">Retention & Feature Usage</div>', unsafe_allow_html=True)
    st.markdown('<div class="psub">Cohort retention curves and feature adoption across plans</div>', unsafe_allow_html=True)
    pills(year_sel, mo_sel, plan_sel)

    ret  = fy(D["retention"].copy(), year_sel, "COHORT_YEAR")
    ft_c = ffe(D["features"],plan_sel,year_sel,mo_sel)
    ft_p = ffe(D["features"],plan_sel,prev_y,mo_sel)
    ret["COHORT_MONTH"] = pd.to_datetime(ret["COHORT_MONTH"]).dt.strftime("%Y-%m")

    te   = ft_c["EVENTS"].sum();       te_p = ft_p["EVENTS"].sum()       if len(ft_p) else None
    ud   = ft_c["UNIQUE_USERS"].sum(); ud_p = ft_p["UNIQUE_USERS"].sum() if len(ft_p) else None

    k1,k2,k3,k4 = st.columns(4)
    m1 = round(ret[ret["MONTHS_SINCE_SIGNUP"]==1]["RETENTION_PCT"].mean(),1) if len(ret) else 0
    m3 = round(ret[ret["MONTHS_SINCE_SIGNUP"]==3]["RETENTION_PCT"].mean(),1) if len(ret) else 0
    with k1: kpi("Month-1 Retention",f"{m1}%",  None,"nt", GRN)
    with k2: kpi("Month-3 Retention",f"{m3}%",  None,"nt", ACC)
    with k3: kpi("Feature Events",    fn(te),   *yoy(te,te_p), MID)
    with k4: kpi("Active User-Days",  fn(ud),   *yoy(ud,ud_p), SB)

    # Retention section
    sec("Cohort Retention")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("**Retention Curves — Top 8 Cohorts**")
        top_c = ret.groupby("COHORT_MONTH")["ACTIVE_USERS"].sum().nlargest(8).index.tolist()
        fig = px.line(ret[ret["COHORT_MONTH"].isin(top_c)],
                      x="MONTHS_SINCE_SIGNUP",y="RETENTION_PCT",color="COHORT_MONTH",markers=True,
                      labels={"RETENTION_PCT":"Retention %","MONTHS_SINCE_SIGNUP":"Month"})
        fig.update_traces(hovertemplate="<b>%{fullData.name}</b> Mo%{x}: %{y:.1f}%<extra></extra>")
        fig.update_layout(yaxis_range=[0,105])
        rs(fig,290)
    with c2:
        st.markdown("**Cohort Retention Heatmap**")
        pv = ret.pivot(index="COHORT_MONTH",columns="MONTHS_SINCE_SIGNUP",values="RETENTION_PCT")
        fig2 = px.imshow(pv,color_continuous_scale=["#FEF0F0","#EBF4FA",ACC],
                         labels=dict(x="Months",y="Cohort",color="Ret %"),
                         zmin=0,zmax=100,aspect="auto",text_auto=".0f")
        fig2.update_traces(textfont=dict(size=8,color=SB),
                           hovertemplate="<b>%{y}</b> Mo%{x}: %{z:.1f}%<extra></extra>")
        fig2.update_layout(height=290,paper_bgcolor=WH,plot_bgcolor=PLT,font=CFONT,
                           margin=dict(l=6,r=6,t=38,b=48),hoverlabel=HL,
                           xaxis=dict(tickfont=dict(size=9,color=SB)),
                           yaxis=dict(tickfont=dict(size=9,color=SB)))
        st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})

    sec("Avg Retention at Key Milestones")
    sa = ret[ret["MONTHS_SINCE_SIGNUP"].isin([1,3,6,12])].copy()
    sa = sa.groupby("MONTHS_SINCE_SIGNUP")["RETENTION_PCT"].mean().reset_index()
    sa.columns=["MONTH","AVG"]; sa["AVG"]=sa["AVG"].round(1)
    sa["LBL"] = sa["MONTH"].apply(lambda m: f"Month {m}")
    fig3 = px.bar(sa,x="LBL",y="AVG",color="AVG",
                  color_continuous_scale=[RED,ORG,GRN],text="AVG",
                  labels={"AVG":"Retention %","LBL":""})
    fig3.update_traces(texttemplate="%{text}%",textposition="outside",
                       textfont=dict(size=13,color=SB),
                       hovertemplate="<b>%{x}</b>: %{y:.1f}%<extra></extra>")
    fig3.update_layout(showlegend=False,yaxis_range=[0,115],coloraxis_showscale=False)
    rs(fig3,230,unified=False,bar_gap=0.45)

    # Feature section
    sec("Feature Usage")
    fa = (ft_c.groupby(["FEATURE_NAME","PLAN"])
          .agg(EVENTS=("EVENTS","sum"),UNIQUE_USERS=("UNIQUE_USERS","sum")).reset_index())
    fa["LBL"] = fa["PLAN"].str.capitalize()
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("**Events by Feature & Plan**")
        fig4 = px.bar(fa,x="FEATURE_NAME",y="EVENTS",color="LBL",barmode="group",
                      color_discrete_map=PC,labels={"EVENTS":"Events","FEATURE_NAME":"","LBL":"Plan"})
        fig4.update_traces(hovertemplate="<b>%{fullData.name}</b> %{x}: %{y:,}<extra></extra>")
        fig4.update_layout(xaxis_tickangle=-30)
        rs(fig4,275,bar_gap=0.15)
    with c2:
        st.markdown("**Feature Trend — Top 5**")
        ft_tr = ft_c.groupby(["EVENT_MONTH","FEATURE_NAME"])["EVENTS"].sum().reset_index()
        ft_tr["EVENT_MONTH"] = pd.to_datetime(ft_tr["EVENT_MONTH"])
        top5  = ft_tr.groupby("FEATURE_NAME")["EVENTS"].sum().nlargest(5).index.tolist()
        fig5  = px.line(ft_tr[ft_tr["FEATURE_NAME"].isin(top5)],
                        x="EVENT_MONTH",y="EVENTS",color="FEATURE_NAME",markers=True,
                        labels={"EVENTS":"Events","EVENT_MONTH":"","FEATURE_NAME":"Feature"})
        fig5.update_traces(hovertemplate="<b>%{fullData.name}</b> %{x|%b %Y}: %{y:,}<extra></extra>")
        rs(fig5,275)