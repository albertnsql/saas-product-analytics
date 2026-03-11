WITH source AS (
    SELECT * FROM {{ source('raw', 'sessions') }}
),

renamed AS (
    SELECT
        session_id,
        user_id,
        plan,
        country,
        CAST(started_at AS TIMESTAMP_NTZ)       AS started_at,
        CAST(ended_at AS TIMESTAMP_NTZ)         AS ended_at,
        CAST(duration_seconds AS INT)           AS duration_seconds,
        ROUND(duration_seconds / 60.0, 2)       AS duration_minutes,
        platform,
        CAST(page_count AS INT)                 AS page_count,
        CAST(feature_count AS INT)              AS feature_count,
        entry_page,
        exit_page,
        CAST(is_bounce AS BOOLEAN)              AS is_bounce,
        CAST(days_since_signup AS INT)          AS days_since_signup,
        DATE_TRUNC('day',  started_at)          AS session_date,
        DATE_TRUNC('week', started_at)          AS session_week,
        DATE_TRUNC('month', started_at)         AS session_month,
        DAYOFWEEK(started_at)                   AS day_of_week,
        HOUR(started_at)                        AS hour_of_day
    FROM source
)

SELECT * FROM renamed