CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    account_balance INTEGER NOT NULL DEFAULT 0,
    access_to_games TEXT DEFAULT NULL,     
    daily_coins_claimed_at TEXT DEFAULT NULL,
    hourly_reward_claimed_at TEXT DEFAULT NULL,
    weekly_reward_claimed_at TEXT DEFAULT NULL,
    gift_claimed_at TEXT DEFAULT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    avatar_url TEXT,
    current_reward_level INTEGER DEFAULT 0
);