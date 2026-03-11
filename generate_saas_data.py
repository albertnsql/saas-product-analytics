"""
Realistic SaaS Data Generator
Generates 3 years of synthetic product analytics data for a B2B SaaS platform.
"""

import pandas as pd
import numpy as np
import random
import uuid
import os
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
np.random.seed(42)
random.seed(42)

# ------------------------------------------------
# CONFIG
# ------------------------------------------------

NUM_USERS = 40000
START_DATE = datetime(2023, 1, 1)
END_DATE   = datetime(2025, 12, 31)
TOTAL_DAYS = (END_DATE - START_DATE).days

PLANS = ["free", "pro", "enterprise"]
PLAN_WEIGHTS = [0.65, 0.28, 0.07]

PLAN_MRR = {"free": 0, "pro": 49, "enterprise": 299}

# Country distribution with plan skew applied later
COUNTRIES = ["US", "UK", "DE", "IN", "CA", "AU", "FR", "NL", "SG", "BR"]
COUNTRY_BASE_WEIGHTS = [0.30, 0.10, 0.10, 0.15, 0.10, 0.05, 0.08, 0.06, 0.03, 0.03]

# Country weights per plan (enterprise skews US/DE/UK, free skews IN/BR)
COUNTRY_WEIGHTS_BY_PLAN = {
    "free":       [0.25, 0.08, 0.08, 0.22, 0.08, 0.05, 0.07, 0.05, 0.05, 0.07],
    "pro":        [0.32, 0.12, 0.11, 0.10, 0.11, 0.06, 0.08, 0.06, 0.02, 0.02],
    "enterprise": [0.45, 0.15, 0.15, 0.04, 0.08, 0.04, 0.05, 0.02, 0.01, 0.01],
}

# Timezone offsets by country (UTC offset hours, approximate business hours anchor)
COUNTRY_TZ_OFFSET = {
    "US": -5, "UK": 0, "DE": 1, "IN": 5.5, "CA": -5,
    "AU": 10, "FR": 1, "NL": 1, "SG": 8, "BR": -3,
}

# Feature usage weights per plan — realistic adoption curves
FEATURES = [
    "view_dashboard", "search", "filter_tasks", "comment_task",
    "create_project", "upload_file", "set_deadline", "invite_teammate",
    "export_report", "view_analytics",
]
FEATURE_WEIGHTS_BY_PLAN = {
    "free":       [0.25, 0.20, 0.18, 0.12, 0.10, 0.06, 0.05, 0.02, 0.01, 0.01],
    "pro":        [0.20, 0.15, 0.14, 0.12, 0.10, 0.08, 0.07, 0.06, 0.04, 0.04],
    "enterprise": [0.15, 0.10, 0.10, 0.10, 0.09, 0.08, 0.08, 0.08, 0.08, 0.14],
}

PAGES = [
    "/dashboard", "/projects", "/tasks", "/reports",
    "/settings", "/team", "/profile", "/billing", "/search", "/notifications"
]
PAGE_WEIGHTS_BY_PLAN = {
    "free":       [0.30, 0.20, 0.20, 0.05, 0.08, 0.04, 0.06, 0.02, 0.03, 0.02],
    "pro":        [0.22, 0.18, 0.18, 0.10, 0.08, 0.07, 0.05, 0.04, 0.04, 0.04],
    "enterprise": [0.18, 0.15, 0.14, 0.14, 0.07, 0.12, 0.04, 0.06, 0.04, 0.06],
}

REFERRAL_SOURCES = ["organic_search", "paid_search", "word_of_mouth", "product_hunt", "linkedin", "direct", "partner"]
REFERRAL_WEIGHTS_BY_PLAN = {
    "free":       [0.35, 0.15, 0.20, 0.10, 0.08, 0.08, 0.04],
    "pro":        [0.25, 0.20, 0.25, 0.05, 0.12, 0.08, 0.05],
    "enterprise": [0.10, 0.15, 0.30, 0.02, 0.20, 0.08, 0.15],
}

os.makedirs("data", exist_ok=True)


# ------------------------------------------------
# HELPERS
# ------------------------------------------------

