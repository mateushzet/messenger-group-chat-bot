CREATE TABLE jackpot_bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    bet_amount INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL
);