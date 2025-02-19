CREATE VIEW Plinko_specific_high_statistic_view AS 
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
    COALESCE(win_streak.Win_streak, 0) AS Win_streak,
    COALESCE(lose_streak.Lose_streak, 0) AS Lose_streak,
    COALESCE(hit_counts.Number_of_0x0_hits, 0) AS Number_of_0x0_hits,
    COALESCE(hit_counts.Number_of_0x2_hits, 0) AS Number_of_0x2_hits,
    COALESCE(hit_counts.Number_of_0x5_hits, 0) AS Number_of_0x5_hits,
    COALESCE(hit_counts.Number_of_2x1_hits, 0) AS Number_of_2x1_hits,
    COALESCE(hit_counts.Number_of_5x3_hits, 0) AS Number_of_5x3_hits,
    COALESCE(hit_counts.Number_of_x14_hits, 0) AS Number_of_x14_hits,
    COALESCE(hit_counts.Number_of_x50_hits, 0) AS Number_of_x50_hits,
    COALESCE(hit_counts.Number_of_x420_hits, 0) AS Number_of_x420_hits
FROM game_history AS main
LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_winnings_from_plinko
    FROM game_history
    WHERE result_amount > 0 AND game_type = 'Plinko'
    GROUP BY user_name
) winnings ON main.user_name = winnings.user_name
LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_chips_lost_on_plinko
    FROM game_history
    WHERE result_amount < 0 AND game_type = 'Plinko'
    GROUP BY user_name
) losses ON main.user_name = losses.user_name
LEFT JOIN (
    SELECT user_name, MAX(max_streak) AS Win_streak
    FROM game_series
    WHERE result_type = 1 AND game_type = 'Plinko'
    GROUP BY user_name
) win_streak ON main.user_name = win_streak.user_name
LEFT JOIN (
    SELECT user_name, MAX(max_streak) AS Lose_streak
    FROM game_series
    WHERE result_type = -1 AND game_type = 'Plinko'
    GROUP BY user_name
) lose_streak ON main.user_name = lose_streak.user_name
LEFT JOIN (
    SELECT user_name, 
        COUNT(CASE WHEN note LIKE '0.0' THEN 1 END) AS Number_of_0x0_hits,
        COUNT(CASE WHEN note LIKE '0.2' THEN 1 END) AS Number_of_0x2_hits,
        COUNT(CASE WHEN note LIKE '0.5' THEN 1 END) AS Number_of_0x5_hits,
        COUNT(CASE WHEN note LIKE '2.1' THEN 1 END) AS Number_of_2x1_hits,
        COUNT(CASE WHEN note LIKE '5.3' THEN 1 END) AS Number_of_5x3_hits,
        COUNT(CASE WHEN note LIKE '14.0' THEN 1 END) AS Number_of_x14_hits,
        COUNT(CASE WHEN note LIKE '50.0' THEN 1 END) AS Number_of_x50_hits,
        COUNT(CASE WHEN note LIKE '420.0' THEN 1 END) AS Number_of_x420_hits
    FROM game_history
    WHERE game_type = 'Plinko'
    GROUP BY user_name
) hit_counts ON main.user_name = hit_counts.user_name
WHERE main.game_type = 'Plinko' AND main.bet_command LIKE '%h%'
GROUP BY main.user_name;
