package repository;

import database.DatabaseConnectionManager;
import service.MessageService;
import utils.Logger;

import java.sql.Statement;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.*;

public class UserRepository {

    public static boolean handleTransfer(String senderName, String amount, String receiverName) {
        if (!validateTransferParams(amount, receiverName)) return false;

        int transferAmount = parseTransferAmount(amount);
        if (transferAmount == -1) return false;

        if (!isValidReceiver(senderName, receiverName)) return false;

        addUserIfNotExists(senderName);

        int balanceSender = getUserBalance(senderName, true);
        int balanceReceiver = getUserBalance(receiverName, false);

        return processTransaction(senderName, receiverName, balanceSender, balanceReceiver, transferAmount);
    }

    public static boolean doesUserExist(String userName) {
        String query = "SELECT 1 FROM users WHERE username = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName.trim());
            ResultSet resultSet = statement.executeQuery();
            return resultSet.next();
        } catch (SQLException e) {
            Logger.logError("Error adding user colors access for user: %s", "UserRepository.doesUserExist()", e, userName);
        }
        return false;
    }

    private static boolean validateTransferParams(String amount, String receiverName) {
        if (amount == null || receiverName == null || amount.trim().isEmpty()) {
            Logger.logWarning("Invalid parameters: amount = %s, receiverName = %s", "UserRepository.validateTransferParams()", amount, receiverName);
            MessageService.sendMessage("Invalid transfer parameters.");
            return false;
        }
        return true;
    }

    private static int parseTransferAmount(String amount) {
        try {
            return Integer.parseInt(amount.trim());
        } catch (NumberFormatException e) {
            Logger.logWarning("Invalid transfer amount: %s", "UserRepository.parseTransferAmount()", amount);
            MessageService.sendMessage("Invalid transfer amount.");
            return -1;
        }
    }

    private static boolean isValidReceiver(String senderName, String receiverName) {
        if (!doesUserExist(receiverName)) {
            notifyInvalidReceiver(receiverName);
            return false;
        }

        if (senderName.equalsIgnoreCase(receiverName)) {
            notifySameSenderAndReceiver(senderName, receiverName);
            return false;
        }
        return true;
    }

    private static void addUserIfNotExists(String userName) {
        if (!doesUserExist(userName)) {
            addUserToDatabase(userName, 0);
            Logger.logInfo("Added user to database: %s", "UserRepository.addUserIfNotExists()", userName);
        }
    }

    private static boolean processTransaction(String senderName, String receiverName, int balanceSender, int balanceReceiver, int transferAmount) {
        if (transferAmount <= 0 || balanceSender < transferAmount) {
            Logger.logWarning("Insufficient balance or invalid transfer amount.", "UserRepository.processTransaction()");
            MessageService.sendMessage("Insufficient balance or invalid transfer amount.");
            return false;
        }

        updateUserBalance(senderName, balanceSender - transferAmount);
        updateUserBalance(receiverName, balanceReceiver + transferAmount);

        Logger.logInfo("Transaction successful: %s -> %s, Amount: %d", "UserRepository.processTransaction()", senderName, receiverName, transferAmount);
        return true;
    }

    private static void notifyInvalidReceiver(String receiverName) {
        Logger.logWarning("Receiver not found or incorrect name: %s", "UserRepository.notifyInvalidReceiver()", receiverName);
        MessageService.sendMessage("The recipient has not activated their balance or the name is incorrect.");
    }

    private static void notifySameSenderAndReceiver(String senderName, String receiverName) {
        Logger.logWarning("Sender and receiver are the same: %s = %s", "UserRepository.notifySameSenderAndReceiver()", senderName, receiverName);
    }

    public static int getUserBalance(String userName, boolean createNewUser) {
        String query = "SELECT account_balance FROM users WHERE username = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName.trim());
            ResultSet resultSet = statement.executeQuery();
            if (resultSet.next()) {
                return resultSet.getInt("account_balance");
            }

            if (createNewUser) {
                addUserToDatabase(userName, 0);
                Logger.logInfo("Created new user: %s", "UserRepository.getUserBalance()", userName);
                return 0;
            }
        } catch (SQLException e) {
            Logger.logError("Error while geting user balance for user: %s", "UserRepository.notifySameSenderAndReceiver()", e, userName);
        }
        return -1;
    }

    public static boolean updateUserBalance(String userName, int newBalance) {
        String query = "UPDATE users SET account_balance = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setInt(1, newBalance);
            statement.setString(2, userName);
            statement.executeUpdate();
            Logger.logInfo("User balance updated: %s = %d", "UserRepository.updateUserBalance()", userName, newBalance);
            return true;
        } catch (SQLException e) {
            Logger.logError("Error while updating user balance for user: %s", "UserRepository.updateUserBalance()", e, userName);
            return false;
        }
    }

    public static void addUserToDatabase(String userName, int balance) {
        String query = "INSERT INTO users (username, account_balance) VALUES (?, ?)";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName);
            statement.setInt(2, balance);
            statement.executeUpdate();
            Logger.logInfo("Added user: %s with balance: %d", "UserRepository.addUserToDatabase()", userName, balance);
        } catch (SQLException e) {
            Logger.logError("Error while adding user to database for user: %s", "UserRepository.addUserToDatabase()", e, userName);
        }
    }

    public static Map<String, Integer> getAllUsers() {
        Map<String, Integer> userBalances = new HashMap<>();
        String query = "SELECT username, account_balance FROM users";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             Statement statement = connection.createStatement();
             ResultSet resultSet = statement.executeQuery(query)) {

            while (resultSet.next()) {
                String userName = resultSet.getString("username");
                int balance = resultSet.getInt("account_balance");
                userBalances.put(userName, balance);
            }
        } catch (SQLException e) {
            Logger.logError("Error while getting all users from database", "UserRepository.getAllUsers()", e);
        }
        return userBalances;
    }

    public static List<Map.Entry<String, Integer>> getRanking() {
        Map<String, Integer> userBalances = getAllUsers();
        List<Map.Entry<String, Integer>> sortedUsers = new ArrayList<>(userBalances.entrySet());
        sortedUsers.removeIf(entry -> entry.getValue() == 0);
        sortedUsers.sort((entry1, entry2) -> Integer.compare(entry2.getValue(), entry1.getValue()));

        return sortedUsers;
    }
}