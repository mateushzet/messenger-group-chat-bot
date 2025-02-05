CREATE TABLE dice_game (
    user_name VARCHAR(255) PRIMARY KEY,
    balance INT,
    current_bet INT,
    dice_rolls VARCHAR(255),
    game_in_progress BOOLEAN,
    player_stands BOOLEAN
);