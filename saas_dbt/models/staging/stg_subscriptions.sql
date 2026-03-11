WITH source AS (
    SELECT * FROM {{ source('raw', 'subscriptions') }}
),

renamed AS (
    SELECT
        subscription_id,
        user_id,
        plan,
        CAST(start_date AS TIMESTAMP_NTZ)       AS started_at,
        CAST(end_date AS TIMESTAMP_NTZ)         AS ended_at,
        DATE_TRUNC('month', start_date)         AS start_month,
        CAST(mrr AS FLOAT)                      AS mrr,
        status,
        CASE WHEN status = 'active'    THEN TRUE ELSE FALSE END AS is_active,
        CASE WHEN status = 'cancelled' THEN TRUE ELSE FALSE END AS is_churned,
        DATEDIFF('day', start_date, COALESCE(end_date, CURRENT_DATE)) AS subscription_length_days
    FROM source
)

SELECT * FROM renamed