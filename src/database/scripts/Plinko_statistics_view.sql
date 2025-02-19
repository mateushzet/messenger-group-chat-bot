CREATE VIEW Plinko_statistic_view AS 
SELECT 
    main.user_name,
    SUM(main.bet_amount) AS Total_chips_bet_on_plinko,
    SUM(main.result_amount) AS Total_plinko_score,
    COALESCE(winnings.Total_winnings_from_plinko, 0) AS Total_winnings_from_plinko,
    COALESCE(losses.Total_chips_lost_on_plinko, 0) AS Total_chips_lost_on_plinko,
    COUNT(main.id) AS Total_games_played_on_plinko,
    AVG(main.bet_amount) AS Average_bet_amount_on_plinko,
    MAX(main.result_amount) AS Maximum_win_on_plinko,
    MIN(main.result_amount) AS Biggest_loss_on_plinko,
    COALESCE(win_streak.max_streak, 0) AS Win_streak,
    COALESCE(lose_streak.max_streak, 0) AS Lose_streak 
FROM 
    game_history AS main
-- Wygrane
LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_winnings_from_plinko
    FROM game_history
    WHERE result_amount > 0 AND game_type = 'Plinko'
    GROUP BY user_name
) winnings ON main.user_name = winnings.user_name
-- Straty
LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_chips_lost_on_plinko
    FROM game_history
    WHERE result_amount < 0 AND game_type = 'Plinko'
    GROUP BY user_name
) losses ON main.user_name = losses.user_name
-- Serie zwycięstw
LEFT JOIN game_series AS win_streak ON win_streak.result_type = 1 AND win_streak.user_name = main.user_name AND win_streak.game_type = 'Plinko'
LEFT JOIN game_series AS lose_streak ON lose_streak.result_type = -1 AND lose_streak.user_name = main.user_name AND lose_streak.game_type = 'Plinko'

WHERE main.game_type = 'Plinko'
GROUP BY 
    main.user_name
    