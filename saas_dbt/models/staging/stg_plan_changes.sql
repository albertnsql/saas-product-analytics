WITH source AS (
    SELECT * FROM {{ source('raw', 'plan_changes') }}
),

renamed AS (
    SELECT
        change_id,
        user_id,
        from_plan,
        to_plan,
        change_type,
        CAST(changed_at AS TIMESTAMP_NTZ)       AS changed_at,
        DATE_TRUNC('month', changed_at)         AS change_month,

        -- MRR impact of the change
        CASE
            WHEN from_plan = 'free'       THEN 0
            WHEN from_plan = 'pro'        THEN 49
            WHEN from_plan = 'enterprise' THEN 299
        END AS from_mrr,
        CASE
            WHEN to_plan = 'free'         THEN 0
            WHEN to_plan = 'pro'          THEN 49
            WHEN to_plan = 'enterprise'   THEN 299
        END AS to_mrr

    FROM source
)

SELECT
    *,
    to_mrr - from_mrr AS mrr_delta
FROM renamed