CREATE TABLE match_odds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INT,      
    home_team VARCHAR(255) NOT NULL,
    away_team VARCHAR(255) NOT NULL,
    commence_time TIMESTAMP NOT NULL,
    bookmaker VARCHAR(255) NOT NULL,
    home_odds DECIMAL(10, 2) DEFAULT NULL,
    draw_odds DECIMAL(10, 2) DEFAULT NULL,
    away_odds DECIMAL(10, 2) DEFAULT NULL,
    home_score INT DEFAULT NULL,
    away_score INT DEFAULT NULL,
    UNIQUE(home_team, away_team, commence_time, bookmaker) 
);
select * from match_odds