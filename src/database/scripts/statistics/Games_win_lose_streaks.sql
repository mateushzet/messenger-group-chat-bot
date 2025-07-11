CREATE VIEW game_series_games AS
WITH game_series AS (
  SELECT
    id,
    created_at,
    result_amount,
	game_type,
    CASE
      WHEN result_amount > 0 THEN 1
      WHEN result_amount < 0 THEN -1
    END AS result_type,
    CASE
      WHEN result_amount > 0 AND LAG(result_amount) OVER (PARTITION BY game_type ORDER BY created_at) <= 0 THEN 1
      WHEN result_amount < 0 AND LAG(result_amount) OVER (PARTITION BY game_type ORDER BY created_at) >= 0 THEN 1
      ELSE 0
    END AS is_new_series
  FROM game_history
),
series_with_group AS (
  SELECT
    *,
    SUM(is_new_series) OVER (PARTITION BY game_type ORDER BY created_at) AS series_group
  FROM game_series
  WHERE result_amount != 0
),
series_count AS (
  SELECT
    result_type,
    series_group,
    COUNT(*) AS streak_length,
	game_type
  FROM series_with_group
  GROUP BY result_type, series_group, game_type
)
SELECT
  result_type,
  MAX(streak_length) AS max_streak,
  game_type
FROM series_count
GROUP BY result_type, game_type