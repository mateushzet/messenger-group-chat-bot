CREATE VIEW Case_statistic_view AS 
SELECT
    main.user_name,
    SUM(main.bet_amount) AS Total_chips_bet_on_case,
    COALESCE(winnings.Total_winnings_from_case, 0) AS Total_winnings_from_case,
    COALESCE(losses.Total_loses_on_case, 0) AS Total_loses_on_case,
	(Total_winnings_from_case + Total_loses_on_case) AS Total_result_from_case,
    COUNT(main.id) AS Total_games_played_on_case,
    AVG(main.bet_amount) AS Average_bet_amount_on_case,
    MAX(main.result_amount) AS Maximum_win_on_case,
    MIN(main.result_amount) AS Biggest_loss_on_case
	
FROM 
    game_history AS main

LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_winnings_from_case
    FROM game_history
    WHERE result_amount > 0 AND game_type = 'Case'
    GROUP BY user_name
) winnings ON main.user_name = winnings.user_name

LEFT JOIN (
	SELECT user_name, (SUM(result_amount)-(SUM(bet_amount))) AS Total_loses_on_case
	FROM game_history 
	WHERE game_type = 'Case'
	GROUP BY user_name
) losses ON main.user_name = losses.user_name

WHERE main.game_type = 'Case' 
GROUP BY 
    main.user_name
    