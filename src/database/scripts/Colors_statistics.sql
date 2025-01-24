CREATE VIEW Colors_statistic_view AS 
SELECT
    main.user_name,
    SUM(main.bet_amount) AS Total_chips_bet_on_colors,
    SUM(main.result_amount) AS Total_roulette_score,
    COALESCE(winnings.Total_winnings_from_colors, 0) AS Total_winnings_from_colors,
    COALESCE(losses.Total_chips_lost_on_colors, 0) AS Total_chips_lost_on_colors,
    COUNT(main.id) AS Total_games_played_on_colors,
    AVG(main.bet_amount) AS Average_bet_amount_on_colors,
    MAX(main.result_amount) AS Maximum_win_on_colors,
    MIN(main.result_amount) AS Biggest_loss_on_colors,
    win_streak.max_streak AS Win_streak,
    lose_streak.max_streak AS Lose_streak,
	COALESCE(red.Hits_by_red, 0) AS Hits_by_red,
	COALESCE(black.Hits_by_black, 0) AS Hits_by_black,
	COALESCE(blue.Hits_by_blue, 0) AS Hits_by_blue,
	COALESCE(gold.Hits_by_gold, 0) AS Hits_by_gold
	
	
    
FROM 
    game_history AS main
-- Wygrane
LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_winnings_from_colors
    FROM game_history
    WHERE result_amount > 0 AND game_type = 'Colors'
    GROUP BY user_name
) winnings ON main.user_name = winnings.user_name
-- Straty
LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_chips_lost_on_colors
    FROM game_history
    WHERE result_amount < 0 AND game_type = 'Colors'
    GROUP BY user_name
) losses ON main.user_name = losses.user_name
LEFT JOIN game_series AS win_streak ON win_streak.result_type = 1 AND win_streak.user_name = main.user_name AND win_streak.game_type ='Colors'
LEFT JOIN game_series AS lose_streak ON lose_streak.result_type = -1 AND lose_streak.user_name = main.user_name AND lose_streak.game_type ='Colors'
LEFT JOIN (
	SELECT user_name, COUNT(*) AS Hits_by_red 
	FROM game_history 
	WHERE game_type = 'Colors' 
	AND result_amount > 0 
	AND note LIKE '%1%' 
	GROUP BY user_name
	) red ON red.user_name = main.user_name
LEFT JOIN (
	SELECT user_name, COUNT(*) AS Hits_by_black 
	FROM game_history 
	WHERE game_type = 'Colors' 
	AND result_amount > 0 
	AND note LIKE '%0%' 
	GROUP BY user_name
	) black ON black.user_name = main.user_name
LEFT JOIN (
	SELECT user_name, COUNT(*) AS Hits_by_blue 
	FROM game_history 
	WHERE game_type = 'Colors' 
	AND result_amount > 0 
	AND note LIKE '%2%' 
	GROUP BY user_name
	) blue ON blue.user_name = main.user_name
LEFT JOIN (
	SELECT user_name, COUNT(*) AS Hits_by_gold 
	FROM game_history 
	WHERE game_type = 'Colors' 
	AND result_amount > 0 
	AND note LIKE '%3%' 
	GROUP BY user_name
	) gold ON gold.user_name = main.user_name

WHERE main.game_type = 'Colors'
GROUP BY 
    main.user_name