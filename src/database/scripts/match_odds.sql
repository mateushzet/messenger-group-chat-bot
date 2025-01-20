CREATE TABLE match_odds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,             -- Unikalny identyfikator rekordu
    match_id INT,      
    home_team VARCHAR(255) NOT NULL,               -- Nazwa drużyny gospodarza
    away_team VARCHAR(255) NOT NULL,               -- Nazwa drużyny gościa
    commence_time TIMESTAMP NOT NULL,              -- Czas rozpoczęcia meczu
    bookmaker VARCHAR(255) NOT NULL,               -- Nazwa bukmachera
    home_odds DECIMAL(10, 2) DEFAULT NULL,         -- Kurs na zwycięstwo drużyny gospodarza
    draw_odds DECIMAL(10, 2) DEFAULT NULL,         -- Kurs na remis
    away_odds DECIMAL(10, 2) DEFAULT NULL,         -- Kurs na zwycięstwo drużyny gościa
    home_score INT DEFAULT NULL,                   -- Wynik drużyny gospodarza
    away_score INT DEFAULT NULL,                   -- Wynik drużyny gościa
    UNIQUE(home_team, away_team, commence_time, bookmaker)  -- Zapewnienie unikalności kombinacji (mecz, bukmacher)
);

select * from match_odds
drop table match_odds