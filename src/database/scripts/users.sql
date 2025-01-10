CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    account_balance INTEGER NOT NULL DEFAULT 0,
    access_to_colors INTEGER NOT NULL DEFAULT 0,
    access_to_slots INTEGER NOT NULL DEFAULT 0,
    daily_coins_claimed_at TEXT DEFAULT NULL,
    hourly_reward_claimed_at TEXT DEFAULT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);