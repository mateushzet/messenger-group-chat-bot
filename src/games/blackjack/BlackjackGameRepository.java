package games.blackjack;

import java.sql.*;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import database.DatabaseConnectionManager;
import model.BlackjackGame;
import utils.Logger;

public class BlackjackGameRepository {

    public static void saveGame(BlackjackGame game) {
        String query = "INSERT INTO blackjack_game (user_name, balance, current_bet, player_hand, dealer_hand, game_in_progress, player_stands) VALUES (?, ?, ?, ?, ?, ?, ?)";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, game.getUserName());
            statement.setInt(2, game.getBalance());
            statement.setInt(3, game.getCurrentBet());
            statement.setString(4, convertHandToString(game.getPlayerHand()));
            statement.setString(5, convertHandToString(game.getDealerHand()));
            statement.setBoolean(6, game.isGameInProgress());
            statement.setBoolean(7, game.isPlayerStands());

            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while saving game", "BlackjackGameRepository.saveGame()", e);
        }
    }

    public static BlackjackGame getGameByUserName(String userName) {
        String query = "SELECT * FROM blackjack_game WHERE user_name = ? AND game_in_progress = 1";
    
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
    
            statement.setString(1, userName);
            ResultSet resultSet = statement.executeQuery();
    
            if (resultSet.next()) {
                List<String> playerHand = convertHandFromString(resultSet.getString("player_hand"));
                List<String> dealerHand = convertHandFromString(resultSet.getString("dealer_hand"));
    
                BlackjackGame game = new BlackjackGame(
                        resultSet.getString("user_name"),
                        resultSet.getInt("current_bet"),
                        playerHand,
                        dealerHand,
                        resultSet.getBoolean("game_in_progress"),
                        resultSet.getInt("balance")
                );
    
                game.setPlayerStands(resultSet.getBoolean("player_stands"));
    
                return game;
            }
        } catch (SQLException e) {
            Logger.logError("Error while fetching game by username", "BlackjackGameRepository.getGameByUserName()", e);
        }
        return null;
    }

    public static void updateGame(BlackjackGame game) {
        String query = "UPDATE blackjack_game SET balance = ?, current_bet = ?, player_hand = ?, dealer_hand = ?, game_in_progress = ?, player_stands = ? WHERE user_name = ? AND game_in_progress = 1";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setInt(1, game.getBalance());
            statement.setInt(2, game.getCurrentBet());
            statement.setString(3, convertHandToString(game.getPlayerHand()));
            statement.setString(4, convertHandToString(game.getDealerHand()));
            statement.setBoolean(5, game.isGameInProgress());
            statement.setBoolean(6, game.isPlayerStands());
            statement.setString(7, game.getUserName());

            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while updating game", "BlackjackGameRepository.updateGame()", e);
        }
    }

    public static void deleteGame(String userName) {
        String query = "DELETE FROM blackjack_game WHERE user_name = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName);
            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while deleting game", "BlackjackGameRepository.deleteGame()", e);
        }
    }

    private static String convertHandToString(List<String> hand) {
        return String.join(",", hand);
    }

    private static List<String> convertHandFromString(String handString) {
        List<String> hand = new ArrayList<>();
        if (handString != null && !handString.isEmpty()) {
            String[] cards = handString.split(",");
            Collections.addAll(hand, cards);
        }
        return hand;
    }
}
