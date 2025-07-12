CREATE VIEW Favourite_games AS
	SELECT user_name, game_type, row_number AS rn FROM (
		SELECT 
			user_name, 
			game_type, 
			COUNT(id) AS game_played,
			ROW_NUMBER() OVER (PARTITION BY user_name ORDER BY COUNT(id) DESC) AS row_number
		FROM 
			game_history
		GROUP BY 
			user_name, game_type
		ORDER BY 
			user_name, row_number
			) AS favourite_game 
	WHERE favourite_game.row_number IN (1,2,3)