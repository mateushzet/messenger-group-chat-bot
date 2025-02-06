package repository;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import utils.Logger;
import database.DatabaseConnectionManager;

public class SlotsRepository {

    public static boolean giveSlotsAccess(String userName) {
        String query = "UPDATE users SET access_to_slots = 1 WHERE username = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            
            statement.setString(1, userName);
            int rowsAffected = statement.executeUpdate();
            
            if (rowsAffected == 0) {
                Logger.logWarning("Error adding user slots access, can't find user: %s", "SlotsRepository.giveSlotsAccess()", userName);
                return false;
            }
            return true;
        } catch (SQLException e) {
            Logger.logError("Error adding user slots access for user: %s", "SlotsRepository.giveSlotsAccess()", e, userName);
            e.printStackTrace();
            return false;
        }
    }

    public static boolean hasSlotsAccess(String playerName) {
        String query = "SELECT access_to_slots FROM users WHERE username = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            
            statement.setString(1, playerName);
            ResultSet resultSet = statement.executeQuery();
            
            if (resultSet.next()) {
                int access = resultSet.getInt("access_to_slots");
                return access == 1;
            }
        } catch (SQLException e) {
            Logger.logError("Error reading slots access from database for user: %s", "SlotsRepository.hasSlotsAccess()", e, playerName);
        }
        return false;
    }

}