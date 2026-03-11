-- marts/core/dim_users.sql
-- One row per user — the master user dimension

WITH users AS (
    SELECT * FROM {{ ref('stg_users') }}
),

activity AS (
    SELECT * FROM {{ ref('int_user_activity') }}
),

tickets AS (
    SELECT
        user_id,
        COUNT(*)                                            AS total_tickets,
        SUM(CASE WHEN is_resolved THEN 1 ELSE 0 END)       AS resolved_tickets,
        AVG(time_to_resolve_hours)                         AS avg_resolve_hours,
        AVG(csat_score)                                    AS avg_csat_score
    FROM {{ ref('stg_support_tickets') }}
    GROUP BY user_id
)

SELECT
    -- Identity
    u.user_id,
    u.email,
    u.company,
    u.country,
    u.referral_source,

    -- Plan
    u.plan,
    u.mrr,

    -- Dates
    u.signed_up_at,
    u.signup_month,
    u.last_active_at,
    u.churned_at,

    -- Cohort (used for retention analysis)
    DATE_TRUNC('month', u.signed_up_at)     AS cohort_month,
    DATEDIFF('month', u.signed_up_at, CURRENT_DATE) AS months_since_signup,

    -- Status
    u.is_churned,
    u.onboarding_completed,
    u.days_to_churn,
    u.days_active,

    -- NPS
    u.nps_score,
    u.nps_category,

    -- Activity (from int_user_activity)
    a.total_sessions,
    a.total_session_hours,
    a.avg_session_duration_seconds,
    a.bounce_rate_pct,
    a.active_days,
    a.active_months,
    a.distinct_features_used,
    a.most_used_feature,
    a.total_page_views,
    a.most_visited_page,
    a.first_session_at,
    a.last_session_at,

    -- Support
    t.total_tickets,
    t.resolved_tickets,
    t.avg_resolve_hours,
    t.avg_csat_score,

    -- Engagement score (simple composite — customize as needed)
    ROUND(
        COALESCE(a.total_sessions, 0) * 0.3
        + COALESCE(a.active_days, 0) * 0.4
        + COALESCE(a.distinct_features_used, 0) * 0.3
    , 2)                                    AS engagement_score

FROM users u
LEFT JOIN activity a ON u.user_id = a.user_id
LEFT JOIN tickets  t ON u.user_id = t.user_id