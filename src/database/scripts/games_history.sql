CREATE TABLE game_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    bet_command VARCHAR(100) NOT NULL,
    bet_amount INTEGER NOT NULL,
    result_amount INT NOT NULL,
    note VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_name) REFERENCES users(user_name)
);
select * from game_history where game_type = 'Lotto' and user_name = 'konrad piwowarczyk' order by id desc

update users set account_balance = account_balance + 20 where user_id = 9