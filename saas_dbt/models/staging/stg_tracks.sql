WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_tracks') }}
),

renamed AS (
    SELECT
        message_id,
        user_id,
        session_id,
        event,
        feature_name,
        CAST(received_at AS TIMESTAMP_NTZ)      AS received_at,
        DATE_TRUNC('day',  received_at)         AS event_date,
        DATE_TRUNC('month', received_at)        AS event_month,
        platform,
        CAST(duration_ms AS INT)                AS duration_ms,
        ROUND(duration_ms / 1000.0, 2)          AS duration_seconds
    FROM source
)

SELECT * FROM renamed