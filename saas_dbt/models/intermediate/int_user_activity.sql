-- Aggregates session, track and page activity per user
-- Used by dim_users and engagement marts

WITH session_stats AS (
    SELECT
        user_id,
        COUNT(*)                                AS total_sessions,
        SUM(duration_seconds)                   AS total_session_seconds,
        AVG(duration_seconds)                   AS avg_session_duration_seconds,
        SUM(page_count)                         AS total_pages_viewed,
        SUM(feature_count)                      AS total_features_used,
        SUM(CASE WHEN is_bounce THEN 1 ELSE 0 END) AS bounce_sessions,
        ROUND(
            SUM(CASE WHEN is_bounce THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0)
        , 2)                                    AS bounce_rate_pct,
        MIN(started_at)                         AS first_session_at,
        MAX(started_at)                         AS last_session_at,
        COUNT(DISTINCT session_date)            AS active_days,
        COUNT(DISTINCT session_month)           AS active_months
    FROM {{ ref('stg_sessions') }}
    GROUP BY user_id
),

feature_stats AS (
    SELECT
        user_id,
        COUNT(*)                                AS total_track_events,
        COUNT(DISTINCT feature_name)            AS distinct_features_used,
        MODE(feature_name)                      AS most_used_feature,
        AVG(duration_ms)                        AS avg_feature_duration_ms
    FROM {{ ref('stg_tracks') }}
    GROUP BY user_id
),

page_stats AS (
    SELECT
        user_id,
        COUNT(*)                                AS total_page_views,
        COUNT(DISTINCT page_url)                AS distinct_pages_visited,
        MODE(page_url)                          AS most_visited_page
    FROM {{ ref('stg_pages') }}
    GROUP BY user_id
)

SELECT
    s.user_id,
    s.total_sessions,
    s.total_session_seconds,
    ROUND(s.total_session_seconds / 3600.0, 2)  AS total_session_hours,
    s.avg_session_duration_seconds,
    s.total_pages_viewed,
    s.total_features_used,
    s.bounce_sessions,
    s.bounce_rate_pct,
    s.first_session_at,
    s.last_session_at,
    s.active_days,
    s.active_months,
    f.total_track_events,
    f.distinct_features_used,
    f.most_used_feature,
    f.avg_feature_duration_ms,
    p.total_page_views,
    p.distinct_pages_visited,
    p.most_visited_page
FROM session_stats s
LEFT JOIN feature_stats f ON s.user_id = f.user_id
LEFT JOIN page_stats    p ON s.user_id = p.user_id