CREATE TABLE balatro_game (
    user_name TEXT PRIMARY KEY,
    bet_amount INTEGER,
    player_hand TEXT,
    discard_pile TEXT,
    game_in_progress INTEGER,
    game_status INTEGER,
    selected_joker_id INTEGER,
    available_jokers TEXT,
    deck TEXT
);