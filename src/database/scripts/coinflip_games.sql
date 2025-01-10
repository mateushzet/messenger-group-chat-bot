CREATE TABLE IF NOT EXISTS coinflip_games (
    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player1_username TEXT NOT NULL,
    player2_username TEXT,
    bet_amount INT NOT NULL DEFAULT 0,
    winner_username TEXT,
    game_status TEXT CHECK(game_status IN ('open', 'finished', 'canceled')) NOT NULL DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);