def s_curve_signup():
    """
    S-curve growth: slow start in 2023, inflection ~mid-2023, 
    accelerating through 2024, slight plateau in late 2025.
    Models a typical VC-backed SaaS growth trajectory.
    """
    # Logistic CDF — maps uniform draw to day offset biased toward later dates
    u = random.random()
    # Inflection at ~40% of range, steep growth
    k = 8.0  # steepness
    x0 = 0.40  # inflection point
    # Inverse logistic
    if u <= 0 or u >= 1:
        u = max(0.001, min(0.999, u))
    logit = np.log(u / (1 - u))
    x = logit / k + x0
    x = max(0.0, min(1.0, x))
    return START_DATE + timedelta(days=int(x * TOTAL_DAYS))


def realistic_timestamp(start, end, country):
    """Generate a timestamp biased toward business hours in the user's timezone."""
    if start >= end:
        return start
    delta = end - start
    ts = start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))

    # Weekend suppression (lower for enterprise/async tools)
    if ts.weekday() >= 5 and random.random() < 0.68:
        ts += timedelta(days=random.randint(1, 2))

    # Business hours bias adjusted for local timezone
    if random.random() < 0.65:
        tz_offset = COUNTRY_TZ_OFFSET.get(country, 0)
        local_business_start = max(0, 8 - int(tz_offset))
        local_business_end   = min(23, 19 - int(tz_offset))
        if local_business_start < local_business_end:
            ts = ts.replace(hour=random.randint(local_business_start, local_business_end))

    return min(ts, END_DATE)


def churn_date_for_user(signup, plan, churned, last_active):
    """
    If churned, return a date between signup and last_active.
    Churn is more likely in months 1-3 (early churn) or after 12 months (renewal churn).
    Fully clamped — safe regardless of how short the active window is.
    """
    if not churned:
        return None
    available_days = max(1, (last_active - signup).days)

    early_lo  = min(14, available_days)
    early_hi  = max(early_lo, min(90, available_days))
    late_lo   = min(91, available_days)
    late_hi   = max(late_lo, available_days)

    if random.random() < 0.60:
        days = random.randint(early_lo, early_hi)
    else:
        days = random.randint(late_lo, late_hi)
    return signup + timedelta(days=days)


def base_sessions_for_plan(plan):
    return {"free": 20, "pro": 80, "enterprise": 220}[plan]


def generate_events_for_user(user_id, plan, country, signup, last_active, activity_mult):
    """
    Single unified generator: sessions are the atomic unit.
    Tracks and pages are born *inside* each session window, and their
    counts are driven by session.page_count / session.feature_count.
    Returns (sessions, tracks, pages) as three lists.
    """
    n_sessions = max(1, int(base_sessions_for_plan(plan) * activity_mult))
    page_weights    = PAGE_WEIGHTS_BY_PLAN[plan]
    feature_weights = FEATURE_WEIGHTS_BY_PLAN[plan]

    sessions, tracks, pages = [], [], []

    for _ in range(n_sessions):
        session_id = str(uuid.uuid4())
        started_at = realistic_timestamp(signup, last_active, country)

        duration_seconds = max(10, int(np.random.lognormal(mean=5.5, sigma=1.1)))
        ended_at = min(started_at + timedelta(seconds=duration_seconds), END_DATE)
        if ended_at <= started_at:
            ended_at = started_at + timedelta(seconds=1)

        platform = random.choices(["web", "mobile", "api"], weights=[70, 20, 10])[0]

        page_count    = 1 if platform == "api" else max(1, int(np.random.lognormal(mean=1.5, sigma=0.8)))
        feature_count = max(0, int(np.random.lognormal(mean=1.2, sigma=0.9)))

        page_sequence = [random.choices(PAGES, weights=page_weights)[0] for _ in range(page_count)]
        entry_page = page_sequence[0]
        exit_page  = page_sequence[-1]
        is_bounce  = (page_count == 1)

        sessions.append({
            "session_id":        session_id,
            "user_id":           user_id,
            "plan":              plan,
            "country":           country,
            "started_at":        started_at,
            "ended_at":          ended_at,
            "duration_seconds":  (ended_at - started_at).seconds,
            "platform":          platform,
            "page_count":        page_count,
            "feature_count":     feature_count,
            "entry_page":        entry_page,
            "exit_page":         exit_page,
            "is_bounce":         is_bounce,
            "days_since_signup": (started_at - signup).days,
        })

        # Page events: exactly page_count rows, timestamps inside session window
        for page_url in page_sequence:
            pages.append({
                "message_id":  str(uuid.uuid4()),
                "user_id":     user_id,
                "session_id":  session_id,
                "page_url":    page_url,
                "received_at": realistic_timestamp(started_at, ended_at, country),
                "platform":    "web" if platform != "mobile" else "mobile",
            })

        # Track events: exactly feature_count rows, timestamps inside session window
        for _ in range(feature_count):
            tracks.append({
                "message_id":   str(uuid.uuid4()),
                "user_id":      user_id,
                "session_id":   session_id,
                "event":        "feature_used",
                "feature_name": random.choices(FEATURES, weights=feature_weights)[0],
                "received_at":  realistic_timestamp(started_at, ended_at, country),
                "platform":     platform,
                "duration_ms":  int(np.random.lognormal(mean=7.5, sigma=1.2)),
            })

    return sessions, tracks, pages


