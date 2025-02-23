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

        int balanceSender = getCurrentUserBalance(senderName, true);
        int balanceReceiver = getCurrentUserBalance(receiverName, false);

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

    public static int getCurrentUserBalance(String userName, boolean createNewUser) {
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

    public static boolean tryToUpdateUserBalance(String userName, int newBalance) {
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

    public static boolean updateUserBalance(String userName, int newBalance) {
        int retryCount = 0;
        while (retryCount < 5) {
            if (tryToUpdateUserBalance(userName, newBalance)) {
                return true;
            }
            retryCount++;
            if (retryCount >= 5) {
                Logger.logWarning("Failed to update user balance after 5 retries for user: %s", "UserRepository.updateUserBalance()", userName);
                return false;
            }
            try {
                Thread.sleep(1000);
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                Logger.logError("Thread interrupted while retrying update for user: %s", "UserRepository.updateUserBalance()", ie, userName);
                return false;
            }
        }
        return false;
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
        if (!sortedUsers.isEmpty() && sortedUsers.get(0).getValue() >= 500) {
            UserAvatarRepository.assignAvatarToUser(sortedUsers.get(0).getKey(), "1st");
        }
        if (sortedUsers.size() > 1 && sortedUsers.get(1).getValue() >= 500) {
            UserAvatarRepository.assignAvatarToUser(sortedUsers.get(1).getKey(), "2nd");
        }
        if (sortedUsers.size() > 2 && sortedUsers.get(2).getValue() >= 500) {
            UserAvatarRepository.assignAvatarToUser(sortedUsers.get(2).getKey(), "3rd");
        }
        return sortedUsers;
    }

    public static int getTotalUserBalance(String userName) {
        int totalBalance = 0;
        int totalBetInMines = 0;
        int totalBetInCoinflip = 0;
        //int totalAmountInBTC = 0;
        int btcAmount = 0;
    
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            String balanceQuery = "SELECT account_balance FROM users WHERE username = ?";
            try (PreparedStatement balanceStatement = connection.prepareStatement(balanceQuery)) {
                balanceStatement.setString(1, userName);
                ResultSet balanceResult = balanceStatement.executeQuery();
                if (balanceResult.next()) {
                    totalBalance = balanceResult.getInt("account_balance");
                }
            }
    
            String minesBetQuery = "SELECT SUM(bet_amount) AS total_bet FROM mines_game WHERE user_name = ?";
            try (PreparedStatement minesStatement = connection.prepareStatement(minesBetQuery)) {
                minesStatement.setString(1, userName);
                ResultSet minesResult = minesStatement.executeQuery();
                if (minesResult.next()) {
                    totalBetInMines = minesResult.getInt("total_bet");
                }
            }

            String coinflipBetQuery = "SELECT SUM(bet_amount) AS total_bet FROM coinflip_games WHERE player1_username = ?";
            try (PreparedStatement coinflipStatement = connection.prepareStatement(coinflipBetQuery)) {
                coinflipStatement.setString(1, userName);
                ResultSet coinflipResult = coinflipStatement.executeQuery();
                if (coinflipResult.next()) {
                    totalBetInCoinflip = coinflipResult.getInt("total_bet");
                }
            }

            //btcAmount = BitcoinRepository.getBitcoinBalanceInCoins(userName);
        
        } catch (SQLException e) {
            Logger.logError("Error while fetching user game stats", "SlotsService.getTotalUserGameStats()", e);
        }
    
        return totalBalance + totalBetInMines + totalBetInCoinflip + btcAmount;
    }

    public static boolean giveGameAccess(String userName, String gameName) {
        String query = "UPDATE users SET access_to_games = CONCAT(access_to_games, ?) WHERE username = ?";
    
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
    
            statement.setString(1, "," + gameName);
            statement.setString(2, userName);
            int rowsAffected = statement.executeUpdate();
    
            return rowsAffected > 0;
        } catch (SQLException e) {
            e.printStackTrace();
            return false;
        }
    }

    public static boolean hasGameAccess(String playerName, String gameName) {
        String query = "SELECT access_to_games FROM users WHERE username = ?";
    
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
    
            statement.setString(1, playerName);
            ResultSet resultSet = statement.executeQuery();
    
            if (resultSet.next()) {
                String accessToGames = resultSet.getString("access_to_games");
                System.out.println(accessToGames);
                System.out.println(gameName);
                if (accessToGames != null) {
                    return accessToGames.contains(gameName);
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return false;
    }

    public static void saveAvatarToDatabase(String username, String avatarUrl) {
        // Check if the user already exists
        if (userExists(username)) {
            // User exists, perform an UPDATE
            updateUserAvatar(username, avatarUrl);
        } else {
            // User does not exist, perform an INSERT and assign default skin
            insertUser(username, avatarUrl);
            UserSkinRepository.assignSkinToUser(username, "default");
            Logger.logInfo("Default skin assigned to user: " + username, "UserRepository.saveAvatarToDatabase()");
        }
    }
    
    private static boolean userExists(String username) {
        String query = "SELECT 1 FROM users WHERE username = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            statement.setString(1, username);
            try (ResultSet resultSet = statement.executeQuery()) {
                return resultSet.next(); // Returns true if the user exists
            }
        } catch (SQLException e) {
            Logger.logError("Failed to check if user exists", "UserRepository.userExists()", e);
            return false; // Assume user does not exist in case of error
        }
    }
    
    private static void updateUserAvatar(String username, String avatarUrl) {
        String query = "UPDATE users SET avatar_url = ? WHERE username = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            statement.setString(1, avatarUrl);
            statement.setString(2, username);
            int rowsUpdated = statement.executeUpdate();
    
            if (rowsUpdated > 0) {
                Logger.logInfo("Avatar URL updated for user: " + username, "UserRepository.updateUserAvatar()");
            } else {
                Logger.logWarning("No rows updated for user: " + username, "UserRepository.updateUserAvatar()");
            }
        } catch (SQLException e) {
            Logger.logError("Failed to update avatar URL in database", "UserRepository.updateUserAvatar()", e);
        }
    }
    
    private static void insertUser(String username, String avatarUrl) {
        String query = "INSERT INTO users (username, avatar_url, account_balance) VALUES (?, ?, 0)";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
            statement.setString(1, username);
            statement.setString(2, avatarUrl);
            int rowsInserted = statement.executeUpdate();
    
            if (rowsInserted > 0) {
                Logger.logInfo("User inserted with avatar URL: " + username, "UserRepository.insertUser()");
            } else {
                Logger.logWarning("No rows inserted for user: " + username, "UserRepository.insertUser()");
            }
        } catch (SQLException e) {
            Logger.logError("Failed to insert user into database", "UserRepository.insertUser()", e);
        }
    }

}