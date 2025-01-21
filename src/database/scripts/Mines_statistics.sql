CREATE VIEW Mines_statistic_view AS
SELECT 
	
    main.user_name,
    SUM(main.bet_amount) AS Total_chips_bet_on_mines,
    SUM(main.result_amount) AS Total_mines_score,
    COALESCE(winnings.Total_winnings_from_mines, 0) AS Total_winnings_from_mines,
    COALESCE(losses.Total_chips_lost_on_mines, 0) AS Total_chips_lost_on_mines,
    COUNT(main.id) AS Total_games_played_on_mines,
    AVG(main.bet_amount) AS Average_bet_amount_on_mines,
    MAX(main.result_amount) AS Maximum_win_on_mines,
    MIN(main.result_amount) AS Biggest_loss_on_mines,
	win_streak.max_streak AS Win_streak,
	lose_streak.max_streak AS Lose_streak
	
FROM 
    game_history AS main
-- Wygrane
LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_winnings_from_mines
    FROM game_history
    WHERE result_amount > 0 AND game_type = 'Mines'
    GROUP BY user_name
) winnings ON main.user_name = winnings.user_name
-- Straty
LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_chips_lost_on_mines
    FROM game_history
    WHERE result_amount < 0 AND game_type = 'Mines'
    GROUP BY user_name
) losses ON main.user_name = losses.user_name
LEFT JOIN game_series AS win_streak ON win_streak.result_type = 1 AND win_streak.user_name = main.user_name AND win_streak.game_type ='Mines'
LEFT JOIN game_series AS lose_streak ON lose_streak.result_type = -1 AND lose_streak.user_name = main.user_name AND lose_streak.game_type ='Mines'
WHERE main.game_type = 'Mines'
GROUP BY 
    main.user_name;