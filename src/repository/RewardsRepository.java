package repository;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.text.SimpleDateFormat;
import java.util.*;

import database.DatabaseConnectionManager;
import utils.Logger;

public class RewardsRepository {

    private static final String DATE_FORMAT = "yyyy-MM-dd";

    public static boolean hasReceivedDailyReward(String userName) {
        String query = "SELECT daily_coins_claimed_at FROM users WHERE username = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            
            statement.setString(1, userName);
            ResultSet resultSet = statement.executeQuery();
            
            if (!resultSet.next()) {
                return false;
            }

            String lastReceivedDate = resultSet.getString("daily_coins_claimed_at");
            String today = getCurrentDate();

            return today.equals(lastReceivedDate);

        } catch (SQLException e) {
            Logger.logError("Error while checking daily reward info for user: %s", "DailyRewardRepository.hasReceivedDailyReward()", e, userName);
            return false;
        }
    }

    public static boolean hasReceivedHourlyReward(String userName) {
        String query = "SELECT hourly_reward_claimed_at FROM users WHERE username = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            
            statement.setString(1, userName);
            ResultSet resultSet = statement.executeQuery();
            
            if (!resultSet.next()) {
                return false;
            }

            String lastReceivedDate = resultSet.getString("hourly_reward_claimed_at");
            String today = getCurrentDateTime();

            return today.equals(lastReceivedDate);

        } catch (SQLException e) {
            Logger.logError("Error while checking hourly reward info for user: %s", "HourlyRewardRepository.hasReceivedHourlyReward()", e, userName);
            return false;
        }
    }

    public static void updateDailyReward(String userName) {
        String query = "UPDATE users SET daily_coins_claimed_at = ? WHERE username = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, getCurrentDate());
            statement.setString(2, userName);
            int rowsUpdated = statement.executeUpdate();

            if (rowsUpdated > 0) {
                Logger.logInfo("Successfully updated daily reward for user: %s", "ColorsRepository.updateDailyReward()", userName);
            } else {
                Logger.logWarning("User not found: %s", "DailyRewardRepository.updateDailyReward()", userName);
            }

        } catch (SQLException e) {
            Logger.logError("Error while updating daily reward info for user: %s", "DailyRewardRepository.updateDailyReward()", e, userName);
        }
    }

    public static void updateHourlyReward(String userName) {
        String query = "UPDATE users SET hourly_reward_claimed_at = ? WHERE username = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, getCurrentDateTime());
            statement.setString(2, userName);
            int rowsUpdated = statement.executeUpdate();

            if (rowsUpdated > 0) {
                Logger.logInfo("Successfully updated hourly reward for user: %s", "ColorsRepository.updateHourlyReward()", userName);
            } else {
                Logger.logWarning("User not found: %s", "HourlyRewardRepository.updateHourlyReward()", userName);
            }

        } catch (SQLException e) {
            Logger.logError("Error while updating hourly reward info for user: %s", "HourlyRewardRepository.updateHourlyReward()", e, userName);
        }
    }

    private static String getCurrentDate() {
        SimpleDateFormat dateFormat = new SimpleDateFormat(DATE_FORMAT);
        return dateFormat.format(new Date());
    }

    private static String getCurrentDateTime() {
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH");
        return dateFormat.format(new Date());
    }
}