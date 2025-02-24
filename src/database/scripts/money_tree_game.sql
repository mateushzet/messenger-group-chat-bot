CREATE TABLE money_tree_game (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL UNIQUE,
    invested_coins INTEGER NOT NULL,
    phase_durations TEXT NOT NULL,
    wither_phase INTEGER NOT NULL,
    wither_time INTEGER NOT NULL,
    start_time INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

select * from money_tree_game