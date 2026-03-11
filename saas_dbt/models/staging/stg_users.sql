WITH source AS (
    SELECT * FROM {{ source('raw', 'users') }}
),

renamed AS (
    SELECT
        user_id,
        CAST(signup_date AS TIMESTAMP_NTZ)          AS signed_up_at,
        DATE_TRUNC('month', signup_date)            AS signup_month,
        plan,
        country,
        email,
        company,
        CAST(activity_mult AS FLOAT)                AS activity_mult,
        CAST(churned AS BOOLEAN)                    AS is_churned,
        CAST(churn_date AS TIMESTAMP_NTZ)           AS churned_at,
        CAST(last_active AS TIMESTAMP_NTZ)          AS last_active_at,
        CAST(onboarding_completed AS BOOLEAN)       AS onboarding_completed,
        referral_source,
        CAST(nps_score AS INT)                      AS nps_score,

        -- Derived fields
        DATEDIFF('day', signup_date, COALESCE(churn_date, CURRENT_DATE))  AS days_to_churn,
        DATEDIFF('day', signup_date, last_active)                          AS days_active,
        CASE
            WHEN plan = 'free'       THEN 0
            WHEN plan = 'pro'        THEN 49
            WHEN plan = 'enterprise' THEN 299
        END                                                                AS mrr,
        CASE
            WHEN nps_score BETWEEN 0  AND 6  THEN 'detractor'
            WHEN nps_score BETWEEN 7  AND 8  THEN 'passive'
            WHEN nps_score BETWEEN 9  AND 10 THEN 'promoter'
        END                                                                AS nps_category

    FROM source
)

SELECT * FROM renamed