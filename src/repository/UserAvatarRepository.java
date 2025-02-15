package repository;

import java.sql.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import database.DatabaseConnectionManager;
import utils.Logger;

public class UserAvatarRepository {
    public static boolean assignAvatarToUser(String username, String avatarId) {
        String[] conditions = {"Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"};
        Map<String, Integer> conditionPriority = new HashMap<>();
        conditionPriority.put("Factory New", 5);
        conditionPriority.put("Minimal Wear", 4);
        conditionPriority.put("Field-Tested", 3);
        conditionPriority.put("Well-Worn", 2);
        conditionPriority.put("Battle-Scarred", 1);
    
        String checkQuery = "SELECT avatar_id FROM user_avatars WHERE user_name = ?";
        String updateQuery = "UPDATE user_avatars SET avatar_id = ? WHERE user_name = ? AND avatar_id = ?";
        String insertQuery = "INSERT INTO user_avatars (user_name, avatar_id) VALUES (?, ?)";
    
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement checkStatement = connection.prepareStatement(checkQuery);
             PreparedStatement updateStatement = connection.prepareStatement(updateQuery);
             PreparedStatement insertStatement = connection.prepareStatement(insertQuery)) {
    
            checkStatement.setString(1, username);
            ResultSet resultSet = checkStatement.executeQuery();
    
            while (resultSet.next()) {
                String existingAvatarId = resultSet.getString("avatar_id");
    
                if (existingAvatarId.equals(avatarId)) {
                    return false;
                }
    
                String baseExisting = getBaseName(existingAvatarId);
                String baseNew = getBaseName(avatarId);
    
                boolean isExistingStatTrak = existingAvatarId.contains("StatTrak");
                boolean isNewStatTrak = avatarId.contains("StatTrak");
    
                if (baseExisting.equals(baseNew) && isExistingStatTrak == isNewStatTrak) {
                    String existingCondition = getCondition(existingAvatarId, conditions);
                    String newCondition = getCondition(avatarId, conditions);
    
                    if (existingCondition == null || newCondition == null) {
                        continue;
                    }
    
                    if (conditionPriority.get(newCondition) > conditionPriority.get(existingCondition)) {
                        updateStatement.setString(1, avatarId);
                        updateStatement.setString(2, username);
                        updateStatement.setString(3, existingAvatarId);
                        int updatedRows = updateStatement.executeUpdate();
                        return updatedRows > 0;
                    } else {
                        return false;
                    }
                }
            }
    
            insertStatement.setString(1, username);
            insertStatement.setString(2, avatarId);
            int rowsAffected = insertStatement.executeUpdate();
    
            return rowsAffected > 0;
        } catch (SQLException e) {
            Logger.logError("Error while assigning avatar to user", "UserAvatarRepository.assignAvatarToUser()", e);
            return false;
        }
    }
    
    private static String getBaseName(String avatarId) {
        return avatarId.replaceAll("(Factory New|Minimal Wear|Field-Tested|Well-Worn|Battle-Scarred|StatTrak)", "").trim();
    }

    private static String getCondition(String avatarId, String[] conditions) {
        for (String condition : conditions) {
            if (avatarId.contains(condition)) {
                return condition;
            }
        }
        return null;
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
