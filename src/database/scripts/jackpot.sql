CREATE TABLE IF NOT EXISTS jackpot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reset_at DATETIME DEFAULT NULL
);
