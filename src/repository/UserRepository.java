package repository;

import app.App;
import service.MessageService;
import utils.LoggerUtil;

import java.io.*;
import java.util.*;

public class UserRepository {

    public static Map<String, Integer> getAllUsers() {
        List<String> lines = readFile(App.USERS_MONEY_FILE_PATH);
        Map<String, Integer> userBalances = new HashMap<>();
        for (String line : lines) {
            String[] parts = line.split(": ");
            if (parts.length == 2) {
                String userName = parts[0].trim();
                int balance = Integer.parseInt(parts[1].trim());
                userBalances.put(userName, balance);
            }
        }
        return userBalances;
    }

    public static boolean doesUserExist(String userName) {
        return getAllUsers().containsKey(userName.trim());
    }

    public static boolean handleTransfer(String senderName, String amount, String... receiverNameParts) {
        if (!validateTransferParams(amount, receiverNameParts)) return false;

        int transferAmount = parseTransferAmount(amount);
        if (transferAmount == -1) return false;

        String receiverName = buildFullName(receiverNameParts);
        if (!isValidReceiver(senderName, receiverName)) return false;

        addUserIfNotExists(senderName);

        int balanceSender = getUserBalance(senderName, true);
        int balanceReceiver = getUserBalance(receiverName, false);

        return processTransaction(senderName, receiverName, balanceSender, balanceReceiver, transferAmount);
    }

    private static boolean validateTransferParams(String amount, String... receiverNameParts) {
        if (amount == null || receiverNameParts == null || amount.trim().isEmpty() || Arrays.stream(receiverNameParts).anyMatch(String::isEmpty)) {
            LoggerUtil.logWarning("Invalid parameters: amount = %s, receiverNameParts = %s", amount, Arrays.toString(receiverNameParts));
            MessageService.sendMessage("Invalid transfer parameters.");
            return false;
        }
        return true;
    }

    private static int parseTransferAmount(String amount) {
        try {
            return Integer.parseInt(amount.trim());
        } catch (NumberFormatException e) {
            LoggerUtil.logWarning("Invalid transfer amount: %s", amount);
            MessageService.sendMessage("Invalid transfer amount.");
            return -1;
        }
    }

    private static String buildFullName(String... nameParts) {
        return String.join(" ", nameParts).trim();
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
            addUserToFile(userName, 0);
            LoggerUtil.logInfo("Added user to file: %s", userName);
        }
    }

    private static boolean processTransaction(String senderName, String receiverName, int balanceSender, int balanceReceiver, int transferAmount) {
        if (transferAmount <= 0 || balanceSender < transferAmount) {
            LoggerUtil.logWarning("Insufficient balance or invalid transfer amount.");
            MessageService.sendMessage("Insufficient balance or invalid transfer amount.");
            return false;
        }

        updateUserBalance(senderName, balanceSender - transferAmount);
        updateUserBalance(receiverName, balanceReceiver + transferAmount);

        LoggerUtil.logInfo("Transaction successful: %s -> %s, Amount: %d", senderName, receiverName, transferAmount);
        return true;
    }

    private static void notifyInvalidReceiver(String receiverName) {
        LoggerUtil.logWarning("Receiver not found or incorrect name: %s", receiverName);
        MessageService.sendMessage("The recipient has not activated their balance or the name is incorrect.");
    }

    private static void notifySameSenderAndReceiver(String senderName, String receiverName) {
        LoggerUtil.logWarning("Sender and receiver are the same: %s = %s", senderName, receiverName);
    }

    public static int getUserBalance(String userName, boolean createNewUser) {
        Map<String, Integer> userBalances = getAllUsers();
        if (userBalances.containsKey(userName.trim())) {
            return userBalances.get(userName.trim());
        }

        if (createNewUser) {
            addUserToFile(userName, 0);
            LoggerUtil.logInfo("Created new user: %s", userName);
            return 0;
        }
        return -1;
    }

    public static void updateUserBalance(String userName, int newBalance) {
        Map<String, Integer> userBalances = getAllUsers();
        userBalances.put(userName, newBalance);
        writeBalancesToFile(userBalances);
        LoggerUtil.logInfo("User balance updated: %s = %d", userName, newBalance);
    }

    public static void addUserToFile(String userName, int balance) {
        Map<String, Integer> userBalances = getAllUsers();
        userBalances.put(userName, balance);
        writeBalancesToFile(userBalances);
        LoggerUtil.logInfo("Added user: %s with balance: %d", userName, balance);
    }

    public static String getRanking() {
        Map<String, Integer> userBalances = getAllUsers();
        List<Map.Entry<String, Integer>> sortedUsers = new ArrayList<>(userBalances.entrySet());
        sortedUsers.sort((entry1, entry2) -> Integer.compare(entry2.getValue(), entry1.getValue()));

        StringBuilder ranking = new StringBuilder("Ranking of Users:\n");
        for (int i = 0; i < sortedUsers.size(); i++) {
            Map.Entry<String, Integer> entry = sortedUsers.get(i);
            ranking.append(i + 1).append(". ").append(entry.getKey()).append(" - ").append(entry.getValue()).append(" coins\n");
        }

        LoggerUtil.logInfo(ranking.toString());
        return ranking.toString();
    }

    private static List<String> readFile(String filePath) {
        List<String> lines = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(filePath), "UTF-8"))) {
            String line;
            while ((line = reader.readLine()) != null) {
                lines.add(line);
            }
        } catch (IOException e) {
            LoggerUtil.logError("Error reading file: %s", e, filePath);
        }
        return lines;
    }

    private static void writeBalancesToFile(Map<String, Integer> userBalances) {
        try (BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(App.USERS_MONEY_FILE_PATH), "UTF-8"))) {
            for (Map.Entry<String, Integer> entry : userBalances.entrySet()) {
                writer.write(entry.getKey() + ": " + entry.getValue());
                writer.newLine();
            }
        } catch (IOException e) {
            LoggerUtil.logError("Error writing balances to file.", e);
        }
    }
}