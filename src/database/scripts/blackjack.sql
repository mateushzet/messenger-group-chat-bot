CREATE TABLE blackjack_game (
    user_name TEXT NOT NULL,
    balance INTEGER NOT NULL,
    current_bet INTEGER NOT NULL,
    player_hand TEXT NOT NULL,
    dealer_hand TEXT NOT NULL,
    game_in_progress BOOLEAN NOT NULL,
    player_stands BOOLEAN NOT NULL
);


select * from blackjack_game