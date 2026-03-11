WITH source AS (
    SELECT * FROM {{ source('raw', 'support_tickets') }}
),

renamed AS (
    SELECT
        ticket_id,
        user_id,
        plan,
        category,
        priority,
        CAST(created_at AS TIMESTAMP_NTZ)       AS created_at,
        CAST(resolved_at AS TIMESTAMP_NTZ)      AS resolved_at,
        DATE_TRUNC('month', created_at)         AS ticket_month,
        CAST(csat_score AS INT)                 AS csat_score,

        -- Derived
        CASE WHEN resolved_at IS NOT NULL THEN TRUE ELSE FALSE END  AS is_resolved,
        DATEDIFF('hour', created_at, resolved_at)                   AS time_to_resolve_hours,
        CASE
            WHEN csat_score >= 4 THEN 'satisfied'
            WHEN csat_score = 3  THEN 'neutral'
            WHEN csat_score <= 2 THEN 'dissatisfied'
        END                                                         AS csat_category

    FROM source
)

SELECT * FROM renamed