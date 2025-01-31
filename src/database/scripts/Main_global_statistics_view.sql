CREATE VIEW Main_global_statistics_view AS
	SELECT
		
		SUM(main.bet_amount) AS Total_chips_bet,
		SUM(main.result_amount) AS Total_score,
		COALESCE(winnings.Total_winnings, 0) AS Total_winnings,
		COALESCE(losses.Total_chips_lost, 0) AS Total_chips_lost,
		COUNT(main.id) AS Total_games_played,
		AVG(main.bet_amount) AS Average_bet_amount,
		MAX(main.result_amount) AS Maximum_win,
		MIN(main.result_amount) AS Biggest_loss,
		COALESCE(Favourite_game_1st.game_type, '') AS Favourite_game_1st,
		COALESCE(Favourite_game_2nd.game_type, '') AS Favourite_game_2nd,
		COALESCE(Favourite_game_3th.game_type, '') AS Favourite_game_3th
		
		
	FROM 
		game_history AS main
		LEFT JOIN (
		SELECT SUM(result_amount) AS Total_winnings
		FROM game_history
		WHERE result_amount > 0 
	) winnings ON 1=1

	LEFT JOIN (
		SELECT SUM(result_amount) AS Total_chips_lost
		FROM game_history
		WHERE result_amount < 0 
	) losses ON 1=1
	LEFT JOIN Favourite_games AS Favourite_game_1st ON Favourite_game_1st.user_name = main.user_name AND Favourite_game_1st.rn = 1
	LEFT JOIN Favourite_games AS Favourite_game_2nd ON Favourite_game_2nd.user_name = main.user_name AND Favourite_game_2nd.rn = 2
	LEFT JOIN Favourite_games AS Favourite_game_3th ON Favourite_game_3th.user_name = main.user_name AND Favourite_game_3th.rn = 3

