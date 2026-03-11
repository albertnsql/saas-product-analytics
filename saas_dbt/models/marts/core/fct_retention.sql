-- Classic cohort retention matrix
-- Rows = cohort month, Columns = months since signup (0-24)
-- % of users still active in each period

WITH user_sessions AS (
    SELECT
        s.user_id,
        u.signup_month                                              AS cohort_month,
        DATEDIFF('month', u.signed_up_at, s.started_at)           AS months_since_signup
    FROM {{ ref('stg_sessions') }} s
    JOIN {{ ref('stg_users') }}    u ON s.user_id = u.user_id
),

cohort_sizes AS (
    SELECT
        signup_month    AS cohort_month,
        COUNT(*)        AS cohort_size
    FROM {{ ref('stg_users') }}
    GROUP BY signup_month
),

active_by_month AS (
    SELECT
        cohort_month,
        months_since_signup,
        COUNT(DISTINCT user_id)     AS active_users
    FROM user_sessions
    WHERE months_since_signup BETWEEN 0 AND 24
    GROUP BY cohort_month, months_since_signup
)

SELECT
    a.cohort_month,
    c.cohort_size,
    a.months_since_signup,
    a.active_users,
    ROUND(a.active_users * 100.0 / NULLIF(c.cohort_size, 0), 2) AS retention_pct
FROM active_by_month a
JOIN cohort_sizes     c ON a.cohort_month = c.cohort_month
ORDER BY a.cohort_month, a.months_since_signup