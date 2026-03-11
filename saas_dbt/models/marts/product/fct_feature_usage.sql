-- Daily feature usage aggregated by plan and feature
-- Great for product analytics dashboards

WITH tracks AS (
    SELECT * FROM {{ ref('stg_tracks') }}
),

users AS (
    SELECT user_id, plan, country, is_churned, signup_month
    FROM {{ ref('stg_users') }}
)

SELECT
    t.event_date,
    t.event_month,
    t.feature_name,
    t.platform,
    u.plan,
    u.country,
    u.is_churned,

    COUNT(*)                        AS total_events,
    COUNT(DISTINCT t.user_id)       AS unique_users,
    COUNT(DISTINCT t.session_id)    AS unique_sessions,
    AVG(t.duration_ms)              AS avg_duration_ms,
    SUM(t.duration_seconds)         AS total_duration_seconds

FROM tracks t
LEFT JOIN users u ON t.user_id = u.user_id
GROUP BY
    t.event_date,
    t.event_month,
    t.feature_name,
    t.platform,
    u.plan,
    u.country,
    u.is_churned