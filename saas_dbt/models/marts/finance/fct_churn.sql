-- One row per churned user with full context

WITH churned_users AS (
    SELECT *
    FROM {{ ref('stg_users') }}
    WHERE is_churned = TRUE
),

activity AS (
    SELECT * FROM {{ ref('int_user_activity') }}
),

last_feature AS (
    SELECT
        user_id,
        feature_name AS last_feature_used,
        received_at  AS last_feature_at
    FROM (
        SELECT
            user_id,
            feature_name,
            received_at,
            ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY received_at DESC) AS rn
        FROM {{ ref('stg_tracks') }}
    )
    WHERE rn = 1
),

tickets AS (
    SELECT
        user_id,
        COUNT(*) AS tickets_before_churn
    FROM {{ ref('stg_support_tickets') }}
    GROUP BY user_id
)

SELECT
    u.user_id,
    u.plan,
    u.country,
    u.referral_source,
    u.mrr                                               AS lost_mrr,
    u.signed_up_at,
    u.churned_at,
    u.days_to_churn,
    u.onboarding_completed,
    u.nps_score,
    u.nps_category,
    DATE_TRUNC('month', u.signed_up_at)                 AS cohort_month,
    DATE_TRUNC('month', u.churned_at)                   AS churn_month,

    -- Was it early churn or late churn?
    CASE
        WHEN u.days_to_churn <= 30  THEN 'immediate'
        WHEN u.days_to_churn <= 90  THEN 'early'
        WHEN u.days_to_churn <= 365 THEN 'mid'
        ELSE 'late'
    END                                                 AS churn_stage,

    -- Activity before churn
    a.total_sessions,
    a.active_days,
    a.bounce_rate_pct,
    a.distinct_features_used,
    a.total_session_hours,

    -- Last touchpoints
    lf.last_feature_used,
    lf.last_feature_at,

    -- Support signal
    t.tickets_before_churn

FROM churned_users u
LEFT JOIN activity    a  ON u.user_id = a.user_id
LEFT JOIN last_feature lf ON u.user_id = lf.user_id
LEFT JOIN tickets      t  ON u.user_id = t.user_id