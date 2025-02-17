CREATE VIEW Blackjack_statistic_view AS 
SELECT
    main.user_name,
    SUM(main.bet_amount) AS Total_chips_bet_on_blackjack,
    SUM(main.result_amount) AS Total_blackjack_score,
    COALESCE(winnings.Total_winnings_from_blackjack, 0) AS Total_winnings_from_blackjack,
    COALESCE(losses.Total_chips_lost_on_blackjack, 0) AS Total_chips_lost_on_blackjack,
    COUNT(main.id) AS Total_games_played_on_blackjack,
    AVG(main.bet_amount) AS Average_bet_amount_on_blackjack,
    MAX(main.result_amount) AS Maximum_win_on_blackjack,
    MIN(main.result_amount) AS Biggest_loss_on_blackjack,
    COALESCE(win_streak.max_streak, 0) AS Win_streak,
    COALESCE(lose_streak.max_streak, 0) AS Lose_streak,
	COALESCE(BJ_Counter.blackjack_counter, 0) AS BJ_Counter

FROM 
    game_history AS main

LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_winnings_from_blackjack
    FROM game_history
    WHERE result_amount > 0 AND game_type = 'Blackjack'
    GROUP BY user_name
) winnings ON main.user_name = winnings.user_name

LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_chips_lost_on_blackjack
    FROM game_history
    WHERE result_amount < 0 AND game_type = 'Blackjack'
    GROUP BY user_name
) losses ON main.user_name = losses.user_name

LEFT JOIN game_series AS win_streak ON win_streak.result_type = 1 AND win_streak.user_name = main.user_name AND win_streak.game_type = 'Blackjack'
LEFT JOIN game_series AS lose_streak ON lose_streak.result_type = -1 AND lose_streak.user_name = main.user_name AND lose_streak.game_type = 'Blackjack'
LEFT JOIN (
	SELECT user_name, COUNT(*) AS Blackjack_counter 
	FROM game_history 
	WHERE game_type = 'Blackjack' 
	AND result_amount = (bet_amount * 2.5) 
	) BJ_Counter ON main.user_name = BJ_Counter.user_name

WHERE main.game_type = 'Blackjack'
GROUP BY 
    main.user_name
    