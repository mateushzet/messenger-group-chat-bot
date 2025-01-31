CREATE VIEW game_series_global AS
WITH game_series AS (
  SELECT
    id,
    user_name,
    created_at,
    result_amount,
    CASE
      WHEN result_amount > 0 THEN 1
      WHEN result_amount < 0 THEN -1
    END AS result_type,
    CASE
      WHEN result_amount > 0 AND LAG(result_amount) OVER (PARTITION BY user_name ORDER BY created_at) <= 0 THEN 1
      WHEN result_amount < 0 AND LAG(result_amount) OVER (PARTITION BY user_name ORDER BY created_at) >= 0 THEN 1
      ELSE 0
    END AS is_new_series
  FROM game_history
),
series_with_group AS (
  SELECT
    *,
    SUM(is_new_series) OVER (PARTITION BY user_name ORDER BY created_at) AS series_group
  FROM game_series
  WHERE result_amount != 0
),
series_count AS (
  SELECT
    result_type,
    series_group,
	user_name,
    COUNT(*) AS streak_length
  FROM series_with_group
  GROUP BY result_type, series_group, user_name
)
SELECT
  result_type,
  user_name,
  MAX(streak_length) AS max_streak

FROM series_count
GROUP BY result_type, user_name