package repository;

import java.sql.*;
import database.DatabaseConnectionManager;

public class RewardsHistoryRepository {

    private static final String INSERT_REWARD_HISTORY = 
        "INSERT INTO rewards_history (user_id, reward_type, amount) VALUES (?, ?, ?)";

    public static void addRewardHistory(String username, String rewardType, double amount) {
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(INSERT_REWARD_HISTORY)) {

            statement.setString(1, username);
            statement.setString(2, rewardType);
            statement.setDouble(3, amount);

            statement.executeUpdate();

        } catch (SQLException e) {
            e.printStackTrace();
            System.err.println("Error adding reward history: " + e.getMessage());
        }
    }

}
