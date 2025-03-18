package repository;

import database.DatabaseConnectionManager;
import utils.BitcoinPriceChecker;
import utils.Logger;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class BitcoinRepository {

    public static double getBitcoinBalance(String userName) {
        String query = "SELECT btc_balance FROM user_bitcoin WHERE username = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName.trim());
            ResultSet resultSet = statement.executeQuery();

            if (resultSet.next()) {
                return resultSet.getDouble("btc_balance");
            } else {
                addUserIfNotExists(userName);
                return 0.0;
            }
        } catch (SQLException e) {
            Logger.logError("Error while getting Bitcoin balance for user: " + userName, "BitcoinRepository.getBitcoinBalance()", e);
            return 0.0;
        }
    }

    public static int getBitcoinBalanceInCoins(String userName) {
        String query = "SELECT btc_balance FROM user_bitcoin WHERE username = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName.trim());
            ResultSet resultSet = statement.executeQuery();

            if (resultSet.next()) {
                double btcAmount = resultSet.getDouble("btc_balance");
                return (int)(btcAmount * BitcoinPriceChecker.getBitcoinPrice());
            } else {
                addUserIfNotExists(userName);
                return 0;
            }
        } catch (SQLException e) {
            Logger.logError("Error while getting Bitcoin balance for user: " + userName, "BitcoinRepository.getBitcoinBalance()", e);
            return 0;
        }
    }

    public static boolean updateBitcoinBalance(String userName, double newBalance) {
        String query = "UPDATE user_bitcoin SET btc_balance = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
    
            statement.setDouble(1, newBalance);
            statement.setString(2, userName);
            statement.executeUpdate();
            Logger.logInfo("Bitcoin balance updated: " + userName + " = " + newBalance + " BTC", "BitcoinRepository.updateBitcoinBalance()");
            return true;
        } catch (SQLException e) {
            Logger.logError("Error while updating Bitcoin balance for user: " + userName, "BitcoinRepository.updateBitcoinBalance()", e);
            return false;
        }
    }

    private static void addUserIfNotExists(String userName) {
        String query = "INSERT INTO user_bitcoin (username, btc_balance) VALUES (?, 0.0)";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName);
            statement.executeUpdate();
            Logger.logInfo("Added user to Bitcoin table: " + userName, "BitcoinRepository.addUserIfNotExists()");
        } catch (SQLException e) {
            Logger.logError("Error while adding user to Bitcoin table: " + userName, "BitcoinRepository.addUserIfNotExists()", e);
        }
    }
}