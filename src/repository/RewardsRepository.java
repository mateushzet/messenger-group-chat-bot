package repository;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.text.SimpleDateFormat;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.WeekFields;
import java.util.*;


import database.DatabaseConnectionManager;
import utils.Logger;

public class RewardsRepository {

    private static final String DATE_FORMAT = "yyyy-MM-dd";

    public static boolean hasReceivedDailyReward(String userName) {

        resetCurrentRewardLevelIfMissed(userName);

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
            Logger.logError("Error while checking daily reward info for user:  " + userName, "RewardsRepository.hasReceivedDailyReward()", e);
            return false;
        }
    }

    public static boolean hasReceivedWeeklyReward(String userName) {
        String query = "SELECT weekly_reward_claimed_at FROM users WHERE username = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
            PreparedStatement statement = connection.prepareStatement(query)) {
            
            statement.setString(1, userName);
            ResultSet resultSet = statement.executeQuery();

            if (!resultSet.next()) {
                return false;
            }

            String lastReceivedString = resultSet.getString("weekly_reward_claimed_at");
            if (lastReceivedString == null || lastReceivedString.isEmpty()) {
                return false;
            }

            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
            LocalDateTime lastReceivedDateTime = LocalDateTime.parse(lastReceivedString, formatter);
            LocalDateTime now = LocalDateTime.now();

            WeekFields weekFields = WeekFields.of(Locale.getDefault());
            int lastWeek = lastReceivedDateTime.toLocalDate().get(weekFields.weekOfWeekBasedYear());
            int currentWeek = now.toLocalDate().get(weekFields.weekOfWeekBasedYear());

            int lastYear = lastReceivedDateTime.toLocalDate().get(weekFields.weekBasedYear());
            int currentYear = now.toLocalDate().get(weekFields.weekBasedYear());

            return (lastYear == currentYear) && (lastWeek == currentWeek);

        } catch (SQLException e) {
            Logger.logError("Error while checking weekly reward info for user:  " + userName, "RewardsRepository.hasReceivedWeeklyReward()", e);
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
    
            String lastReceivedString = resultSet.getString("hourly_reward_claimed_at");

            if (lastReceivedString == null) {
                return false;
            }

            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
            LocalDateTime lastReceived = LocalDateTime.parse(lastReceivedString, formatter);
            LocalDateTime now = LocalDateTime.now();
    
            return lastReceived.getYear() == now.getYear() &&
                   lastReceived.getMonth() == now.getMonth() &&
                   lastReceived.getDayOfMonth() == now.getDayOfMonth() &&
                   lastReceived.getHour() == now.getHour();
    
        } catch (SQLException e) {
            Logger.logError("Error while checking hourly reward info for user:  " + userName, 
                            "RewardsRepository.hasReceivedHourlyReward()", e);
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
                Logger.logInfo("Successfully updated daily reward for user:  " + userName, "RewardsRepository.updateDailyReward()");
            } else {
                Logger.logWarning("User not found:  " + userName, "DailyRewardRepository.updateDailyReward()");
            }

        } catch (SQLException e) {
            Logger.logError("Error while updating daily reward info for user:  " + userName, "RewardsRepository.updateDailyReward()", e);
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
                Logger.logInfo("Successfully updated hourly reward for user:  " + userName, "RewardsRepository.updateHourlyReward()");
            } else {
                Logger.logWarning("User not found:  " + userName, "RewardsRepository.updateHourlyReward()");
            }

        } catch (SQLException e) {
            Logger.logError("Error while updating hourly reward info for user:  " + userName, "RewardsRepository.updateHourlyReward()", e);
        }
    }

    public static void updateWeeklyReward(String userName) {
        String query = "UPDATE users SET weekly_reward_claimed_at = ? WHERE username = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, getCurrentDateTime());
            statement.setString(2, userName);
            int rowsUpdated = statement.executeUpdate();

            if (rowsUpdated > 0) {
                Logger.logInfo("Successfully updated hourly reward for user: " + userName, "RewardsRepository.updateHourlyReward()");
            } else {
                Logger.logWarning("User not found:  " + userName, "RewardsRepository.updateHourlyReward()");
            }

        } catch (SQLException e) {
            Logger.logError("Error while updating hourly reward info for user:  " + userName, "RewardsRepository.updateHourlyReward()", e);
        }
    }

    public static void updateGiftTimestamp(String userName) {
        String query = "UPDATE users SET gift_claimed_at = ? WHERE username = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, getCurrentDate());
            statement.setString(2, userName);
            int rowsUpdated = statement.executeUpdate();

            if (rowsUpdated > 0) {
                Logger.logInfo("Successfully updated gift timestamp for user:  " + userName, "RewardsRepository.updateGiftTimestamp()");
            } else {
                Logger.logWarning("User not found:  " + userName, "RewardsRepository.updateGiftTimestamp()");
            }

        } catch (SQLException e) {
            Logger.logError("Error while updating daily reward info for user:  " + userName, "RewardsRepository.updateGiftTimestamp()", e);
        }
    }

    public static boolean hasSentDailyGift(String userName) {
        String query = "SELECT gift_claimed_at FROM users WHERE username = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            
            statement.setString(1, userName);
            ResultSet resultSet = statement.executeQuery();
            
            if (!resultSet.next()) {
                return false;
            }

            String lastReceivedDate = resultSet.getString("gift_claimed_at");
            String today = getCurrentDate();

            return today.equals(lastReceivedDate);

        } catch (SQLException e) {
            Logger.logError("Error while checking gift info for user:  " + userName, "RewardsRepository.hasSentDailyGift()", e);
            return false;
        }
    }

        public static int getCurrentRewardLevel(String userName) {
        String query = "SELECT current_reward_level FROM users WHERE username = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            
            statement.setString(1, userName);
            ResultSet resultSet = statement.executeQuery();
            
            if (!resultSet.next()) {
                return -1;
            }

            int current_reward_level = resultSet.getInt("current_reward_level");

            return current_reward_level;

        } catch (SQLException e) {
            Logger.logError("Error while checking current_reward_level info for user:  " + userName, "RewardsRepository.getCurrentRewardLevel()", e);
            return -1;
        }
    }

    public static void setCurrentRewardLevel(String userName, int level) {
        String query = "UPDATE users SET current_reward_level = ? WHERE username = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
            PreparedStatement statement = connection.prepareStatement(query)) {
            
            statement.setInt(1, level);
            statement.setString(2, userName);
            statement.executeUpdate();

        } catch (SQLException e) {
            Logger.logError("Error while setting current_reward_level for user: " + userName,
                            "RewardsRepository.setCurrentRewardLevel()", e);
        }
    }

    public static String getDailyRewardClaimDate(String userName) {
        String query = "SELECT daily_coins_claimed_at FROM users WHERE username = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
            PreparedStatement statement = connection.prepareStatement(query)) {
            
            statement.setString(1, userName);
            ResultSet resultSet = statement.executeQuery();

            if (resultSet.next()) {
                return resultSet.getString("daily_coins_claimed_at");
            }

        } catch (SQLException e) {
            Logger.logError("Error while getting daily_coins_claimed_at for user: " + userName,
                            "RewardsRepository.getDailyRewardClaimDate()", e);
        }

        return null;
    }

    public static void resetCurrentRewardLevelIfMissed(String userName) {
        String lastClaimed = getDailyRewardClaimDate(userName);
        String today = getCurrentDate();
        if (lastClaimed == null || lastClaimed.isEmpty()) return;

        LocalDate lastDate = LocalDate.parse(lastClaimed);
        LocalDate currentDate = LocalDate.parse(today);

        if (!lastDate.plusDays(1).equals(currentDate) && !lastDate.equals(currentDate)) {
            setCurrentRewardLevel(userName, 0);
        }
    }

    private static String getCurrentDate() {
        SimpleDateFormat dateFormat = new SimpleDateFormat(DATE_FORMAT);
        return dateFormat.format(new Date());
    }

    public static String getCurrentDateTime() {
        return LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
    }
}