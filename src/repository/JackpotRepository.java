package repository;

import java.sql.*;

import database.DatabaseConnectionManager;
import utils.Logger;

public class JackpotRepository {

    public static int getJackpot() {
        String query = "SELECT amount FROM jackpot LIMIT 1";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             Statement statement = connection.createStatement();
             ResultSet resultSet = statement.executeQuery(query)) {
            
            if (resultSet.next()) {
                return resultSet.getInt("amount");
            }
        } catch (SQLException e) {
             Logger.logError("Error while geting jackpot amount", "DailyRewardRepository.getJackpot()", e);

        }
        return 0;
    }

    public static void addToJackpotPool(int betAmount) {
        int jackpotPool = getJackpot();
        jackpotPool += betAmount * 0.1;

        String query = "UPDATE jackpot SET amount = ?, last_updated = CURRENT_TIMESTAMP";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            
            statement.setInt(1, jackpotPool);
            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while updating jackpot amount", "DailyRewardRepository.addToJackpotPool()", e);
        }
    }

    public static void resetJackpot() {
        String query = "UPDATE jackpot SET amount = 0, last_updated = CURRENT_TIMESTAMP, reset_at = CURRENT_TIMESTAMP";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            
            statement.setInt(1, 0);
            statement.setTimestamp(2, new Timestamp(System.currentTimeMillis()));
            statement.setTimestamp(3, new Timestamp(System.currentTimeMillis()));
            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while reseting jackpot amount", "DailyRewardRepository.resetJackpot()", e);
        }
    }
}