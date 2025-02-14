package repository;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

import database.DatabaseConnectionManager;
import utils.Logger;

public class UserAvatarRepository {
    public static boolean assignAvatarToUser(String username, String avatarId) {
        String query = "INSERT INTO user_avatars (user_name, avatar_id) VALUES (?, ?)";
    
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
    
            statement.setString(1, username);
            statement.setString(2, avatarId);
    
            int rowsAffected = statement.executeUpdate();
            return rowsAffected > 0;
        } catch (SQLException e) {
            Logger.logError("Error while assigning avatar to user", "UserAvatarRepository.assignAvatarsToUser()", e);
            return false;
        }
    }

    public static List<String> getAllAvatarsForUser(String username) {
        String query = "SELECT avatar_id FROM user_avatars WHERE user_name = ?";
        List<String> avatars = new ArrayList<>();

        try (Connection connection = DatabaseConnectionManager.getConnection();
            PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, username);

            try (ResultSet resultSet = statement.executeQuery()) {
                while (resultSet.next()) {
                    avatars.add(resultSet.getString("avatar_id"));
                }
            }
        } catch (SQLException e) {
            Logger.logError("Error while fetching avatars for user", "UserAvatarRepository.getAllavAtarsForUser()", e);
        }
        return avatars;
    }

    public static String getActiveAvatarForUser(String username) {
        String query = "SELECT avatar_id FROM user_avatars WHERE user_name = ? AND is_active = 1";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
    
            statement.setString(1, username);
    
            try (ResultSet resultSet = statement.executeQuery()) {
                if (resultSet.next()) {
                    return resultSet.getString("avatar_id");
                }
            }
        } catch (SQLException e) {
            Logger.logError("Error while fetching active avatar for user", "UserAvatarRepository.getActiveAvatarForUser()", e);
        }
        return null;
    }

    public static boolean updateActiveAvatarForUser(String username, String avatarId) {
        String updateQuery = "UPDATE user_avatars SET is_active = 0 WHERE user_name = ? AND is_active = 1";
        String setActiveQuery = "UPDATE user_avatars SET is_active = 1 WHERE user_name = ? AND avatar_id = ?";
    
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            try (PreparedStatement statement = connection.prepareStatement(updateQuery)) {
                statement.setString(1, username);
                statement.executeUpdate();
            }
    
            try (PreparedStatement statement = connection.prepareStatement(setActiveQuery)) {
                statement.setString(1, username);
                statement.setString(2, avatarId);
                int rowsAffected = statement.executeUpdate();
    
                if (rowsAffected > 0) {
                    return true;
                } else {
                    return false;
                }
            } catch (SQLException e) {
                Logger.logError("Error while setting active avatar", "UserAvatarRepository.updateActiveAvatarForUser()", e);
                return false;
            }
        } catch (SQLException e) {
            Logger.logError("Error while updating active avatar", "UserAvatarRepository.updateActiveAvatarForUser()", e);
            return false;
        }
    }

}
