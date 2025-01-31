CREATE VIEW Slots_statistic_view AS
SELECT 
	
    main.user_name,
    SUM(main.bet_amount) AS Total_chips_bet_on_slots,
    SUM(main.result_amount) AS Total_slots_score,
    COALESCE(winnings.Total_winnings_from_slots, 0) AS Total_winnings_from_slots,
    COALESCE(losses.Total_chips_lost_on_slots, 0) AS Total_chips_lost_on_slots,
    COUNT(main.id) AS Total_games_played_on_slots,
    AVG(main.bet_amount) AS Average_bet_amount_on_slots,
    MAX(main.result_amount) AS Maximum_win_on_slots,
    MIN(main.result_amount) AS Biggest_loss_on_slots,
    COALESCE(jackpots.Biggest_jackpot, 0) AS Biggest_jackpot,
    COALESCE(jackpots.Jackpots_wins, 0) AS Jackpots_wins,
    jackpots.Jackpot_date,
	win_streak.max_streak AS Win_streak,
	lose_streak.max_streak AS Lose_streak
	
FROM 
    game_history AS main

LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_winnings_from_slots
    FROM game_history
    WHERE result_amount > 0 AND game_type = 'Slots'
    GROUP BY user_name
) winnings ON main.user_name = winnings.user_name

LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_chips_lost_on_slots
    FROM game_history
    WHERE result_amount < 0 AND game_type = 'Slots'
    GROUP BY user_name
) losses ON main.user_name = losses.user_name

LEFT JOIN (
    SELECT 
        user_name,
        MAX(result_amount) AS Biggest_jackpot,
        COUNT(*) AS Jackpots_wins,
        MAX(created_at) AS Jackpot_date
    FROM game_history
    WHERE note LIKE '%6-6-6%' 
    GROUP BY user_name
) jackpots ON main.user_name = jackpots.user_name
LEFT JOIN game_series AS win_streak ON win_streak.result_type = 1 AND win_streak.user_name = main.user_name AND win_streak.game_type ="Slots"
LEFT JOIN game_series AS lose_streak ON lose_streak.result_type = -1 AND lose_streak.user_name = main.user_name AND lose_streak.game_type ="Slots"
GROUP BY 
    main.user_name;