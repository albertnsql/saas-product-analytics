-- Enriched session fact table — joins user context onto every session

WITH sessions AS (
    SELECT * FROM {{ ref('stg_sessions') }}
),

users AS (
    SELECT
        user_id,
        plan,
        country,
        is_churned,
        onboarding_completed,
        signup_month,
        mrr
    FROM {{ ref('stg_users') }}
)

SELECT
    s.session_id,
    s.user_id,
    s.started_at,
    s.ended_at,
    s.session_date,
    s.session_week,
    s.session_month,
    s.duration_seconds,
    s.duration_minutes,
    s.platform,
    s.page_count,
    s.feature_count,
    s.entry_page,
    s.exit_page,
    s.is_bounce,
    s.days_since_signup,
    s.day_of_week,
    s.hour_of_day,

    -- User context
    u.plan,
    u.country,
    u.is_churned,
    u.onboarding_completed,
    u.signup_month,
    u.mrr,

    -- Session depth bucket
    CASE
        WHEN s.page_count = 1    THEN '1 page (bounce)'
        WHEN s.page_count <= 3   THEN '2-3 pages'
        WHEN s.page_count <= 7   THEN '4-7 pages'
        ELSE '8+ pages (deep)'
    END                         AS depth_bucket,

    -- Session length bucket
    CASE
        WHEN s.duration_seconds < 60    THEN '< 1 min'
        WHEN s.duration_seconds < 300   THEN '1-5 min'
        WHEN s.duration_seconds < 900   THEN '5-15 min'
        WHEN s.duration_seconds < 3600  THEN '15-60 min'
        ELSE '1hr+'
    END                         AS duration_bucket

FROM sessions s
LEFT JOIN users u ON s.user_id = u.user_id