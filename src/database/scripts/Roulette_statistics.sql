CREATE VIEW Roulette_statistic_view AS
SELECT
    main.user_name,
    SUM(main.bet_amount) AS Total_chips_bet_on_roulette,
    SUM(main.result_amount) AS Total_roulette_score,
    COALESCE(winnings.Total_winnings_from_roulette, 0) AS Total_winnings_from_roulette,
    COALESCE(losses.Total_chips_lost_on_roulette, 0) AS Total_chips_lost_on_roulette,
    COUNT(main.id) AS Total_games_played_on_roulette,
    AVG(main.bet_amount) AS Average_bet_amount_on_roulette,
    MAX(main.result_amount) AS Maximum_win_on_roulette,
    MIN(main.result_amount) AS Biggest_loss_on_roulette,
    win_streak.max_streak AS Win_streak,
    lose_streak.max_streak AS Lose_streak,
	COALESCE(red.Hits_by_red, 0) AS Hits_by_red,
	COALESCE(bigwinred.Maximum_win_on_red, 0) AS Maximum_win_on_red,
	COALESCE(black.Hits_by_black, 0) AS Hits_by_black,
	COALESCE(bigwinblack.Maximum_win_on_black, 0) AS Maximum_win_on_black,
	COALESCE(green.Hits_by_green, 0) AS Hits_by_green,
	COALESCE(bigwingreen.Maximum_win_on_green, 0) AS Maximum_win_on_green,
	COALESCE(number.Hits_by_number, 0) AS Hits_by_number
	
	
    
FROM 
    game_history AS main
-- Wygrane
LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_winnings_from_roulette
    FROM game_history
    WHERE result_amount > 0 AND game_type = 'Roulette'
    GROUP BY user_name
) winnings ON main.user_name = winnings.user_name
-- Straty
LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_chips_lost_on_roulette
    FROM game_history
    WHERE result_amount < 0 AND game_type = 'Roulette'
    GROUP BY user_name
) losses ON main.user_name = losses.user_name
LEFT JOIN game_series AS win_streak ON win_streak.result_type = 1 AND win_streak.user_name = main.user_name AND win_streak.game_type ='Roulette'
LEFT JOIN game_series AS lose_streak ON lose_streak.result_type = -1 AND lose_streak.user_name = main.user_name AND lose_streak.game_type ='Roulette'
LEFT JOIN (
	SELECT user_name, COUNT(*) AS Hits_by_red 
	FROM game_history 
	WHERE game_type = 'Roulette' 
	AND TRIM(substr(note,-2)) %2 = 1 
	AND TRIM(substr(note,-2)) != 0 
	AND result_amount > 0 
	GROUP BY user_name
	) red ON red.user_name = main.user_name
LEFT JOIN (
	SELECT user_name, COUNT(*) AS Hits_by_black
	FROM game_history 
	WHERE game_type = 'Roulette' 
	AND TRIM(substr(note,-2)) %2 = 0 
	AND TRIM(substr(note,-2)) != 0 
	AND result_amount > 0 
	GROUP BY user_name
	) black ON black.user_name = main.user_name
LEFT JOIN (
	SELECT user_name, COUNT(*) AS Hits_by_green
	FROM game_history 
	WHERE game_type = 'Roulette' 
	AND result_amount > 0
	AND note LIKE 'Result: 0'
	GROUP BY user_name
	) green ON green.user_name = main.user_name
LEFT JOIN (
	SELECT user_name, COUNT(*) AS Hits_by_number
	FROM game_history 
	WHERE game_type = 'Roulette' 
	AND result_amount > 0 
	AND TRIM(substr(bet_command,-2,1)) = TRIM(substr(note,-2)) 
	GROUP BY user_name
	) number ON number.user_name = main.user_name
LEFT JOIN (
    SELECT user_name, MAX(result_amount) AS Maximum_win_on_red 
    FROM game_history 
    WHERE game_type = 'Roulette' 
    AND result_amount > 0 
    AND CAST(SUBSTR(note, -2) AS INTEGER) IN (1, 3, 5, 7, 9, 11)
    GROUP BY user_name
) bigwinred ON bigwinred.user_name = main.user_name
LEFT JOIN (
    SELECT user_name, MAX(result_amount) AS Maximum_win_on_black 
    FROM game_history 
    WHERE game_type = 'Roulette' 
    AND result_amount > 0 
    AND CAST(SUBSTR(note, -2) AS INTEGER) IN (2, 4, 6, 8, 10, 12)
    GROUP BY user_name
) bigwinblack ON bigwinblack.user_name = main.user_name
LEFT JOIN (
    SELECT user_name, MAX(result_amount) AS Maximum_win_on_green 
    FROM game_history 
    WHERE game_type = 'Roulette' 
    AND result_amount > 0 
    AND CAST(SUBSTR(note, -2) AS INTEGER) = 0 
    GROUP BY user_name
) bigwingreen ON bigwingreen.user_name = main.user_name

WHERE main.game_type = 'Roulette'
GROUP BY 
    main.user_name