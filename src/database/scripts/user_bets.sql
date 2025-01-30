CREATE TABLE user_bets (
    bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL,
    match_id INT NOT NULL,
    bet_type VARCHAR(50) NOT NULL,
    bet_amount DECIMAL(10, 2) NOT NULL,
    odds DECIMAL(10, 2) DEFAULT 0.0,
    bet_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_paid BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_name) REFERENCES users(username),
    FOREIGN KEY (match_id) REFERENCES match_odds(match_id)
);

select * from users