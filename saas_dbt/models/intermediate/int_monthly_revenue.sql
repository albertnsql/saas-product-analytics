-- Builds month-by-month MRR movements per user
-- Foundation for the fct_mrr mart

WITH spine AS (
    -- Generate one row per user per month they were active
    SELECT
        u.user_id,
        u.plan,
        u.mrr,
        u.signed_up_at,
        u.churned_at,
        u.is_churned,
        DATE_TRUNC('month', u.signed_up_at)     AS cohort_month,
        m.month_date
    FROM {{ ref('stg_users') }} u
    JOIN (
        SELECT DATEADD('month', ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1, '2023-01-01'::DATE) AS month_date
        FROM TABLE(GENERATOR(ROWCOUNT => 36))   -- 36 months = 3 years
    ) m
        ON m.month_date >= DATE_TRUNC('month', u.signed_up_at)
        AND m.month_date <= DATE_TRUNC('month', COALESCE(u.churned_at, CURRENT_DATE))
),

with_prev AS (
    SELECT
        *,
        LAG(mrr) OVER (PARTITION BY user_id ORDER BY month_date) AS prev_mrr,
        LAG(plan) OVER (PARTITION BY user_id ORDER BY month_date) AS prev_plan
    FROM spine
),

classified AS (
    SELECT
        user_id,
        plan,
        month_date,
        cohort_month,
        mrr,
        prev_mrr,

        CASE
            WHEN prev_mrr IS NULL AND mrr > 0    THEN 'new'
            WHEN prev_mrr IS NULL AND mrr = 0    THEN 'new_free'
            WHEN mrr > prev_mrr                  THEN 'expansion'
            WHEN mrr < prev_mrr AND mrr > 0      THEN 'contraction'
            WHEN mrr = prev_mrr                  THEN 'retained'
            WHEN mrr = 0 AND prev_mrr > 0        THEN 'churn'
            ELSE 'retained'
        END AS mrr_movement_type,

        mrr - COALESCE(prev_mrr, 0) AS mrr_change

    FROM with_prev
)

SELECT * FROM classified