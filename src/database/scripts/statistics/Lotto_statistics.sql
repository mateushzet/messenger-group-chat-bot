CREATE VIEW Lotto_statistics_view AS 
SELECT
    main.user_name,
    SUM(main.bet_amount) AS Total_chips_bet_on_lotto,
    SUM(main.result_amount) AS Total_lotto_score,
    COALESCE(winnings.Total_winnings_from_lotto, 0) AS Total_winnings_from_lotto,
    COALESCE(losses.Total_chips_lost_on_lotto, 0) AS Total_chips_lost_on_lotto,
    COUNT(main.id) AS Total_games_played_on_lotto,
    AVG(main.bet_amount) AS Average_bet_amount_on_lotto,
    MAX(main.result_amount) AS Maximum_win_on_lotto,
    MIN(main.result_amount) AS Biggest_loss_on_lotto,
    COALESCE(win_streak.max_streak, 0) AS Win_streak,
    COALESCE(lose_streak.max_streak, 0) AS Lose_streak,
    COALESCE(single.Number_of_single_hits, 0) AS Number_of_single_hits,
    COALESCE(double_hits.Number_of_double_hits, 0) AS Number_of_double_hits,
    COALESCE(triple.Number_of_triple_hits, 0) AS Number_of_triple_hits,
    COALESCE(quadruple.Number_of_quadruple_hits, 0) AS Number_of_quadruple_hits,
    COALESCE(quintuple.Number_of_quintuple_hits, 0) AS Number_of_quintuple_hits,
    COALESCE(sextuple.Number_of_sextuple_hits, 0) AS Number_of_sextuple_hits
FROM 
    game_history AS main

LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_winnings_from_lotto
    FROM game_history
    WHERE result_amount > 0 AND game_type = 'Lotto'
    GROUP BY user_name
) winnings ON main.user_name = winnings.user_name

LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_chips_lost_on_lotto
    FROM game_history
    WHERE result_amount < 0 AND game_type = 'Lotto'
    GROUP BY user_name
) losses ON main.user_name = losses.user_name

LEFT JOIN game_series AS win_streak ON win_streak.result_type = 1 AND win_streak.user_name = main.user_name AND win_streak.game_type = 'Lotto'
LEFT JOIN game_series AS lose_streak ON lose_streak.result_type = -1 AND lose_streak.user_name = main.user_name AND lose_streak.game_type = 'Lotto'

LEFT JOIN (
    SELECT user_name, COUNT(*) AS Number_of_single_hits 
    FROM game_history 
    WHERE game_type = 'Lotto' 
    AND note LIKE '%Matches: 1%' 
    GROUP BY user_name
) single ON single.user_name = main.user_name

LEFT JOIN (
    SELECT user_name, COUNT(*) AS Number_of_double_hits 
    FROM game_history 
    WHERE game_type = 'Lotto' 
    AND note LIKE '%Matches: 2%' 
    GROUP BY user_name
) double_hits ON double_hits.user_name = main.user_name

LEFT JOIN (
    SELECT user_name, COUNT(*) AS Number_of_triple_hits 
    FROM game_history 
    WHERE game_type = 'Lotto' 
    AND note LIKE '%Matches: 3%' 
    GROUP BY user_name
) triple ON triple.user_name = main.user_name

LEFT JOIN (
    SELECT user_name, COUNT(*) AS Number_of_quadruple_hits 
    FROM game_history 
    WHERE game_type = 'Lotto' 
    AND note LIKE '%Matches: 4%' 
    GROUP BY user_name
) quadruple ON quadruple.user_name = main.user_name

LEFT JOIN (
    SELECT user_name, COUNT(*) AS Number_of_quintuple_hits 
    FROM game_history 
    WHERE game_type = 'Lotto' 
    AND note LIKE '%Matches: 5%' 
    GROUP BY user_name
) quintuple ON quintuple.user_name = main.user_name

LEFT JOIN (
    SELECT user_name, COUNT(*) AS Number_of_sextuple_hits 
    FROM game_history 
    WHERE game_type = 'Lotto' 
    AND note LIKE '%Matches: 6%' 
    GROUP BY user_name
) sextuple ON sextuple.user_name = main.user_name
WHERE main.game_type = 'Lotto'
GROUP BY 
    main.user_name,
    winnings.Total_winnings_from_lotto,
    losses.Total_chips_lost_on_lotto,
    win_streak.max_streak,
    lose_streak.max_streak,
    single.Number_of_single_hits,
    double_hits.Number_of_double_hits,
    triple.Number_of_triple_hits,
    quadruple.Number_of_quadruple_hits,
    quintuple.Number_of_quintuple_hits,
    sextuple.Number_of_sextuple_hits;