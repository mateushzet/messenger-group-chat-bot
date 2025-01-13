package repository;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

import database.DatabaseConnectionManager;
import utils.Logger;

public class UserSkinRepository {
    public static boolean assignSkinToUser(String username, String skinId) {
        String query = "INSERT INTO user_skins (user_name, skin_id) VALUES (?, ?)";
    
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
    
            statement.setString(1, username);
            statement.setString(2, skinId);
    
            int rowsAffected = statement.executeUpdate();
            return rowsAffected > 0;
        } catch (SQLException e) {
            Logger.logError("Error while assigning skin to user", "UserSkinRepository.assignSkinToUser()", e);
            return false;
        }
    }

    public static List<String> getAllSkinsForUser(String username) {
        String query = "SELECT skin_id FROM user_skins WHERE user_name = ?";
        List<String> skins = new ArrayList<>();

        try (Connection connection = DatabaseConnectionManager.getConnection();
            PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, username);

            try (ResultSet resultSet = statement.executeQuery()) {
                while (resultSet.next()) {
                    skins.add(resultSet.getString("skin_id"));
                }
            }
        } catch (SQLException e) {
            Logger.logError("Error while fetching skins for user", "UserSkinRepository.getAllSkinsForUser()", e);
        }
        return skins;
    }

    public static String getActiveSkinForUser(String username) {
        String query = "SELECT skin_id FROM user_skins WHERE user_name = ? AND is_active = 1";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
    
            statement.setString(1, username);
    
            try (ResultSet resultSet = statement.executeQuery()) {
                if (resultSet.next()) {
                    return resultSet.getString("skin_id");
                }
            }
        } catch (SQLException e) {
            Logger.logError("Error while fetching active skin for user", "UserSkinRepository.getActiveSkinForUser()", e);
        }
        return null;
    }

    public static boolean updateActiveSkinForUser(String username, String skinId) {
        String updateQuery = "UPDATE user_skins SET is_active = 0 WHERE user_name = ? AND is_active = 1";
        String setActiveQuery = "UPDATE user_skins SET is_active = 1 WHERE user_name = ? AND skin_id = ?";
    
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            try (PreparedStatement statement = connection.prepareStatement(updateQuery)) {
                statement.setString(1, username);
                statement.executeUpdate();
            }
    
            try (PreparedStatement statement = connection.prepareStatement(setActiveQuery)) {
                statement.setString(1, username);
                statement.setString(2, skinId);
                int rowsAffected = statement.executeUpdate();
    
                if (rowsAffected > 0) {
                    return true;
                } else {
                    return false;
                }
            } catch (SQLException e) {
                Logger.logError("Error while setting active skin", "UserSkinRepository.updateActiveSkinForUser()", e);
                return false;
            }
        } catch (SQLException e) {
            Logger.logError("Error while updating active skin", "UserSkinRepository.updateActiveSkinForUser()", e);
            return false;
        }
    }

}
