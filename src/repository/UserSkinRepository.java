package repository;

import java.sql.*;

import database.DatabaseConnectionManager;
import utils.Logger;

public class UserSkinRepository {
    public static boolean assignSkinToUser(String username, String skinId) {
        String query = "INSERT INTO user_skins (user_name, skin_id) VALUES (?, ?) " +
                       "ON CONFLICT(user_name) DO UPDATE SET skin_id = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, username);
            statement.setString(2, skinId);
            statement.setString(3, skinId);

            int rowsAffected = statement.executeUpdate();
            return rowsAffected > 0;
        } catch (SQLException e) {
            Logger.logError("Error while assigning skin to user", "UserSkinRepository.assignSkinToUser()", e);
            return false;
        }
    }

    public static String getSkinForUser(String username) {
        String query = "SELECT skin_id FROM user_skins WHERE user_name = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, username);

            try (ResultSet resultSet = statement.executeQuery()) {
                if (resultSet.next()) {
                    return resultSet.getString("skin_id");
                }
            }
        } catch (SQLException e) {
            Logger.logError("Error while fetching skin for user", "UserSkinRepository.getSkinForUser()", e);
        }
        return null;
    }
}
