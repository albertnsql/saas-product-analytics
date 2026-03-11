# 📊 saas_dbt — B2B SaaS Analytics with dbt + Snowflake

> A production-grade dbt transformation layer that turns raw event and transactional data into analytics-ready mart tables for a B2B SaaS product — covering revenue, churn, product engagement, and cohort retention.

![dbt](https://img.shields.io/badge/dbt-1.11-orange?logo=dbt&logoColor=white)
![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?logo=snowflake&logoColor=white)
![Models](https://img.shields.io/badge/models-16-blue)
![Tests](https://img.shields.io/badge/tests-39%20passing-brightgreen)
![Rows](https://img.shields.io/badge/rows-45.6M-lightgrey)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Data Sources](#data-sources)
- [Model Reference](#model-reference)
  - [Staging Layer](#staging-layer)
  - [Intermediate Layer](#intermediate-layer)
  - [Marts Layer](#marts-layer)
- [Test Coverage](#test-coverage)
- [Row Counts](#row-counts)
- [Setup & Installation](#setup--installation)
- [Running the Project](#running-the-project)
- [Project Structure](#project-structure)

---

## Overview

This dbt project transforms 9 raw Snowflake tables (~45.6M rows of synthetic B2B SaaS data) into 6 analytics mart tables across three business domains:

| Domain | Models | What it answers |
|---|---|---|
| **Core** | `dim_users`, `fct_retention` | Who are our users? How well do we retain them? |
| **Finance** | `fct_mrr`, `fct_churn` | What does our revenue look like? Who churns and why? |
| **Product** | `fct_sessions`, `fct_feature_usage` | How are users engaging with the product? |

The marts feed directly into a **Streamlit + Plotly** dashboard for self-serve business analytics.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAW LAYER  (Snowflake)                        │
│  users  sessions  raw_tracks  raw_pages  payments  subscriptions │
│  raw_identifies  plan_changes  support_tickets                   │
└────────────────────────────┬────────────────────────────────────┘
                             │  {{ source('raw', ...) }}
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   STAGING LAYER  (VIEWs)                        │
│  stg_users       stg_sessions      stg_tracks      stg_pages    │
│  stg_payments    stg_subscriptions stg_plan_changes             │
│  stg_support_tickets                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │  {{ ref('stg_...') }}
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                INTERMEDIATE LAYER  (VIEWs)                      │
│  int_user_activity          int_monthly_revenue                 │
└────────────────────────────┬────────────────────────────────────┘
                             │  {{ ref('int_...') }}
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MARTS LAYER  (TABLEs)                        │
│                                                                 │
│   core/               finance/             product/             │
│   ├── dim_users        ├── fct_mrr          ├── fct_sessions    │
│   └── fct_retention    └── fct_churn        └── fct_feature_usage│
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                   Streamlit Dashboard
```

---

## Data Sources

All 9 source tables live in the `saas_analytics.raw` schema in Snowflake.

| Source Table | Rows | Description |
|---|---|---|
| `users` | 40,000 | One row per user — signup info, plan, churn status |
| `sessions` | 4,221,361 | One row per user session |
| `raw_tracks` | 18,899,450 | Feature interaction events (one per feature click) |
| `raw_pages` | 22,088,021 | Page view events |
| `payments` | 271,549 | All payment transactions including failures and refunds |
| `subscriptions` | 40,000 | One subscription row per user |
| `raw_identifies` | 40,000 | Signup identify events from the event stream |
| `plan_changes` | 2,767 | Upgrade and downgrade events |
| `support_tickets` | 24,224 | Customer support tickets |

---

## Model Reference

### Staging Layer

> All staging models are materialised as **VIEWs** in the `staging` schema. They rename columns, cast types, and add lightweight derived fields. No business logic here.

---

#### `stg_users`
Cleans the raw users table and derives key fields used across all downstream models.

**Key derived columns:**
| Column | Logic |
|---|---|
| `mrr` | `0` / `49` / `299` based on `plan` |
| `nps_category` | `detractor` (0–6) / `passive` (7–8) / `promoter` (9–10) |
| `days_to_churn` | `DATEDIFF(signup_date, churn_date)` |
| `days_active` | `DATEDIFF(signup_date, last_active)` |
| `is_churned` | Cast to `BOOLEAN` |

---

#### `stg_sessions`
Cleans the raw sessions table. Adds time-grain columns and computed duration.

**Key derived columns:**
| Column | Logic |
|---|---|
| `duration_minutes` | `duration_seconds / 60.0` |
| `session_date` | `DATE_TRUNC('day', started_at)` |
| `session_week` | `DATE_TRUNC('week', started_at)` |
| `session_month` | `DATE_TRUNC('month', started_at)` |
| `day_of_week` | `DAYOFWEEK(started_at)` |
| `hour_of_day` | `HOUR(started_at)` |

---

#### `stg_tracks`
Cleans feature interaction events. Adds `duration_seconds` conversion from `duration_ms`.

---

#### `stg_pages`
Cleans page view events. Adds `event_date` and `event_month` time-grain columns.

---

#### `stg_payments`
Cleans payment records. Adds boolean flags and separates refund amounts from collected amounts.

**Key derived columns:**
| Column | Logic |
|---|---|
| `is_successful` | `status = 'succeeded'` |
| `is_failed` | `status = 'failed'` |
| `is_refunded` | `status = 'refunded'` |
| `collected_amount` | Amount where succeeded and `amount > 0` |
| `refund_amount` | `ABS(amount)` where `amount < 0` |

---

#### `stg_subscriptions`
Cleans subscription records. Derives `subscription_length_days`, `is_active`, and `is_churned` flags.

---

#### `stg_plan_changes`
Cleans upgrade/downgrade events. Derives the MRR impact of each plan change.

**Key derived columns:**
| Column | Logic |
|---|---|
| `from_mrr` | MRR value of the previous plan |
| `to_mrr` | MRR value of the new plan |
| `mrr_delta` | `to_mrr - from_mrr` (positive = upgrade, negative = downgrade) |

---

#### `stg_support_tickets`
Cleans support tickets. Derives resolution time and CSAT category.

**Key derived columns:**
| Column | Logic |
|---|---|
| `is_resolved` | `resolved_at IS NOT NULL` |
| `time_to_resolve_hours` | `DATEDIFF('hour', created_at, resolved_at)` |
| `csat_category` | `satisfied` (4–5) / `neutral` (3) / `dissatisfied` (1–2) |

---

### Intermediate Layer

> Intermediate models are materialised as **VIEWs** in the `intermediate` schema. They perform heavy joins and aggregations that would be repeated across multiple mart models.

---

#### `int_user_activity`
Aggregates session, feature, and page activity **per user**. Used by `dim_users` and `fct_churn`.

**Sources joined:** `stg_sessions` + `stg_tracks` + `stg_pages`

**Output columns:**
| Column | Description |
|---|---|
| `total_sessions` | Total session count |
| `total_session_hours` | Total session time in hours |
| `avg_session_duration_seconds` | Mean session duration |
| `bounce_rate_pct` | `bounce_sessions / total_sessions × 100` |
| `active_days` | Distinct days with at least one session |
| `active_months` | Distinct months with at least one session |
| `distinct_features_used` | Count of unique features ever used |
| `most_used_feature` | Modal feature name |
| `total_page_views` | Total page view count |
| `most_visited_page` | Modal page URL |

---

#### `int_monthly_revenue`
Builds a **date-spine** (36 months, Jan 2023 → Dec 2025) and classifies each user-month as a revenue movement type. Foundation for `fct_mrr`.

**Sources joined:** `stg_users` × date spine (Snowflake `GENERATOR`)

**Movement classification logic:**
| Movement Type | Condition |
|---|---|
| `new` | First month for this user, paid plan |
| `new_free` | First month for this user, free plan |
| `expansion` | `mrr > prev_mrr` |
| `contraction` | `mrr < prev_mrr AND mrr > 0` |
| `retained` | `mrr = prev_mrr` |
| `churn` | `mrr = 0 AND prev_mrr > 0` |

---

### Marts Layer

> All mart models are materialised as **TABLEs** in the `marts` schema, split across `core/`, `finance/`, and `product/` sub-schemas.

---

#### `dim_users` — Core
**One row per user.** The master user dimension table. Joins identity, plan, activity, and support data into a single wide table.

| Column Group | Columns |
|---|---|
| Identity | `user_id`, `email`, `company`, `country`, `referral_source` |
| Plan | `plan`, `mrr` |
| Dates | `signed_up_at`, `signup_month`, `last_active_at`, `churned_at`, `cohort_month` |
| Status | `is_churned`, `onboarding_completed`, `days_to_churn`, `days_active` |
| NPS | `nps_score`, `nps_category` |
| Activity | `total_sessions`, `bounce_rate_pct`, `active_days`, `distinct_features_used`, `most_used_feature` |
| Support | `total_tickets`, `resolved_tickets`, `avg_resolve_hours`, `avg_csat_score` |
| Derived | `engagement_score` = `sessions×0.3 + active_days×0.4 + distinct_features×0.3` |

**Rows:** 40,000

---

#### `fct_retention` — Core
Classic **cohort retention matrix**. One row per cohort month × months-since-signup pair.

| Column | Description |
|---|---|
| `cohort_month` | Month the cohort signed up |
| `cohort_size` | Total users in that cohort |
| `months_since_signup` | 0 through 24 |
| `active_users` | Users with ≥1 session in that period |
| `retention_pct` | `active_users / cohort_size × 100` |

**Rows:** 600

---

#### `fct_mrr` — Finance
Monthly MRR waterfall aggregated by plan and movement type. Powers the revenue dashboard.

| Column | Description |
|---|---|
| `month_date` | Calendar month |
| `plan` | `free` / `pro` / `enterprise` |
| `mrr_movement_type` | `new` / `expansion` / `retained` / `contraction` / `churn` / `new_free` |
| `users` | User count in this bucket |
| `total_mrr` | Total MRR for this group |
| `net_mrr_change` | Net MRR delta |
| `new_mrr`, `expansion_mrr`, `contraction_mrr`, `churned_mrr`, `retained_mrr` | Pre-pivoted movement columns |

**Rows:** 1,998

---

#### `fct_churn` — Finance
**One row per churned user** with full behavioural context captured at churn time.

| Column | Description |
|---|---|
| `user_id` | Unique identifier |
| `plan` | Plan at time of churn |
| `lost_mrr` | MRR lost from this user |
| `days_to_churn` | Days between signup and churn |
| `churn_stage` | `immediate` (≤30d) / `early` (31–90d) / `mid` (91–365d) / `late` (365d+) |
| `churn_month` | Month when churn occurred |
| `total_sessions` | Sessions logged before churn |
| `bounce_rate_pct` | Bounce rate before churn |
| `last_feature_used` | Final feature interaction before churn |
| `tickets_before_churn` | Support tickets raised before churn |

**Rows:** 11,751

---

#### `fct_sessions` — Product
Every session enriched with user context and two derived bucket dimensions for easy dashboard filtering.

**Extra derived columns vs staging:**
| Column | Logic |
|---|---|
| `depth_bucket` | `1 page (bounce)` / `2-3 pages` / `4-7 pages` / `8+ pages (deep)` |
| `duration_bucket` | `< 1 min` / `1-5 min` / `5-15 min` / `15-60 min` / `1hr+` |
| User context columns | `plan`, `country`, `is_churned`, `onboarding_completed`, `mrr` joined from `stg_users` |

**Rows:** 4,221,361

---

#### `fct_feature_usage` — Product
Daily feature usage aggregated by `feature_name × platform × plan × country`. Powers the feature analytics dashboard page.

| Column | Description |
|---|---|
| `event_date` | Calendar date |
| `event_month` | Calendar month |
| `feature_name` | Feature interacted with |
| `platform` | `web` / `mobile` / `desktop` |
| `plan` | User's plan |
| `country` | User's country |
| `total_events` | Total interactions |
| `unique_users` | Distinct users |
| `unique_sessions` | Distinct sessions |
| `avg_duration_ms` | Average feature engagement time (ms) |
| `total_duration_seconds` | Total time spent on this feature |

**Rows:** 1,075,600

---

## Test Coverage

39 tests across all layers — all passing.

| Test Type | Count | Models Covered |
|---|---|---|
| `unique` | 12 | All primary keys |
| `not_null` | 18 | PKs, FK columns, key measures |
| `accepted_values` | 9 | `plan`, `status`, `churn_stage`, `mrr_movement_type`, `change_type` |

```bash
dbt test
# Finished running 39 tests.
# Completed successfully. PASS=39 WARN=0 ERROR=0 SKIP=0 TOTAL=39
```

---

## Row Counts

| Model | Layer | Rows |
|---|---|---|
| `dim_users` | mart | 40,000 |
| `fct_retention` | mart | 600 |
| `fct_mrr` | mart | 1,998 |
| `fct_churn` | mart | 11,751 |
| `fct_sessions` | mart | 4,221,361 |
| `fct_feature_usage` | mart | 1,075,600 |
| **Total mart rows** | | **5,351,310** |

---

## Setup & Installation

### Prerequisites
- Python 3.8+
- A Snowflake account with the `saas_analytics` database and `raw` schema loaded
- `dbt-snowflake` 1.11+

### 1. Install dbt

```bash
pip install dbt-snowflake
```

### 2. Configure credentials

Create `~/.dbt/profiles.yml` — **never commit this file**:

```yaml
saas_analytics:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: <your_account_identifier>
      user: <your_username>
      password: <your_password>
      role: ACCOUNTADMIN
      database: saas_analytics
      warehouse: COMPUTE_WH
      schema: MARTS
      threads: 4
      client_session_keep_alive: False
```

### 3. Clone and verify

```bash
git clone https://github.com/<your-username>/saas-dbt-snowflake.git
cd saas-dbt-snowflake

dbt debug
# All checks passed!
```

---

## Running the Project

```bash
# Run all 16 models
dbt run

# Run tests
dbt test

# Run a specific layer
dbt run --select staging
dbt run --select intermediate
dbt run --select marts

# Run a model and all upstream dependencies
dbt run --select +dim_users
dbt run --select +fct_churn

# Build (run + test together)
dbt build

# Generate and serve documentation
dbt docs generate
dbt docs serve
```

**Expected output for `dbt run`:**
```
Completed successfully
Done. PASS=16 WARN=0 ERROR=0 SKIP=0 TOTAL=16
```

---

## Project Structure

```
saas_dbt/
├── dbt_project.yml                  # Project config — materialisation strategies
├── README.md
├── .gitignore                       # Excludes profiles.yml, target/, logs/
│
└── models/
    ├── staging/
    │   ├── sources.yml              # Raw source definitions + source tests
    │   ├── stg_users.sql
    │   ├── stg_sessions.sql
    │   ├── stg_tracks.sql
    │   ├── stg_pages.sql
    │   ├── stg_payments.sql
    │   ├── stg_subscriptions.sql
    │   ├── stg_plan_changes.sql
    │   └── stg_support_tickets.sql
    │
    ├── intermediate/
    │   ├── int_user_activity.sql
    │   └── int_monthly_revenue.sql
    │
    └── marts/
        ├── schema.yml               # Mart model descriptions + tests
        ├── core/
        │   ├── dim_users.sql
        │   └── fct_retention.sql
        ├── finance/
        │   ├── fct_mrr.sql
        │   └── fct_churn.sql
        └── product/
            ├── fct_sessions.sql
            └── fct_feature_usage.sql
```

---

## Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| dbt-core | 1.11.7 | Transformation framework |
| dbt-snowflake | 1.11.3 | Snowflake adapter |
| Snowflake | — | Cloud data warehouse |
| Python | 3.11 | Data generation (`generate_saas_data.py`) |
| Streamlit | 1.35+ | Analytics dashboard |
| Plotly | 5.18+ | Interactive charts |
