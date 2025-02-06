package games.coinflip;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

import database.DatabaseConnectionManager;
import model.CoinflipGame;
import utils.Logger;

public class CoinflipRepository {

    public static Integer addCoinflipGame(String player1Username, int betAmount) {
        String query = "INSERT INTO coinflip_games (player1_username, bet_amount, game_status) " +
                       "VALUES (?, ?, 'open')";
    
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query, Statement.RETURN_GENERATED_KEYS)) {
    
            statement.setString(1, player1Username);
            statement.setInt(2, betAmount);
            int rowsAffected = statement.executeUpdate();
    
            if (rowsAffected > 0) {
                try (ResultSet generatedKeys = statement.getGeneratedKeys()) {
                    if (generatedKeys.next()) {
                        return generatedKeys.getInt(1);
                    }
                }
            }
        } catch (SQLException e) {
            Logger.logError("Error while creating coinflip game for user: %s, bet amount: %d", "CoinflipRepository.addCoinflipGame()", e, player1Username, betAmount);
        }
    
        return null;
    }

    public static boolean updateGameResult(int gameId, String winnerUsername) {
        String query = "UPDATE coinflip_games SET winner_username = ?, game_status = 'finished', updated_at = CURRENT_TIMESTAMP WHERE game_id = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, winnerUsername);
            statement.setInt(2, gameId);
            int rowsAffected = statement.executeUpdate();
            
            return rowsAffected > 0;
        } catch (SQLException e) {
            Logger.logError("Error while updating game result, gameId: %d", "CoinflipRepository.updateGameResult()", e, gameId);
            return false;
        }
    }

    public static boolean cancelGame(int gameId) {
        String query = "UPDATE coinflip_games SET game_status = 'canceled', updated_at = CURRENT_TIMESTAMP WHERE game_id = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setInt(1, gameId);
            int rowsAffected = statement.executeUpdate();
            
            return rowsAffected > 0;
        } catch (SQLException e) {
            Logger.logError("Error while canceling game result, gameId: %d", "CoinflipRepository.cancelGame()", e, gameId);
            return false;
        }
    }
    
    public static List<CoinflipGame> getOpenGames() {
        List<CoinflipGame> openGames = new ArrayList<>();
        String query = "SELECT * FROM coinflip_games WHERE game_status = 'open'";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             Statement statement = connection.createStatement();
             ResultSet resultSet = statement.executeQuery(query)) {

            while (resultSet.next()) {
                CoinflipGame game = new CoinflipGame();
                game.setGameId(resultSet.getInt("game_id"));
                game.setPlayer1Username(resultSet.getString("player1_username"));
                game.setPlayer2Username(resultSet.getString("player2_username"));
                game.setBetAmount(resultSet.getInt("bet_amount"));
                game.setGameStatus(resultSet.getString("game_status"));
                game.setCreatedAt(resultSet.getTimestamp("created_at"));
                game.setUpdatedAt(resultSet.getTimestamp("updated_at"));
                openGames.add(game);
            }
        } catch (SQLException e) {
            Logger.logError("Error while getting open games", "CoinflipRepository.getOpenGames()", e);
        }

        return openGames;
    }

    public static CoinflipGame getGameById(int gameId) {
        CoinflipGame game = null;
        String query = "SELECT * FROM coinflip_games WHERE game_id = ? AND game_status = 'open'";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setInt(1, gameId);
            ResultSet resultSet = statement.executeQuery();

            if (resultSet.next()) {
                game = new CoinflipGame();
                game.setGameId(resultSet.getInt("game_id"));
                game.setPlayer1Username(resultSet.getString("player1_username"));
                game.setPlayer2Username(resultSet.getString("player2_username"));
                game.setBetAmount(resultSet.getInt("bet_amount"));
                game.setGameResult(resultSet.getString("game_result"));
                game.setWinnerUsername(resultSet.getString("winner_username"));
                game.setGameStatus(resultSet.getString("game_status"));
                game.setCreatedAt(resultSet.getTimestamp("created_at"));
                game.setUpdatedAt(resultSet.getTimestamp("updated_at"));
            }
        } catch (SQLException e) {
            Logger.logError("Error while getting coinflip game by ID", "CoinflipRepository.getGameById()", e);
        }

        return game;
    }

}
