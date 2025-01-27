CREATE VIEW Games_statistics_view AS
	SELECT
		main.game_type AS Game_type,
		SUM(main.bet_amount) AS Total_chips_bet,
		SUM(main.result_amount) AS Total_score,
		COALESCE(winnings.Total_winnings, 0) AS Total_winnings,
		COALESCE(losses.Total_chips_lost, 0) AS Total_chips_lost,
		COUNT(main.id) AS Total_games_played,
		AVG(main.bet_amount) AS Average_bet_amount,
		MAX(main.result_amount) AS Maximum_win,
		MIN(main.result_amount) AS Biggest_loss,
		COALESCE(win_streak.max_streak, 0) AS Win_streak,
		COALESCE(lose_streak.max_streak, 0) AS Lose_streak
		
		
	FROM 
		game_history AS main
		LEFT JOIN (
		SELECT game_type, SUM(result_amount) AS Total_winnings
		FROM game_history
		WHERE result_amount > 0 
		GROUP BY game_type
	) winnings ON main.game_type = winnings.game_type
	-- Straty
	LEFT JOIN (
		SELECT game_type, SUM(result_amount) AS Total_chips_lost
		FROM game_history
		WHERE result_amount < 0 
		GROUP BY game_type
	) losses ON main.game_type = losses.game_type
	-- Serie zwycięstw
	LEFT JOIN game_series_games AS win_streak ON win_streak.result_type = 1 AND win_streak.game_type = main.game_type 
	LEFT JOIN game_series_games AS lose_streak ON lose_streak.result_type = -1 AND lose_streak.game_type = main.game_type 
	GROUP BY 
		main.game_type