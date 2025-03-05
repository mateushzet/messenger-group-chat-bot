CREATE TABLE IF NOT EXISTS rewards_history (
    user_name TEXT NOT NULL,
    reward_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);