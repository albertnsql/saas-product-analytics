WITH source AS (
    SELECT * FROM {{ source('raw', 'payments') }}
),

renamed AS (
    SELECT
        payment_id,
        user_id,
        CAST(amount AS FLOAT)                   AS amount,
        CAST(payment_date AS TIMESTAMP_NTZ)     AS paid_at,
        DATE_TRUNC('month', payment_date)       AS payment_month,
        status,
        plan,

        -- Flags
        CASE WHEN status = 'succeeded' THEN 1 ELSE 0 END   AS is_successful,
        CASE WHEN status = 'failed'    THEN 1 ELSE 0 END   AS is_failed,
        CASE WHEN status = 'refunded'  THEN 1 ELSE 0 END   AS is_refunded,
        CASE WHEN amount < 0           THEN ABS(amount) ELSE 0 END AS refund_amount,
        CASE WHEN amount > 0 AND status = 'succeeded' THEN amount ELSE 0 END AS collected_amount

    FROM source
)

SELECT * FROM renamed