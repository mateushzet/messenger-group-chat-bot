CREATE TABLE mines_game (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(255) NOT NULL,
    bet_amount INT NOT NULL,
    total_bombs INT NOT NULL,
    revealed_fields INT NOT NULL,
    game_in_progress BOOLEAN NOT NULL,
    bomb_board BLOB,
    revealed_board BLOB
);