"""
SaaS Analytics Dashboard — Streamlit App
7 CSV files in data/exports/ (down from 15).
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import warnings
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
# DESIGN TOKENS
# ─────────────────────────────────────────────
BLUE       = "#1E3A5F"
LIGHT_BLUE = "#2E6DA4"
ACCENT     = "#00B4D8"
GREEN      = "#2ECC71"
RED        = "#E74C3C"
ORANGE     = "#F39C12"
PURPLE     = "#9B59B6"

PLAN_COLORS = {"free": ACCENT, "pro": LIGHT_BLUE, "enterprise": BLUE}
MONTH_NAMES = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
               7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
  .stApp { background: #F0F4F8; }

  [data-testid="stSidebar"] { background: #1E3A5F !important; }
  [data-testid="stSidebar"] * { color: #E8F4FD !important; }
  [data-testid="stSidebar"] label {
    color: #A8D4F0 !important; font-size: 0.72rem;
    font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
  }

  .metric-card {
    background: white; border-radius: 12px; padding: 20px 24px;
    border-left: 4px solid #00B4D8;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 4px;
  }
  .metric-label {
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; color: #6B8CAE; margin-bottom: 6px;
  }
  .metric-value  { font-size: 2rem; font-weight: 700; color: #1E3A5F; line-height: 1; }
  .metric-delta  { font-size: 0.78rem; margin-top: 6px; font-weight: 600; }
  .metric-delta.up      { color: #2ECC71; }
  .metric-delta.down    { color: #E74C3C; }
  .metric-delta.neutral { color: #95A5A6; }

  .section-header {
    font-size: 1.15rem; font-weight: 700; color: #1E3A5F;
    margin: 28px 0 14px; padding-bottom: 8px;
    border-bottom: 2px solid #00B4D8;
  }
  .page-title    { font-size: 2rem; font-weight: 700; color: #1E3A5F; letter-spacing: -0.03em; }
  .page-subtitle { font-size: 0.9rem; color: #6B8CAE; margin-top: 2px; }
  .filter-pill {
    display: inline-block; background: rgba(0,180,216,0.12);
    color: #1E3A5F; border-radius: 20px; padding: 3px 10px;
    font-size: 0.75rem; font-weight: 600; margin-right: 4px; margin-bottom: 4px;
  }
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 2rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATA LOADING  (7 files)
# ─────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "exports")

@st.cache_data
def load_all():
    def read(f):
        df = pd.read_csv(os.path.join(DATA_DIR, f))
        df.columns = [c.upper() for c in df.columns]
        return df
    return {
        # mart tables — used as-is
        "dim_users":     read("dim_users_export.csv"),
        "fct_mrr":       read("fct_mrr_export.csv"),
        "fct_churn":     read("fct_churn_export.csv"),
        "fct_retention": read("fct_retention_export.csv"),
        # aggregated session data — one file replaces 6
        "sessions":      read("fct_sessions_agg.csv"),
        # aggregated feature data — one file replaces 4
        "features":      read("fct_feature_usage_agg.csv"),
        # payments summary
        "payments":      read("payments_export.csv"),
    }

try:
    D = load_all()
except FileNotFoundError as e:
    st.error(f"❌ Missing export file: {e}")
    st.info("Run `snowflake_export_queries.sql` and save CSVs to `data/exports/`.")
    st.stop()


# ─────────────────────────────────────────────
# FILTER HELPERS
# ─────────────────────────────────────────────
def fp(df, plans, col="PLAN"):
    """Filter by plan."""
    return df[df[col].str.lower().isin([p.lower() for p in plans])]

def fy(df, years, col="SESSION_YEAR"):
    """Filter by year — uses the correct year column name per dataframe."""
    if col not in df.columns:
        return df
    return df[df[col].isin(years)]

def fm(df, months, col="SESSION_MONTH_NUM"):
    """Filter by month — skip if no months selected (= all months)."""
    if col not in df.columns or not months:
        return df
    return df[df[col].isin(months)]

def filter_sessions(df, plans, years, months):
    df = fp(df, plans)
    df = fy(df, years, "SESSION_YEAR")
    df = fm(df, months, "SESSION_MONTH_NUM")
    return df

def filter_features(df, plans, years, months):
    df = fp(df, plans)
    df = fy(df, years, "EVENT_YEAR")
    df = fm(df, months, "EVENT_MONTH_NUM")
    return df

def filter_mrr(df, plans, years, months):
    df = fp(df, plans)
    df = fy(df, years, "MRR_YEAR")
    df = fm(df, months, "MRR_MONTH_NUM")
    return df

def filter_churn(df, plans, years, months):
    df = fp(df, plans)
    df = fy(df, years, "CHURN_YEAR")
    df = fm(df, months, "CHURN_MONTH_NUM")
    return df

def filter_users(df, plans, years, months):
    df = fp(df, plans)
    df = fy(df, years, "SIGNUP_YEAR")
    df = fm(df, months, "SIGNUP_MONTH_NUM")
    return df


# ─────────────────────────────────────────────
# YoY HELPER
# ─────────────────────────────────────────────
def yoy_delta(curr_val, prev_val):
    if prev_val is None or prev_val == 0:
        return None, "neutral"
    pct = (curr_val - prev_val) / abs(prev_val) * 100
    direction = "up" if pct >= 0 else "down"
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.1f}% vs prev year", direction


# ─────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────
def metric_card(label, value, delta=None, delta_dir="up", accent=ACCENT):
    delta_html = ""
    if delta:
        arrow = "▲" if delta_dir == "up" else ("▼" if delta_dir == "down" else "–")
        delta_html = f'<div class="metric-delta {delta_dir}">{arrow} {delta}</div>'
    st.markdown(f"""
    <div class="metric-card" style="border-left-color:{accent}">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      {delta_html}
    </div>""", unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)

def chart_card(fig, title=None):
    if title:
        st.markdown(f'<div style="font-weight:600;color:{BLUE};margin-bottom:8px;font-size:0.95rem;">{title}</div>',
                    unsafe_allow_html=True)
    fig.update_layout(
        paper_bgcolor="white", plot_bgcolor="#F8FAFC",
        font_family="DM Sans", font_color=BLUE,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#E0E8F0", borderwidth=1),
    )
    st.plotly_chart(fig, use_container_width=True)

def fmt_currency(val):
    if pd.isna(val): return "$0"
    if val >= 1_000_000: return f"${val/1_000_000:.2f}M"
    if val >= 1_000:     return f"${val/1_000:.1f}K"
    return f"${val:,.0f}"

def fmt_number(val):
    if pd.isna(val): return "0"
    if val >= 1_000_000: return f"{val/1_000_000:.2f}M"
    if val >= 1_000:     return f"{val/1_000:.1f}K"
    return f"{int(val):,}"

def active_filter_pills(years, months, plans):
    parts = [
        f"Plans: {', '.join(plans)}",
        f"Years: {', '.join(str(y) for y in sorted(years))}",
    ]
    if months:
        parts.append(f"Months: {', '.join(MONTH_NAMES[m] for m in sorted(months))}")
    pills = "".join(f'<span class="filter-pill">{p}</span>' for p in parts)
    st.markdown(f'<div style="margin-bottom:16px;">{pills}</div>', unsafe_allow_html=True)

def wt_avg(df, val_col, wt_col):
    """Weighted average — used for session KPIs."""
    total_w = df[wt_col].sum()
    if total_w == 0: return 0.0
    return round((df[val_col] * df[wt_col]).sum() / total_w, 1)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
all_years = sorted(D["fct_mrr"]["MRR_YEAR"].dropna().unique().astype(int).tolist())

with st.sidebar:
    st.markdown("""
    <div style="padding:16px 0 22px;">
      <div style="font-size:1.35rem;font-weight:700;color:white;letter-spacing:-0.02em;">📊 SaaS Analytics</div>
      <div style="font-size:0.72rem;color:#7EB8D8;margin-top:3px;">Powered by dbt + Snowflake</div>
    </div>""", unsafe_allow_html=True)

    page = st.selectbox("NAVIGATION", [
        "🏠  Overview",
        "💰  Revenue & MRR",
        "📉  Churn Analysis",
        "👥  User Engagement",
        "🔧  Feature Usage",
        "🔁  Retention",
    ])

    st.markdown("---")
    st.markdown('<div style="font-size:0.72rem;font-weight:700;letter-spacing:0.1em;'
                'color:#7EB8D8;text-transform:uppercase;margin-bottom:10px;">Filters</div>',
                unsafe_allow_html=True)

    year_filter = st.multiselect("YEAR", options=all_years, default=[max(all_years)])
    if not year_filter:
        year_filter = [max(all_years)]

    month_labels   = list(MONTH_NAMES.values())
    sel_month_lbls = st.multiselect("MONTH (blank = all)", options=month_labels, default=[])
    month_filter   = [k for k, v in MONTH_NAMES.items() if v in sel_month_lbls]

    plan_filter = st.multiselect("PLAN", ["free","pro","enterprise"],
                                 default=["free","pro","enterprise"])
    if not plan_filter:
        plan_filter = ["free","pro","enterprise"]

    prev_years = sorted(set(y - 1 for y in year_filter))

    st.markdown("---")
    yoy_curr = ", ".join(str(y) for y in sorted(year_filter))
    yoy_prev = ", ".join(str(y) for y in sorted(prev_years)) if prev_years else "—"
    st.markdown(f"""
    <div style="background:rgba(0,180,216,0.12);border-radius:8px;padding:8px 10px;margin-bottom:10px;">
      <div style="font-size:9px;font-weight:700;color:#7EB8D8;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:2px;">YoY Comparison</div>
      <div style="font-size:11px;color:#A8D4F0;font-weight:600;">{yoy_curr} vs {yoy_prev}</div>
      <div style="font-size:9px;color:#4A7A9B;margin-top:2px;">All KPI cards show delta</div>
    </div>""", unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.7rem;color:#4A7A9B;text-align:center;">Data snapshot from Snowflake marts</div>',
                unsafe_allow_html=True)


# ═════════════════════════════════════════════
# PAGE: OVERVIEW
# ═════════════════════════════════════════════
if page == "🏠  Overview":
    st.markdown('<div class="page-title">Executive Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Key metrics across your entire SaaS business</div>',
                unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    active_filter_pills(year_filter, month_filter, plan_filter)

    u_curr = filter_users(D["dim_users"], plan_filter, year_filter,  month_filter)
    u_prev = filter_users(D["dim_users"], plan_filter, prev_years, month_filter)

    def u_kpi(df): return {
        "total":    len(df),
        "paid":     len(df[df["PLAN"] != "free"]),
        "mrr":      df["MRR"].sum(),
        "churn":    round(df["IS_CHURNED"].astype(bool).mean() * 100, 1) if len(df) else 0,
        "onboard":  round(df["ONBOARDING_COMPLETED"].astype(bool).mean() * 100, 1) if len(df) else 0,
        "eng":      round(df["ENGAGEMENT_SCORE"].mean(), 1) if len(df) else 0,
    }
    c = u_kpi(u_curr)
    p = u_kpi(u_prev) if len(u_prev) else None

    def d(ck, pk=None, invert=False):
        v, di = yoy_delta(c[ck], p[pk or ck] if p else None)
        if invert and di == "up": di = "down"
        elif invert and di == "down": di = "up"
        return v, di

    tu_d, tu_r = d("total")
    pu_d, pu_r = d("paid")
    mr_d, mr_r = d("mrr")
    ch_d, ch_r = d("churn", invert=True)
    ob_d, ob_r = d("onboard")
    en_d, en_r = d("eng")

    r1,r2,r3,r4,r5,r6 = st.columns(6)
    with r1: metric_card("New Users",      fmt_number(c["total"]),  tu_d, tu_r, BLUE)
    with r2: metric_card("Paid Users",     fmt_number(c["paid"]),   pu_d, pu_r, LIGHT_BLUE)
    with r3: metric_card("MRR (cohort)",   fmt_currency(c["mrr"]),  mr_d, mr_r, ACCENT)
    with r4: metric_card("Churn Rate",     f"{c['churn']}%",        ch_d, ch_r, RED)
    with r5: metric_card("Onboarding",     f"{c['onboard']}%",      ob_d, ob_r, GREEN)
    with r6: metric_card("Avg Engagement", str(c["eng"]),           en_d, en_r, ORANGE)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        section("User Distribution by Plan")
        plan_dist = (u_curr.groupby("PLAN")
                     .agg(USERS=("USER_ID","count"), MRR=("MRR","sum"))
                     .reset_index().sort_values("MRR", ascending=False))
        fig = px.pie(plan_dist, names="PLAN", values="USERS",
                     color="PLAN", color_discrete_map={k.upper():v for k,v in PLAN_COLORS.items()},
                     hole=0.55)
        fig.update_traces(textposition="outside", textinfo="percent+label",
                          marker=dict(line=dict(color="white", width=2)))
        chart_card(fig)

    with col2:
        section("MRR by Plan")
        fig2 = px.bar(plan_dist, x="PLAN", y="MRR",
                      color="PLAN", color_discrete_map={k.upper():v for k,v in PLAN_COLORS.items()},
                      text="MRR")
        fig2.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
        fig2.update_layout(showlegend=False, yaxis_title="MRR ($)", xaxis_title="")
        chart_card(fig2)

    section("User Signups Over Time")
    users_all = fp(D["dim_users"], plan_filter)
    users_all = users_all.copy()
    users_all["MONTH_DT"] = pd.to_datetime(users_all["SIGNUP_MONTH"])
    signups = (users_all.groupby(["MONTH_DT","PLAN"])
               .size().reset_index(name="NEW_USERS").sort_values("MONTH_DT"))
    fig3 = px.area(signups, x="MONTH_DT", y="NEW_USERS", color="PLAN",
                   color_discrete_map={k.upper():v for k,v in PLAN_COLORS.items()},
                   labels={"NEW_USERS":"New Users","MONTH_DT":""})
    for yr in year_filter:
        fig3.add_vrect(x0=f"{yr}-01-01", x1=f"{yr}-12-31",
                       fillcolor=ACCENT, opacity=0.06, line_width=0,
                       annotation_text=str(yr), annotation_position="top left",
                       annotation_font_size=10)
    fig3.update_layout(hovermode="x unified")
    chart_card(fig3)

    section("Top Countries by Users")
    countries = (u_curr.groupby("COUNTRY")
                 .agg(USERS=("USER_ID","count"), MRR=("MRR","sum"))
                 .reset_index().sort_values("USERS", ascending=False).head(10))
    fig4 = px.bar(countries, x="USERS", y="COUNTRY", orientation="h",
                  color="MRR", color_continuous_scale=["#A8D4F0", BLUE],
                  labels={"USERS":"Users","COUNTRY":"","MRR":"MRR ($)"})
    fig4.update_layout(yaxis=dict(autorange="reversed"))
    chart_card(fig4)


# ═════════════════════════════════════════════
# PAGE: REVENUE & MRR
# ═════════════════════════════════════════════
elif page == "💰  Revenue & MRR":
    st.markdown('<div class="page-title">Revenue & MRR</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Monthly recurring revenue movements and growth trends</div>',
                unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    active_filter_pills(year_filter, month_filter, plan_filter)

    mrr_all  = fp(D["fct_mrr"], plan_filter)
    mrr_curr = filter_mrr(D["fct_mrr"], plan_filter, year_filter, month_filter)
    mrr_prev = filter_mrr(D["fct_mrr"], plan_filter, prev_years,  month_filter)

    def mrr_sum(df, mtype): return df[df["MRR_MOVEMENT_TYPE"]==mtype]["TOTAL_MRR"].sum()

    c_tot = mrr_curr[mrr_curr["MRR_MOVEMENT_TYPE"]!="NEW_FREE"]["TOTAL_MRR"].sum()
    p_tot = mrr_prev[mrr_prev["MRR_MOVEMENT_TYPE"]!="NEW_FREE"]["TOTAL_MRR"].sum() if len(mrr_prev) else None
    c_new = mrr_sum(mrr_curr,"NEW"); p_new = mrr_sum(mrr_prev,"NEW") if len(mrr_prev) else None
    c_chu = abs(mrr_sum(mrr_curr,"CHURN")); p_chu = abs(mrr_sum(mrr_prev,"CHURN")) if len(mrr_prev) else None
    c_exp = mrr_sum(mrr_curr,"EXPANSION"); p_exp = mrr_sum(mrr_prev,"EXPANSION") if len(mrr_prev) else None

    mt_d,mt_r = yoy_delta(c_tot,p_tot)
    mn_d,mn_r = yoy_delta(c_new,p_new)
    mc_d,mc_r = yoy_delta(c_chu,p_chu); mc_r = "down" if mc_r=="up" else ("up" if mc_r=="down" else "neutral")
    me_d,me_r = yoy_delta(c_exp,p_exp)

    c1,c2,c3,c4 = st.columns(4)
    with c1: metric_card("Total MRR",     fmt_currency(c_tot), mt_d, mt_r, ACCENT)
    with c2: metric_card("New MRR",       fmt_currency(c_new), mn_d, mn_r, GREEN)
    with c3: metric_card("Churned MRR",   fmt_currency(c_chu), mc_d, mc_r, RED)
    with c4: metric_card("Expansion MRR", fmt_currency(c_exp), me_d, me_r, LIGHT_BLUE)

    movement_colors = {
        "NEW":GREEN,"EXPANSION":ACCENT,"RETAINED":LIGHT_BLUE,
        "CONTRACTION":ORANGE,"CHURN":RED,"NEW_FREE":"#95A5A6"
    }

    section("MRR Waterfall — Monthly Movements")
    mrr_all["MONTH_DATE"] = pd.to_datetime(mrr_all["MONTH_DATE"])
    mrr_agg = mrr_all.groupby(["MONTH_DATE","MRR_MOVEMENT_TYPE"]).agg(MRR=("TOTAL_MRR","sum")).reset_index()
    fig = px.bar(mrr_agg, x="MONTH_DATE", y="MRR", color="MRR_MOVEMENT_TYPE",
                 color_discrete_map=movement_colors, barmode="relative",
                 labels={"MRR":"MRR ($)","MONTH_DATE":"","MRR_MOVEMENT_TYPE":"Movement"})
    for yr in year_filter:
        fig.add_vrect(x0=f"{yr}-01-01", x1=f"{yr}-12-31", fillcolor=ACCENT, opacity=0.06, line_width=0)
    fig.update_layout(hovermode="x unified")
    chart_card(fig)

    col1, col2 = st.columns(2)
    with col1:
        section("MRR by Movement Type")
        mrr_summary = mrr_curr.groupby("MRR_MOVEMENT_TYPE")["TOTAL_MRR"].sum().reset_index()
        mrr_summary = mrr_summary[mrr_summary["MRR_MOVEMENT_TYPE"] != "NEW_FREE"]
        fig2 = px.pie(mrr_summary, names="MRR_MOVEMENT_TYPE", values="TOTAL_MRR",
                      color="MRR_MOVEMENT_TYPE", color_discrete_map=movement_colors, hole=0.5)
        chart_card(fig2)

    with col2:
        section("New vs Churned MRR — Current vs Prev Year")
        def mrr_nvc(df, label):
            d = df[df["MRR_MOVEMENT_TYPE"].isin(["NEW","CHURN"])].copy()
            d["MONTH_DATE"] = pd.to_datetime(d["MONTH_DATE"])
            d["PERIOD"] = label
            return d
        nvc = pd.concat([mrr_nvc(mrr_curr,"Current"), mrr_nvc(mrr_prev,"Prev Year")]) if len(mrr_prev) else mrr_nvc(mrr_curr,"Current")
        nvc_agg = nvc.groupby(["MONTH_DATE","MRR_MOVEMENT_TYPE","PERIOD"])["TOTAL_MRR"].sum().reset_index()
        fig3 = px.line(nvc_agg, x="MONTH_DATE", y="TOTAL_MRR",
                       color="MRR_MOVEMENT_TYPE", line_dash="PERIOD",
                       color_discrete_map={"NEW":GREEN,"CHURN":RED},
                       markers=True, labels={"TOTAL_MRR":"MRR ($)","MONTH_DATE":""})
        chart_card(fig3)

    section("Payment Success Rates by Plan")
    # Free plan has no rows in stg_payments — only pro and enterprise pay
    pay_agg = D["payments"].copy()
    paid_plans = [p for p in plan_filter if p != "free"]
    pay_agg = pay_agg[pay_agg["PLAN"].str.lower().isin(paid_plans)]
    if len(pay_agg) == 0:
        st.info("ℹ️ No payment data for the selected plans. Free users have no payment records.")
    else:
        pay_cols = st.columns(len(pay_agg))
        for i, (_, row) in enumerate(pay_agg.iterrows()):
            total = row["SUCCEEDED"] + row["FAILED"] + row["REFUNDED"]
            rate  = round(row["SUCCEEDED"] / total * 100, 1) if total > 0 else 0
            plan_name = str(row["PLAN"]).lower()
            with pay_cols[i]:
                metric_card(
                    f"{plan_name.upper()} Payment Success",
                    f"{rate}%",
                    delta=f"${row['REVENUE']:,.0f} collected",
                    delta_dir="up",
                    accent=PLAN_COLORS.get(plan_name, ACCENT),
                )


# ═════════════════════════════════════════════
# PAGE: CHURN ANALYSIS
# ═════════════════════════════════════════════
elif page == "📉  Churn Analysis":
    st.markdown('<div class="page-title">Churn Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Understanding who churns, when, and why</div>',
                unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    active_filter_pills(year_filter, month_filter, plan_filter)

    ch_curr = filter_churn(D["fct_churn"], plan_filter, year_filter, month_filter)
    ch_prev = filter_churn(D["fct_churn"], plan_filter, prev_years,  month_filter)

    def chkpi(df):
        return {
            "n":     len(df),
            "mrr":   df["LOST_MRR"].sum() if len(df) else 0,
            "days":  int(df["DAYS_TO_CHURN"].mean()) if len(df) else 0,
            "sess":  round(df["TOTAL_SESSIONS"].mean(),1) if len(df) else 0,
            "bnc":   round(df["BOUNCE_RATE_PCT"].mean(),1) if len(df) else 0,
        }
    cc = chkpi(ch_curr)
    cp = chkpi(ch_prev) if len(ch_prev) else None

    def dch(k, invert=False):
        v, di = yoy_delta(cc[k], cp[k] if cp else None)
        if invert and di=="up": di="down"
        elif invert and di=="down": di="up"
        return v, di

    n_d,n_r   = dch("n",   invert=True)
    mr_d,mr_r = dch("mrr", invert=True)
    da_d,da_r = dch("days")
    se_d,se_r = dch("sess")
    bn_d,bn_r = dch("bnc", invert=True)

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: metric_card("Total Churned",      fmt_number(cc["n"]),    n_d,  n_r,  RED)
    with c2: metric_card("Lost MRR",           fmt_currency(cc["mrr"]),mr_d, mr_r, RED)
    with c3: metric_card("Avg Days to Churn",  f"{cc['days']}d",       da_d, da_r, ORANGE)
    with c4: metric_card("Avg Sessions (pre)", str(cc["sess"]),        se_d, se_r, LIGHT_BLUE)
    with c5: metric_card("Avg Bounce Rate",    f"{cc['bnc']}%",        bn_d, bn_r, PURPLE)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        section("Churn by Stage & Plan")
        cs = (ch_curr.groupby(["CHURN_STAGE","PLAN"])
              .agg(CHURNED_USERS=("USER_ID","count"), LOST_MRR=("LOST_MRR","sum"))
              .reset_index())
        fig = px.bar(cs, x="CHURN_STAGE", y="CHURNED_USERS", color="PLAN", barmode="group",
                     color_discrete_map={k.upper():v for k,v in PLAN_COLORS.items()},
                     category_orders={"CHURN_STAGE":["immediate","early","mid","late"]},
                     labels={"CHURNED_USERS":"Churned Users","CHURN_STAGE":"Stage"})
        chart_card(fig)

    with col2:
        section("Lost MRR by Stage")
        fig2 = px.bar(cs, x="CHURN_STAGE", y="LOST_MRR", color="PLAN", barmode="stack",
                      color_discrete_map={k.upper():v for k,v in PLAN_COLORS.items()},
                      labels={"LOST_MRR":"Lost MRR ($)","CHURN_STAGE":"Stage"})
        chart_card(fig2)

    section("Churn Trend — Current vs Previous Year")
    churn_trend = fp(D["fct_churn"], plan_filter).dropna(subset=["CHURNED_AT"]).copy()
    churn_trend["MONTH_DT"]  = pd.to_datetime(churn_trend["CHURNED_AT"]).dt.to_period("M").dt.to_timestamp()
    churn_trend["YEAR_VAL"]  = churn_trend["CHURN_YEAR"].astype(int)
    show_yrs = sorted(set(year_filter) | set(prev_years))
    ct = (churn_trend[churn_trend["YEAR_VAL"].isin(show_yrs)]
          .groupby(["MONTH_DT","PLAN","YEAR_VAL"]).size()
          .reset_index(name="CHURNED").sort_values("MONTH_DT"))
    fig3 = px.line(ct, x="MONTH_DT", y="CHURNED", color="PLAN", line_dash="YEAR_VAL",
                   color_discrete_map={k.upper():v for k,v in PLAN_COLORS.items()},
                   markers=True, labels={"CHURNED":"Churned Users","MONTH_DT":"","YEAR_VAL":"Year"})
    fig3.update_layout(hovermode="x unified")
    chart_card(fig3)

    col1, col2 = st.columns(2)
    with col1:
        section("Last Feature Used Before Churn")
        lf = (ch_curr.dropna(subset=["LAST_FEATURE_USED"])
              .groupby("LAST_FEATURE_USED").size()
              .reset_index(name="USERS").sort_values("USERS", ascending=False).head(10))
        fig4 = px.bar(lf, x="USERS", y="LAST_FEATURE_USED", orientation="h",
                      color_discrete_sequence=[RED],
                      labels={"USERS":"Churned Users","LAST_FEATURE_USED":""})
        fig4.update_layout(yaxis=dict(autorange="reversed"))
        chart_card(fig4)

    with col2:
        section("NPS of Churned Users")
        nps = (ch_curr.dropna(subset=["NPS_CATEGORY"])
               .groupby("NPS_CATEGORY").size().reset_index(name="USERS"))
        nps_colors = {"detractor":RED,"passive":ORANGE,"promoter":GREEN}
        fig5 = px.pie(nps, names="NPS_CATEGORY", values="USERS",
                      color="NPS_CATEGORY",
                      color_discrete_map={k.upper():v for k,v in nps_colors.items()},
                      hole=0.5)
        chart_card(fig5)


# ═════════════════════════════════════════════
# PAGE: USER ENGAGEMENT
# (sessions file: plan × year × month × platform × depth × duration × entry × exit)
# ═════════════════════════════════════════════
elif page == "👥  User Engagement":
    st.markdown('<div class="page-title">User Engagement</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Session behaviour, depth, and platform usage</div>',
                unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    active_filter_pills(year_filter, month_filter, plan_filter)

    sess_curr = filter_sessions(D["sessions"], plan_filter, year_filter, month_filter)
    sess_prev = filter_sessions(D["sessions"], plan_filter, prev_years,  month_filter)

    # ── KPI aggregation from the single sessions file
    kpi_curr = (sess_curr.groupby("PLAN")
                .agg(TOTAL_SESSIONS=("SESSIONS","sum"),
                     AVG_DUR=("AVG_DURATION_MIN", "mean"),
                     AVG_PGS=("AVG_PAGES","mean"),
                     AVG_FTS=("AVG_FEATURES","mean"),
                     BOUNCE_COUNT=("BOUNCE_COUNT","sum"))
                .reset_index())
    kpi_prev = (sess_prev.groupby("PLAN")
                .agg(TOTAL_SESSIONS=("SESSIONS","sum"),
                     BOUNCE_COUNT=("BOUNCE_COUNT","sum"))
                .reset_index()) if len(sess_prev) else pd.DataFrame()

    ts    = kpi_curr["TOTAL_SESSIONS"].sum()
    ts_p  = kpi_prev["TOTAL_SESSIONS"].sum() if len(kpi_prev) else None
    ts_d, ts_r = yoy_delta(ts, ts_p)

    dur   = round(kpi_curr["AVG_DUR"].mean(), 1)
    pgs   = round(kpi_curr["AVG_PGS"].mean(), 1)
    fts   = round(kpi_curr["AVG_FTS"].mean(), 1)
    bnc   = round(kpi_curr["BOUNCE_COUNT"].sum() / ts * 100, 1) if ts else 0
    bnc_p = round(kpi_prev["BOUNCE_COUNT"].sum() / ts_p * 100, 1) if ts_p else None
    bn_d, bn_r = yoy_delta(bnc, bnc_p)
    bn_r = "down" if bn_r=="up" else ("up" if bn_r=="down" else "neutral")

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: metric_card("Total Sessions",        fmt_number(ts),  ts_d, ts_r, BLUE)
    with c2: metric_card("Avg Duration",          f"{dur} min",    None, "neutral", ACCENT)
    with c3: metric_card("Avg Pages/Session",     str(pgs),        None, "neutral", LIGHT_BLUE)
    with c4: metric_card("Avg Features/Session",  str(fts),        None, "neutral", GREEN)
    with c5: metric_card("Bounce Rate",           f"{bnc}%",       bn_d, bn_r, ORANGE)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        section("Sessions by Platform")
        # GROUP BY platform × plan from the single sessions file
        plat = (sess_curr.groupby(["PLATFORM","PLAN"])["SESSIONS"].sum().reset_index())
        fig = px.bar(plat, x="PLATFORM", y="SESSIONS", color="PLAN", barmode="group",
                     color_discrete_map={k.upper():v for k,v in PLAN_COLORS.items()},
                     labels={"SESSIONS":"Sessions","PLATFORM":""})
        chart_card(fig)

    with col2:
        section("Session Depth Distribution")
        depth = (sess_curr.groupby("DEPTH_BUCKET")["SESSIONS"].sum().reset_index())
        order = ["1 page (bounce)","2-3 pages","4-7 pages","8+ pages (deep)"]
        fig2 = px.bar(depth, x="DEPTH_BUCKET", y="SESSIONS",
                      color_discrete_sequence=[ACCENT],
                      category_orders={"DEPTH_BUCKET":order},
                      labels={"SESSIONS":"Sessions","DEPTH_BUCKET":""})
        chart_card(fig2)

    section("Session Duration by Plan")
    dur_agg = (sess_curr.groupby(["DURATION_BUCKET","PLAN"])["SESSIONS"].sum().reset_index())
    order2 = ["< 1 min","1-5 min","5-15 min","15-60 min","1hr+"]
    fig3 = px.bar(dur_agg, x="DURATION_BUCKET", y="SESSIONS", color="PLAN", barmode="group",
                  color_discrete_map={k.upper():v for k,v in PLAN_COLORS.items()},
                  category_orders={"DURATION_BUCKET":order2},
                  labels={"SESSIONS":"Sessions","DURATION_BUCKET":""})
    fig3.update_layout(hovermode="x unified")
    chart_card(fig3)

    col1, col2 = st.columns(2)
    with col1:
        section("Top Entry Pages")
        entry = (sess_curr.groupby("ENTRY_PAGE")["SESSIONS"].sum()
                 .reset_index().sort_values("SESSIONS", ascending=False).head(10))
        fig4 = px.bar(entry, x="SESSIONS", y="ENTRY_PAGE", orientation="h",
                      color_discrete_sequence=[LIGHT_BLUE],
                      labels={"SESSIONS":"Sessions","ENTRY_PAGE":""})
        fig4.update_layout(yaxis=dict(autorange="reversed"))
        chart_card(fig4)

    with col2:
        section("Top Exit Pages")
        exit_p = (sess_curr.groupby("EXIT_PAGE")["SESSIONS"].sum()
                  .reset_index().sort_values("SESSIONS", ascending=False).head(10))
        fig5 = px.bar(exit_p, x="SESSIONS", y="EXIT_PAGE", orientation="h",
                      color_discrete_sequence=[RED],
                      labels={"SESSIONS":"Sessions","EXIT_PAGE":""})
        fig5.update_layout(yaxis=dict(autorange="reversed"))
        chart_card(fig5)


# ═════════════════════════════════════════════
# PAGE: FEATURE USAGE
# (features file: feature × plan × platform × year × month)
# ═════════════════════════════════════════════
elif page == "🔧  Feature Usage":
    st.markdown('<div class="page-title">Feature Usage</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Which features drive engagement and which are underused</div>',
                unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    active_filter_pills(year_filter, month_filter, plan_filter)

    ft_curr = filter_features(D["features"], plan_filter, year_filter, month_filter)
    ft_prev = filter_features(D["features"], plan_filter, prev_years,  month_filter)

    # ── KPI cards
    te   = ft_curr["EVENTS"].sum()
    te_p = ft_prev["EVENTS"].sum() if len(ft_prev) else None
    te_d, te_r = yoy_delta(te, te_p)

    ud   = ft_curr["UNIQUE_USERS"].sum()
    ud_p = ft_prev["UNIQUE_USERS"].sum() if len(ft_prev) else None
    ud_d, ud_r = yoy_delta(ud, ud_p)

    avg_dur   = round(ft_curr["AVG_DURATION_SEC"].mean(), 1)
    avg_dur_p = round(ft_prev["AVG_DURATION_SEC"].mean(), 1) if len(ft_prev) else None
    dr_d, dr_r = yoy_delta(avg_dur, avg_dur_p)

    distinct_features = ft_curr["FEATURE_NAME"].nunique()

    c1,c2,c3,c4 = st.columns(4)
    with c1: metric_card("Total Feature Events", fmt_number(te),           te_d, te_r, BLUE)
    with c2: metric_card("Unique User-Days",      fmt_number(ud),           ud_d, ud_r, LIGHT_BLUE)
    with c3: metric_card("Distinct Features",     str(distinct_features),  None, "neutral", ACCENT)
    with c4: metric_card("Avg Duration",          f"{avg_dur}s",           dr_d, dr_r, GREEN)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Feature usage by plan — GROUP BY feature × plan
    section("Feature Usage by Plan")
    fp_agg = (ft_curr.groupby(["FEATURE_NAME","PLAN"])
              .agg(EVENTS=("EVENTS","sum"), UNIQUE_USERS=("UNIQUE_USERS","sum"))
              .reset_index())
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(fp_agg, x="FEATURE_NAME", y="EVENTS", color="PLAN", barmode="group",
                     color_discrete_map={k.upper():v for k,v in PLAN_COLORS.items()},
                     labels={"EVENTS":"Total Events","FEATURE_NAME":""})
        fig.update_layout(xaxis_tickangle=-35)
        chart_card(fig, "Total Events by Feature")

    with col2:
        fig2 = px.bar(fp_agg, x="FEATURE_NAME", y="UNIQUE_USERS", color="PLAN", barmode="group",
                      color_discrete_map={k.upper():v for k,v in PLAN_COLORS.items()},
                      labels={"UNIQUE_USERS":"Unique Users","FEATURE_NAME":""})
        fig2.update_layout(xaxis_tickangle=-35)
        chart_card(fig2, "Unique Users by Feature")

    # ── Trend — GROUP BY event_month × feature_name (already monthly from SQL)
    section("Feature Usage Trend (Top 5 Features)")
    ft_trend = (ft_curr.groupby(["EVENT_MONTH","FEATURE_NAME"])["EVENTS"].sum().reset_index())
    ft_trend["EVENT_MONTH"] = pd.to_datetime(ft_trend["EVENT_MONTH"])
    top5 = ft_trend.groupby("FEATURE_NAME")["EVENTS"].sum().nlargest(5).index.tolist()
    fig3 = px.line(ft_trend[ft_trend["FEATURE_NAME"].isin(top5)],
                   x="EVENT_MONTH", y="EVENTS", color="FEATURE_NAME", markers=True,
                   labels={"EVENTS":"Events","EVENT_MONTH":"","FEATURE_NAME":"Feature"})
    fig3.update_layout(hovermode="x unified")
    chart_card(fig3)

    # ── Platform heatmap — GROUP BY feature × platform
    section("Feature × Platform Heatmap")
    fplat = (ft_curr.groupby(["FEATURE_NAME","PLATFORM"])["EVENTS"].sum().reset_index())
    pivot = fplat.pivot(index="FEATURE_NAME", columns="PLATFORM", values="EVENTS").fillna(0)
    fig4 = px.imshow(pivot, color_continuous_scale=["#EBF4FA", BLUE],
                     labels=dict(color="Events"), aspect="auto")
    chart_card(fig4)


# ═════════════════════════════════════════════
# PAGE: RETENTION
# ═════════════════════════════════════════════
elif page == "🔁  Retention":
    st.markdown('<div class="page-title">Cohort Retention</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">How well we retain users over time by signup cohort</div>',
                unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    active_filter_pills(year_filter, month_filter, plan_filter)

    retention = D["fct_retention"].copy()
    retention = fy(retention, year_filter, "COHORT_YEAR")
    retention["COHORT_MONTH"] = pd.to_datetime(retention["COHORT_MONTH"]).dt.strftime("%Y-%m")

    section("Retention Heatmap — % Active by Cohort")
    pivot_ret = retention.pivot(index="COHORT_MONTH", columns="MONTHS_SINCE_SIGNUP", values="RETENTION_PCT")
    fig = px.imshow(pivot_ret,
                    color_continuous_scale=["#FEF0F0","#EBF4FA",BLUE],
                    labels=dict(x="Months Since Signup", y="Cohort", color="Retention %"),
                    zmin=0, zmax=100, aspect="auto", text_auto=".0f")
    fig.update_traces(textfont_size=8)
    fig.update_layout(height=500)
    chart_card(fig)

    col1, col2 = st.columns(2)
    with col1:
        section("Retention Curves — Selected Cohorts")
        top_cohorts = (retention.groupby("COHORT_MONTH")["ACTIVE_USERS"].sum()
                       .nlargest(6).index.tolist())
        fig2 = px.line(retention[retention["COHORT_MONTH"].isin(top_cohorts)],
                       x="MONTHS_SINCE_SIGNUP", y="RETENTION_PCT", color="COHORT_MONTH",
                       markers=True,
                       labels={"RETENTION_PCT":"Retention %","MONTHS_SINCE_SIGNUP":"Months Since Signup"})
        fig2.update_layout(yaxis_range=[0,105])
        chart_card(fig2)

    with col2:
        section("Avg Retention at Key Milestones")
        summary = retention[retention["MONTHS_SINCE_SIGNUP"].isin([1,3,6,12])].copy()
        summary_avg = summary.groupby("MONTHS_SINCE_SIGNUP")["RETENTION_PCT"].mean().reset_index()
        summary_avg.columns = ["MONTH","AVG_RETENTION"]
        summary_avg["AVG_RETENTION"] = summary_avg["AVG_RETENTION"].round(1)
        fig3 = px.bar(summary_avg, x="MONTH", y="AVG_RETENTION",
                      color="AVG_RETENTION", color_continuous_scale=["#E74C3C",ACCENT,BLUE],
                      text="AVG_RETENTION")
        fig3.update_traces(texttemplate="%{text}%", textposition="outside")
        fig3.update_layout(showlegend=False, yaxis_range=[0,110],
                           coloraxis_showscale=False,
                           xaxis_title="Month", yaxis_title="Avg Retention %")
        chart_card(fig3)

    section("Cohort Size Over Time")
    cohort_sizes = retention[retention["MONTHS_SINCE_SIGNUP"]==0][["COHORT_MONTH","COHORT_SIZE"]].copy()
    cohort_sizes["COHORT_MONTH"] = pd.to_datetime(cohort_sizes["COHORT_MONTH"])
    fig4 = px.area(cohort_sizes, x="COHORT_MONTH", y="COHORT_SIZE",
                   color_discrete_sequence=[ACCENT],
                   labels={"COHORT_SIZE":"Users in Cohort","COHORT_MONTH":""})
    fig4.update_traces(fillcolor="rgba(0,180,216,0.15)")
    chart_card(fig4)