# ------------------------------------------------
# USERS
# ------------------------------------------------

print("Generating users...")

users = []
for i in range(NUM_USERS):
    plan = random.choices(PLANS, weights=PLAN_WEIGHTS)[0]
    signup = s_curve_signup()
    country = random.choices(COUNTRIES, weights=COUNTRY_WEIGHTS_BY_PLAN[plan])[0]

    # Activity multiplier: enterprise users structurally more active, not just by luck
    base_activity = {"free": 0.6, "pro": 1.0, "enterprise": 1.8}[plan]
    activity = min(round(base_activity * (np.random.pareto(1.5) + 0.4), 2), 15.0)

    churn_rate = {"free": 0.38, "pro": 0.14, "enterprise": 0.05}[plan]
    churned = random.random() < churn_rate

    # Last active: churned users go cold; retained users stay warm toward END_DATE
    if churned:
        max_active_days = min(600, (END_DATE - signup).days)
        last_active = signup + timedelta(days=random.randint(14, max(15, max_active_days)))
        last_active = min(last_active, END_DATE - timedelta(days=30))
    else:
        # Retained users: last active within 45 days of END_DATE
        last_active = END_DATE - timedelta(days=random.randint(0, 45))
        last_active = max(last_active, signup + timedelta(days=1))

    churn_dt = churn_date_for_user(signup, plan, churned, last_active)

    # Onboarding: enterprise almost always completes, free rarely does
    onboarding_rate = {"free": 0.28, "pro": 0.65, "enterprise": 0.91}[plan]
    onboarding_completed = random.random() < onboarding_rate

    referral_source = random.choices(REFERRAL_SOURCES, weights=REFERRAL_WEIGHTS_BY_PLAN[plan])[0]

    # NPS score (only ~30% respond; enterprise responds more)
    nps_response_rate = {"free": 0.15, "pro": 0.30, "enterprise": 0.55}[plan]
    if random.random() < nps_response_rate:
        # Enterprise skews promoter, free skews detractor
        nps_weights = {
            "free":       [0.30, 0.35, 0.35],   # detractor / passive / promoter
            "pro":        [0.15, 0.30, 0.55],
            "enterprise": [0.05, 0.20, 0.75],
        }[plan]
        category = random.choices(["detractor", "passive", "promoter"], weights=nps_weights)[0]
        nps_score = {
            "detractor": random.randint(0, 6),
            "passive":   random.randint(7, 8),
            "promoter":  random.randint(9, 10),
        }[category]
    else:
        nps_score = None

    users.append({
        "user_id":              f"user_{i+1}",
        "signup_date":          signup,
        "plan":                 plan,
        "country":              country,
        "email":                fake.email(),
        "company":              fake.company(),
        "activity_mult":        activity,
        "churned":              churned,
        "churn_date":           churn_dt,
        "last_active":          last_active,
        "onboarding_completed": onboarding_completed,
        "referral_source":      referral_source,
        "nps_score":            nps_score,
    })

users_df = pd.DataFrame(users)
users_df.to_csv("data/users.csv", index=False)
print(f"Users generated: {len(users_df)}")


# ------------------------------------------------
# RAW IDENTIFIES
# ------------------------------------------------

print("Generating raw_identifies...")

identifies = []
for _, u in users_df.iterrows():
    identifies.append({
        "message_id":           str(uuid.uuid4()),
        "user_id":              u.user_id,
        "email":                u.email,
        "company":              u.company,
        "plan":                 u.plan,
        "country":              u.country,
        "referral_source":      u.referral_source,
        "onboarding_completed": u.onboarding_completed,
        "event_type":           "signup",
        "received_at":          u.signup_date,
    })

