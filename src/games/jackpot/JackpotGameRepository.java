package games.jackpot;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import database.DatabaseConnectionManager;

public class JackpotGameRepository {

    public static void addJackpotBet(String username, String betAmount, Timestamp timestamp) {
        String query = "INSERT INTO jackpot_bets (username, bet_amount, timestamp) VALUES (?, ?, ?)";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            statement.setString(1, username);
            statement.setInt(2, Integer.parseInt(betAmount));
            statement.setTimestamp(3, timestamp);
            statement.executeUpdate();
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    public static void deleteAllJackpotBets() {
        String query = "DELETE FROM jackpot_bets";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            statement.executeUpdate();
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    public static Map<String, Integer> getJackpotBets() {
        Map<String, Integer> bets = new HashMap<>();
        String query = "SELECT username, bet_amount FROM jackpot_bets";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query);
             ResultSet resultSet = statement.executeQuery()) {
            while (resultSet.next()) {
                String username = resultSet.getString("username");
                int betAmount = resultSet.getInt("bet_amount");
    
                bets.put(username, bets.getOrDefault(username, 0) + betAmount);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return bets;
    }

    public static Map<String, String> getUserAvatars(List<String> usernames) {
        Map<String, String> avatars = new HashMap<>();
        String query = "SELECT username, avatar_url FROM users WHERE username = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection();
            PreparedStatement statement = connection.prepareStatement(query)) {
            for (String username : usernames) {
                statement.setString(1, username);
                try (ResultSet resultSet = statement.executeQuery()) {
                    if (resultSet.next()) {
                        String avatarUrl = resultSet.getString("avatar_url");
                        avatars.put(username, avatarUrl);
                    }
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return avatars;
    }

    public static Timestamp getOldestTimestamp() {
        String query = "SELECT MIN(timestamp) AS oldest_timestamp FROM jackpot_bets";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query);
             ResultSet resultSet = statement.executeQuery()) {
            if (resultSet.next()) {
                return resultSet.getTimestamp("oldest_timestamp");
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return null;
    }

}