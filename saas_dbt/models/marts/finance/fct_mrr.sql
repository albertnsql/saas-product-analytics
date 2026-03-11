-- Monthly MRR movements — new, expansion, contraction, churn, retained
-- One row per user per month

WITH mrr AS (
    SELECT * FROM {{ ref('int_monthly_revenue') }}
),

aggregated AS (
    SELECT
        month_date,
        cohort_month,
        plan,
        mrr_movement_type,

        COUNT(DISTINCT user_id)                     AS users,
        SUM(mrr)                                    AS total_mrr,
        SUM(mrr_change)                             AS net_mrr_change,

        SUM(CASE WHEN mrr_movement_type = 'new'         THEN mrr ELSE 0 END) AS new_mrr,
        SUM(CASE WHEN mrr_movement_type = 'expansion'   THEN mrr_change ELSE 0 END) AS expansion_mrr,
        SUM(CASE WHEN mrr_movement_type = 'contraction' THEN mrr_change ELSE 0 END) AS contraction_mrr,
        SUM(CASE WHEN mrr_movement_type = 'churn'       THEN mrr_change ELSE 0 END) AS churned_mrr,
        SUM(CASE WHEN mrr_movement_type = 'retained'    THEN mrr ELSE 0 END) AS retained_mrr

    FROM mrr
    GROUP BY month_date, cohort_month, plan, mrr_movement_type
)

SELECT * FROM aggregated
ORDER BY month_date, plan