WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_pages') }}
),

renamed AS (
    SELECT
        message_id,
        user_id,
        session_id,
        page_url,
        CAST(received_at AS TIMESTAMP_NTZ)      AS received_at,
        DATE_TRUNC('day',  received_at)         AS event_date,
        DATE_TRUNC('month', received_at)        AS event_month,
        platform
    FROM source
)

SELECT * FROM renamed