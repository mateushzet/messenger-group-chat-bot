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
select * from game_history order by id desc


select * from game_history where game_type = 'Slots' and note = 'Result: 6-6-6'