package repository;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import utils.Logger;
import database.DatabaseConnectionManager;

public class ColorsRepository {

    public static boolean giveColorsAccess(String userName) {
        String query = "UPDATE users SET access_to_colors = 1 WHERE username = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            
            statement.setString(1, userName);
            int rowsAffected = statement.executeUpdate();
            
            if (rowsAffected == 0) {
                Logger.logWarning("Error adding user colors access, can't find user: %s", "ColorsRepository.giveColorsAccess()", userName);
                return false;
            }
            return true;
        } catch (SQLException e) {
            Logger.logError("Error adding user colors access for user: %s", "ColorsRepository.giveColorsAccess()", e, userName);
            e.printStackTrace();
            return false;
        }
    }

    public static boolean hasColorsAccess(String playerName) {
        String query = "SELECT access_to_colors FROM users WHERE username = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            
            statement.setString(1, playerName);
            ResultSet resultSet = statement.executeQuery();
            
            if (resultSet.next()) {
                int access = resultSet.getInt("access_to_colors");
                return access == 1;
            }
        } catch (SQLException e) {
            Logger.logError("Error reading colors access from database for user: %s", "ColorsRepository.hasColorsAccess()", e, playerName);
        }
        return false;
    }

}
