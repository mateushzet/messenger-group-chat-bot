CREATE VIEW Mines_statistic_view AS
SELECT 
    main.user_name,
    SUM(main.bet_amount) AS Total_chips_bet_on_mines,
    SUM(main.result_amount) AS Total_mines_score,
    COALESCE(winnings.Total_winnings_from_mines, 0) AS Total_winnings_from_mines,
    COALESCE(losses.Total_chips_lost_on_mines, 0) AS Total_chips_lost_on_mines,
    COUNT(main.id) AS Total_games_played_on_mines,
    AVG(main.bet_amount) AS Average_bet_amount_on_mines,
    MAX(main.result_amount) AS Maximum_win_on_mines,
    MIN(main.result_amount) AS Biggest_loss_on_mines,
    win_streak.max_streak AS Win_streak,
    lose_streak.max_streak AS Lose_streak,
    COALESCE(revealed_values.Tiles_revealed, 0) AS Tiles_revealed,
	COALESCE(bombs.Bombs_detonated, 0) AS Bombs_detonated,
	COALESCE(mines_wins.Games_fully_cleared, 0) AS Games_fully_cleared
    
FROM 
    game_history AS main

LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_winnings_from_mines
    FROM game_history
    WHERE result_amount > 0 AND game_type = 'Mines'
    GROUP BY user_name
) winnings ON main.user_name = winnings.user_name

LEFT JOIN (
    SELECT user_name, SUM(result_amount) AS Total_chips_lost_on_mines
    FROM game_history
    WHERE result_amount < 0 AND game_type = 'Mines'
    GROUP BY user_name
) losses ON main.user_name = losses.user_name
LEFT JOIN game_series AS win_streak ON win_streak.result_type = 1 AND win_streak.user_name = main.user_name AND win_streak.game_type ='Mines'
LEFT JOIN game_series AS lose_streak ON lose_streak.result_type = -1 AND lose_streak.user_name = main.user_name AND lose_streak.game_type ='Mines'

LEFT JOIN (
    WITH extracted_data AS (
        SELECT 
            game_history.user_name,
            REPLACE(SUBSTR(note, INSTR(note, 'RevealedFields: ') + LENGTH('RevealedFields: ')), ',', '') AS revealed_values
        FROM game_history
        WHERE INSTR(note, 'RevealedFields: ') > 0
    )
    SELECT 
        user_name,
        SUM(CAST(SUBSTR(revealed_values, i, 1) AS INTEGER)) AS Tiles_revealed
    FROM extracted_data
    CROSS JOIN (SELECT 1 AS i UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 
                UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10
                UNION ALL SELECT 11 UNION ALL SELECT 12 UNION ALL SELECT 13 UNION ALL SELECT 14 UNION ALL SELECT 15
                UNION ALL SELECT 16 UNION ALL SELECT 17 UNION ALL SELECT 18 UNION ALL SELECT 19 UNION ALL SELECT 20
                UNION ALL SELECT 21 UNION ALL SELECT 22 UNION ALL SELECT 23 UNION ALL SELECT 24 ) AS numbers
    WHERE i <= LENGTH(revealed_values)
    GROUP BY user_name
) revealed_values ON main.user_name = revealed_values.user_name
LEFT JOIN (
	SELECT user_name, COUNT(*) AS Bombs_detonated 
	FROM game_history 
	WHERE game_type='Mines' 
	AND result_amount < 0 
	GROUP BY user_name
	) bombs ON main.user_name = bombs.user_name
LEFT JOIN (
	SELECT user_name, COUNT(*) AS Games_fully_cleared
	FROM game_history 
	WHERE game_type='Mines' 
	AND result_amount > 0 
	AND bet_command 
	NOT LIKE '%cashout%' 
	GROUP BY user_name
	) mines_wins ON mines_wins.user_name = main.user_name
WHERE main.game_type = 'Mines'
GROUP BY 
    main.user_name