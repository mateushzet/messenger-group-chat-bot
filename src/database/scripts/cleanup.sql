DELETE FROM user_bitcoin;
DELETE FROM blackjack_game;
DELETE FROM coinflip_games;
DELETE FROM logs;
DELETE FROM dice_game;
DELETE FROM game_history;
UPDATE jackpot set amount = 0, last_updated = date('now'), reset_at = date('now');
DELETE FROM rewards_history;
DELETE FROM user_avatars;
DELETE FROM user_skins;
DELETE FROM user_bets;
UPDATE users set account_balance = 0, daily_coins_claimed_at = null, hourly_reward_claimed_at = null, updated_at = date('now'), access_to_games = null;