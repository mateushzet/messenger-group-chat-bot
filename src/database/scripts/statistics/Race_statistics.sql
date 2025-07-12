CREATE VIEW Race_statistic_view AS 
WITH RankedHorses AS (
    SELECT 
        user_name,
        TRIM(SUBSTR(bet_command, -2, 1)) AS Favorite_horse,
        COUNT(bet_command) AS How_many_races,
        ROW_NUMBER() OVER (PARTITION BY user_name ORDER BY COUNT(bet_command) DESC) AS rank
    FROM game_history
    WHERE game_type = 'Race'
    GROUP BY user_name, TRIM(SUBSTR(bet_command, -2, 1))
)
SELECT
    main.user_name,
    SUM(main.bet_amount) AS Total_chips_bet_on_race,
    SUM(main.result_amount) AS Total_race_score,
    COALESCE(winnings.Total_winnings_from_race, 0) AS Total_winnings_from_race,
    COALESCE(losses.Total_chips_lost_on_race, 0) AS Total_chips_lost_on_race,
    COUNT(main.id) AS Total_games_played_on_race,
    AVG(main.bet_amount) AS Average_bet_amount_on_race,
    MAX(main.result_amount) AS Maximum_win_on_race,
    MIN(main.result_amount) AS Biggest_loss_on_race,
    COALESCE(win_streak.max_streak, 0) AS Win_streak,
    COALESCE(lose_streak.max_streak, 0) AS Lose_streak,
    COALESCE(favorite_horses.Favorite_horse, 'N/A') AS Favorite_horse,
    COALESCE(favorite_horses.How_many_races, 0) AS Favorite_horse_races
FROM 
    game_history AS main

LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_winnings_from_race
    FROM game_history
    WHERE result_amount > 0 AND game_type = 'Race'
    GROUP BY user_name
) winnings ON main.user_name = winnings.user_name

LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_chips_lost_on_race
    FROM game_history
    WHERE result_amount < 0 AND game_type = 'Race'
    GROUP BY user_name
) losses ON main.user_name = losses.user_name
LEFT JOIN game_series AS win_streak ON win_streak.result_type = 1 AND win_streak.user_name = main.user_name AND win_streak.game_type = 'Race'
LEFT JOIN game_series AS lose_streak ON lose_streak.result_type = -1 AND lose_streak.user_name = main.user_name AND lose_streak.game_type = 'Race'

LEFT JOIN (
    SELECT user_name, Favorite_horse, How_many_races
    FROM RankedHorses
    WHERE rank = 1
) favorite_horses ON main.user_name = favorite_horses.user_name
WHERE main.game_type = 'Race'
GROUP BY 
    main.user_name, favorite_horses.Favorite_horse, favorite_horses.How_many_races;