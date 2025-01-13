package repository;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

import database.DatabaseConnectionManager;
import model.GameHistory;

public class GameHistoryRepository {

    private static final String INSERT_GAME_HISTORY = 
        "INSERT INTO game_history (user_name, game_type, bet_command, bet_amount, result_amount, note) VALUES (?, ?, ?, ?, ?, ?)";

    private static final String SELECT_USER_HISTORY = 
        "SELECT id, user_name, game_type, bet_command, bet_amount, result_amount, note, created_at FROM game_history WHERE user_name = ? ORDER BY created_at DESC";

    public static void addGameHistory(String userName, String gameType, String betCommand, int betAmount, int resultAmount, String note) {
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(INSERT_GAME_HISTORY)) {

            statement.setString(1, userName);
            statement.setString(2, gameType);
            statement.setString(3, betCommand);
            statement.setInt(4, betAmount);
            statement.setInt(5, resultAmount);
            statement.setString(6, note);

            statement.executeUpdate();

        } catch (SQLException e) {
            e.printStackTrace();
            System.err.println("Error adding game history: " + e.getMessage());
        }
    }

    public static List<GameHistory> getUserHistory(String userName) {
        List<GameHistory> history = new ArrayList<>();

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(SELECT_USER_HISTORY)) {

            statement.setString(1, userName);
            ResultSet resultSet = statement.executeQuery();

            while (resultSet.next()) {
                GameHistory entry = new GameHistory(
                    resultSet.getInt("id"),
                    resultSet.getString("user_name"),
                    resultSet.getString("game_type"),
                    resultSet.getString("bet_command"),
                    resultSet.getInt("bet_amount"),
                    resultSet.getInt("result_amount"),
                    resultSet.getString("note"),
                    resultSet.getTimestamp("created_at").toLocalDateTime()
                );
                history.add(entry);
            }

        } catch (SQLException e) {
            e.printStackTrace();
            System.err.println("Error fetching user history: " + e.getMessage());
        }

        return history;
    }
}