identifies_df = pd.DataFrame(identifies)
identifies_df.to_csv("data/raw_identifies.csv", index=False)
print(f"raw_identifies: {len(identifies_df)}")


# ------------------------------------------------
# PLAN CHANGE EVENTS (upgrades / downgrades)
# ------------------------------------------------

print("Generating plan_changes...")

plan_changes = []
UPGRADE_PATH = {"free": "pro", "pro": "enterprise"}
DOWNGRADE_PATH = {"enterprise": "pro", "pro": "free"}

for _, u in users_df.iterrows():
    # ~12% of free users upgrade to pro; ~8% of pro upgrade to enterprise
    upgrade_rate = {"free": 0.12, "pro": 0.08, "enterprise": 0.0}[u.plan]
    # ~5% of pro downgrade to free after churn; ~10% enterprise to pro
    downgrade_rate = {"free": 0.0, "pro": 0.05, "enterprise": 0.10}[u.plan]

    if random.random() < upgrade_rate and not u.churned:
        max_days = max(31, (u.last_active - u.signup_date).days - 1)
        days_in = random.randint(30, max_days) if max_days > 30 else 30
        change_date = u.signup_date + timedelta(days=days_in)
        plan_changes.append({
            "change_id":    str(uuid.uuid4()),
            "user_id":      u.user_id,
            "from_plan":    u.plan,
            "to_plan":      UPGRADE_PATH[u.plan],
            "change_type":  "upgrade",
            "changed_at":   change_date,
        })
    elif random.random() < downgrade_rate and u.churned and u.churn_date is not None:
        plan_changes.append({
            "change_id":    str(uuid.uuid4()),
            "user_id":      u.user_id,
            "from_plan":    u.plan,
            "to_plan":      DOWNGRADE_PATH[u.plan],
            "change_type":  "downgrade",
            "changed_at":   u.churn_date,
        })

plan_changes_df = pd.DataFrame(plan_changes)
plan_changes_df.to_csv("data/plan_changes.csv", index=False)
print(f"plan_changes: {len(plan_changes_df)}")


# ------------------------------------------------
# SESSIONS, TRACKS & PAGES  (one unified loop — events born inside session windows)
# ------------------------------------------------

print("Generating sessions, tracks, and pages...")

all_sessions, all_tracks, all_pages = [], [], []

for _, u in users_df.iterrows():
    s, t, p = generate_events_for_user(
        user_id       = u.user_id,
        plan          = u.plan,
        country       = u.country,
        signup        = u.signup_date,
        last_active   = u.last_active,
        activity_mult = u.activity_mult,
    )
    all_sessions.extend(s)
    all_tracks.extend(t)
    all_pages.extend(p)

sessions_df = pd.DataFrame(all_sessions)
sessions_df.to_csv("data/sessions.csv", index=False)
print(f"sessions:   {len(sessions_df):>8,}")

tracks_df = pd.DataFrame(all_tracks)
tracks_df.to_csv("data/raw_tracks.csv", index=False)
print(f"raw_tracks: {len(tracks_df):>8,}")

pages_df = pd.DataFrame(all_pages)
pages_df.to_csv("data/raw_pages.csv", index=False)
print(f"raw_pages:  {len(pages_df):>8,}")


# ------------------------------------------------
# SUBSCRIPTIONS
# ------------------------------------------------

print("Generating subscriptions...")

subs = []
for _, u in users_df.iterrows():
    subs.append({
        "subscription_id": str(uuid.uuid4()),
        "user_id":         u.user_id,
        "plan":            u.plan,
        "start_date":      u.signup_date,
        "end_date":        u.churn_date if u.churned else None,
        "mrr":             PLAN_MRR[u.plan],
        "status":          "cancelled" if u.churned else "active",
    })

subs_df = pd.DataFrame(subs)
subs_df.to_csv("data/subscriptions.csv", index=False)
print(f"subscriptions: {len(subs_df)}")


# ------------------------------------------------
# PAYMENTS
# ------------------------------------------------

print("Generating payments...")

FAILURE_RATE = 0.04   # 4% of charges fail
REFUND_RATE  = 0.015  # 1.5% of successful payments get refunded

