# SaaS Product Analysis

A full end-to-end B2B SaaS analytics project — from synthetic data generation through Snowflake loading and dbt transformations — built on a modern data stack.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?logo=snowflake&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-1.11-orange?logo=dbt&logoColor=white)
![Rows](https://img.shields.io/badge/data-45.6M%20rows-lightgrey)

-----

## What This Project Does

This project simulates a real-world SaaS analytics pipeline for a B2B product with three subscription tiers (Free, Pro, Enterprise). It covers the full journey from raw data to business insights:

1. **Synthetic data generation** — 45.6M rows of realistic user, session, event, and payment data across 3 years (2023–2025), using S-curve signup growth, lognormal session durations, and plan-weighted behaviour
1. **Snowflake loading** — Raw data staged and loaded into 9 source tables
1. **dbt transformations** — 16 models, 3 layers, 39 passing tests turning raw events into analytics-ready marts

-----

## Project Structure

```
sas_product_analysis/
│
├── generate_saas_data.py       # Synthetic data generator
├── snowflake_load.sql          # Snowflake stage + COPY INTO
├── README.md                   # This file
│
├── saas_dbt/                   # dbt transformation project
│   └── README.md               # Full dbt documentation → start here
│
└── data/                       # Generated CSVs — gitignored, regenerate locally
```

-----

## Data at a Glance

|Table            |Rows          |Description               |
|-----------------|--------------|--------------------------|
|`raw_pages`      |22,088,021    |Page view events          |
|`raw_tracks`     |18,899,450    |Feature interaction events|
|`sessions`       |4,221,361     |User sessions             |
|`payments`       |271,549       |Payment transactions      |
|`users`          |40,000        |User profiles             |
|`raw_identifies` |40,000        |Signup identity events    |
|`subscriptions`  |40,000        |Subscription records      |
|`support_tickets`|24,224        |Support history           |
|`plan_changes`   |2,767         |Upgrades / downgrades     |
|**Total**        |**45,647,412**|                          |

**Snapshot:** ~$1.26M active MRR · 38.6% free churn · 14.1% pro churn · 5.4% enterprise churn

-----

## Tech Stack

|Layer          |Tool                              |
|---------------|----------------------------------|
|Data generation|Python 3.11 · pandas · numpy      |
|Data warehouse |Snowflake                         |
|Transformations|dbt-core 1.11 · dbt-snowflake 1.11|

-----

*For full model documentation, architecture diagrams, and SQL logic — see [`saas_dbt/README.md`](saas_dbt/README.md)*
