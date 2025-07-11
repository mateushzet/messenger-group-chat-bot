package games.slots;

import java.sql.*;
import java.time.LocalDate;

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

    public static void setJackpot(double newJackpotAmount) {
        String query = "UPDATE jackpot SET amount = ?, last_updated = CURRENT_TIMESTAMP";
        
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            
            statement.setDouble(1, newJackpotAmount);
            statement.executeUpdate();
            
        } catch (SQLException e) {
            Logger.logError("Error while setting new jackpot amount", "JackpotRepository.setJackpotAfterPayout()", e);
        }
    }

    public static LocalDate getJackpotLastUpdatedDate() {
        String query = "SELECT last_updated FROM jackpot LIMIT 1";
        try (Connection connection = DatabaseConnectionManager.getConnection();
            Statement statement = connection.createStatement();
            ResultSet resultSet = statement.executeQuery(query)) {

            if (resultSet.next()) {
                Date sqlDate = resultSet.getDate("last_updated");
                if (sqlDate != null) {
                    return sqlDate.toLocalDate();
                }
            }
        } catch (SQLException e) {
            Logger.logError("Error while getting jackpot last_updated", "JackpotRepository.getJackpotLastUpdatedDate()", e);
        }
        return null;
    }
}