payments = []
for _, s in subs_df.iterrows():
    if s.plan == "free":
        continue

    # Number of billing months = until churn or until END_DATE
    end = s.end_date if pd.notna(s.end_date) and s.end_date else END_DATE
    end = min(pd.Timestamp(end), pd.Timestamp(END_DATE))
    start = pd.Timestamp(s.start_date)
    months = max(1, int((end - start).days / 30))

    for m in range(months):
        payment_date = start + timedelta(days=30 * m)
        if payment_date > pd.Timestamp(END_DATE):
            break

        failed = random.random() < FAILURE_RATE
        status = "failed" if failed else "succeeded"
        amount = PLAN_MRR[s.plan] if not failed else 0

        payments.append({
            "payment_id":   str(uuid.uuid4()),
            "user_id":      s.user_id,
            "amount":       amount,
            "payment_date": payment_date,
            "status":       status,
            "plan":         s.plan,
        })

        # Possible refund on successful payment
        if not failed and random.random() < REFUND_RATE:
            refund_days = random.randint(1, 14)
            payments.append({
                "payment_id":   str(uuid.uuid4()),
                "user_id":      s.user_id,
                "amount":       -PLAN_MRR[s.plan],
                "payment_date": payment_date + timedelta(days=refund_days),
                "status":       "refunded",
                "plan":         s.plan,
            })

payments_df = pd.DataFrame(payments)
payments_df.to_csv("data/payments.csv", index=False)
print(f"payments: {len(payments_df)}")


# ------------------------------------------------
# SUPPORT TICKETS
# ------------------------------------------------

print("Generating support_tickets...")

TICKET_CATEGORIES = ["billing", "bug_report", "feature_request", "onboarding", "account_access", "performance"]
TICKET_CAT_WEIGHTS_BY_PLAN = {
    "free":       [0.10, 0.25, 0.30, 0.25, 0.07, 0.03],
    "pro":        [0.20, 0.20, 0.25, 0.15, 0.10, 0.10],
    "enterprise": [0.25, 0.15, 0.15, 0.10, 0.15, 0.20],
}
TICKET_PRIORITY_BY_PLAN = {
    "free":       ["low", "medium"],
    "pro":        ["low", "medium", "high"],
    "enterprise": ["medium", "high", "urgent"],
}

tickets = []
for _, u in users_df.iterrows():
    # Ticket rate: enterprise opens more tickets per user
    ticket_rate = {"free": 0.08, "pro": 0.25, "enterprise": 0.70}[u.plan]
    if random.random() > ticket_rate:
        continue

    n_tickets = random.randint(1, {"free": 2, "pro": 5, "enterprise": 12}[u.plan])
    for _ in range(n_tickets):
        created = realistic_timestamp(u.signup_date, u.last_active, u.country)
        resolve_days = np.random.lognormal(mean=1.5, sigma=0.8)
        resolved_at = created + timedelta(days=resolve_days)

        tickets.append({
            "ticket_id":  str(uuid.uuid4()),
            "user_id":    u.user_id,
            "plan":       u.plan,
            "category":   random.choices(TICKET_CATEGORIES, weights=TICKET_CAT_WEIGHTS_BY_PLAN[u.plan])[0],
            "priority":   random.choice(TICKET_PRIORITY_BY_PLAN[u.plan]),
            "created_at": created,
            "resolved_at": resolved_at if random.random() < 0.88 else None,
            "csat_score": random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.08, 0.15, 0.32, 0.40])[0]
                          if random.random() < 0.45 else None,
        })

tickets_df = pd.DataFrame(tickets)
tickets_df.to_csv("data/support_tickets.csv", index=False)
print(f"support_tickets: {len(tickets_df)}")


# ------------------------------------------------
# SUMMARY STATS
# ------------------------------------------------

print("\n=== DATA GENERATION COMPLETE ===")
print(f"Users:            {len(users_df):>8,}")
print(f"Identifies:       {len(identifies_df):>8,}")
print(f"Plan changes:     {len(plan_changes_df):>8,}")
print(f"Sessions:         {len(sessions_df):>8,}")
print(f"Track events:     {len(tracks_df):>8,}")
print(f"Page events:      {len(pages_df):>8,}")
print(f"Subscriptions:    {len(subs_df):>8,}")
print(f"Payments:         {len(payments_df):>8,}")
print(f"Support tickets:  {len(tickets_df):>8,}")

paid_users = users_df[users_df.plan != "free"]
churn_by_plan = users_df.groupby("plan")["churned"].mean()
print("\nChurn rates by plan:")
print(churn_by_plan.to_string())

total_mrr = subs_df[subs_df.status == "active"]["mrr"].sum()
print(f"\nActive MRR (snapshot): ${total_mrr:,.0f}")