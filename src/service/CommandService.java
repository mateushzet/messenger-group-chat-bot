package service;

import repository.UserRepository;
import repository.RewardsHistoryRepository;
import repository.RewardsRepository;
import repository.UserAvatarRepository;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.LocalTime;
import java.util.List;
import java.util.Map;
import java.util.Random;

import utils.ConfigReader;
import utils.HelpDataProvider;
import utils.HelpImageGenerator;
import utils.Logger;
import utils.RankingImageGenerator;
import app.App;
import controller.CommandController;
import database.DatabaseConnectionManager;
import model.CommandContext;
import model.GameHelp;

public class CommandService {
    
    private static int dailyRewardPrize = ConfigReader.getDailyRewardPrize();
    private static int hourlyRewardPrize = ConfigReader.getHourlyRewardPrize();
    private static int coinFlipAmount = 0;
    private static String coinFlipCurrentPlayer = "";

    public static void handleMoneyCommand(CommandContext context) {
        String userName = context.getUserName();
        int balance = UserRepository.getCurrentUserBalance(userName, true);
        if(balance >= 1000) UserAvatarRepository.assignAvatarToUser(userName, "1000");
        if(balance >= 10000) UserAvatarRepository.assignAvatarToUser(userName, "10000");
        if(balance >= 100000) UserAvatarRepository.assignAvatarToUser(userName, "100000");
        if(balance >= 1000000) UserAvatarRepository.assignAvatarToUser(userName, "1000000");
        if(balance >= 10000000) UserAvatarRepository.assignAvatarToUser(userName, "10000000");
        MessageService.sendMessage(userName + ", current balance: " + balance);
        Logger.logInfo(userName + ", current balance: " + balance,"CommandService.handleMoneyCommand()");
    }

    public static void handleTimeCommand(CommandContext context) {
        MessageService.sendMessage("Current time: " + java.time.LocalTime.now());
    }

    public static void handleKillCommand(CommandContext context) {
        String userName = context.getUserName();
        String adminName = ConfigReader.getAdminName();

        if (!userName.equals(adminName)) {
            MessageService.sendMessage(userName + ", you have no rights to use admin commands!");
            return;
        }

        MessageService.sendMessage("Shutting down the bot");
        Logger.logInfo("Shutting down the bot at the request of " + context.getUserName(), "CommandService.handleKillCommand()");
        System.exit(0);
    }

    public static void handleStopCommand(CommandContext context) {
        String userName = context.getUserName();
        String adminName = ConfigReader.getAdminName();

        if (!userName.equals(adminName)) {
            MessageService.sendMessage(userName + ", you have no rights to use admin commands!");
            return;
        }
        
        MessageService.sendMessage("Status: stopped");
        App.running = 0;
    }

    public static void handleStartCommand(CommandContext context) {
        String userName = context.getUserName();
        String adminName = ConfigReader.getAdminName();

        if (!userName.equals(adminName)) {
            MessageService.sendMessage(userName + ", you have no rights to use admin commands!");
            return;
        }

        MessageService.sendMessage("Status: running");
        App.running = 1;
    }

    public static void handleStatusCommand(CommandContext context) {
        String status = (App.running == 1) ? "running" : "stopped";
        MessageService.sendMessage("Status: " + status);
    }

    public static void handleSayCommand(CommandContext context) {
        String text = String.join(" ", context.getArguments());
        MessageService.sendMessage(text);
    }
    
    public static void handleAnswerCommand(CommandContext context) {
        String answer = context.getFirstArgument();
        MathQuestionService.handleMathAnswer(answer, context.getUserName());
    }

    public static void handleTransferCommand(CommandContext context) {
        String amount = context.getFirstArgument();
        List<String> receiverNameParts = context.getArguments().subList(1, context.getArguments().size());
        String receiverName =  String.join(" ", receiverNameParts);
        String senderName = context.getUserName();

        if (receiverName.startsWith("@")) {
            receiverName = receiverName.substring(1);
        }

        boolean correctTransfer = UserRepository.handleTransfer(senderName, amount, receiverName);
        
        if (correctTransfer) {
            MessageService.sendMessage("Transferred " + amount + " coins to " + receiverName);
        } else {
            MessageService.sendMessage("Transfer failed");
            Logger.logWarning("Transfer failed sender: " + senderName + ", amount: " + amount + ", receiver: " + receiverName, "CommandService.handleTransferCommand()");
        }
    }

    public static void handleGiftCommand(CommandContext context) {
        String userName = context.getUserName();
        List<String> receiverNameParts = context.getArguments().subList(0, context.getArguments().size());
        String receiverName = String.join(" ", receiverNameParts);

        if (receiverName.startsWith("@")) {
            receiverName = receiverName.substring(1);
        }


        try {

            if (userName.toLowerCase().equals(receiverName.toLowerCase())) {
                MessageService.sendMessage("You can't send a gift to yourself.");
                return;
            }

            if (RewardsRepository.hasSentDailyGift(userName)) {
                MessageService.sendMessage("You have already sent a gift today.");
                return;
            }

            boolean correctTransfer = UserRepository.processGiftCommand(userName.toLowerCase(), dailyRewardPrize, receiverName.toLowerCase());

            if (correctTransfer) {
                MessageService.sendMessage(userName + " has sent a gift of " + dailyRewardPrize + " coins to " + receiverName + "!");
                Logger.logInfo("User " + userName + " sent a gift of " + dailyRewardPrize + " to " + receiverName, "CommandService.handleGiftCommand()");
                RewardsHistoryRepository.addRewardHistory(userName, "Gift Sent", dailyRewardPrize);
                RewardsHistoryRepository.addRewardHistory(receiverName, "Gift Received", dailyRewardPrize);
            } else {
                Logger.logWarning("Error processing gift from " + userName + " to " + receiverName, "CommandService.handleGiftCommand()");
                MessageService.sendMessage("An error occurred while sending your gift. Please try again later.");
            }
    

        } catch (Exception e) {
            Logger.logError("Error processing gift from " + userName + " to " + receiverName, "CommandService.handleGiftCommand()", e);
            MessageService.sendMessage("An error occurred while sending your gift. Please try again later.");
        }
    }


    public static void handleRankCommand(CommandContext context) {
        List<Map.Entry<String, Integer>> rankingString = UserRepository.getRanking();
        RankingImageGenerator.generateRankingImage(rankingString, context.getUserName());
        MessageService.sendMessageFromClipboard(true);
    }

    public static void handleHelpCommand(CommandContext context) {
        String userName = context.getUserName();
        String categoryName = context.getFirstArgument();

        GameHelp gameHelp = HelpDataProvider.getGameHelp(categoryName);

        if(gameHelp.getDescription().equals("Unknown game")){
            if (categoryName.equalsIgnoreCase("games")) {
                HelpImageGenerator.generateGameList(userName);
                MessageService.sendMessageFromClipboard(true);
            } else if (categoryName.equalsIgnoreCase("rewards")) {
                HelpImageGenerator.generateRewardsList(userName);
                MessageService.sendMessageFromClipboard(true);
            } else if (categoryName.equalsIgnoreCase("settings")) {
                //HelpImageGenerator.generateSettingsList(userName);
                MessageService.sendMessage("settings help is not implemented yet");
            } else if (categoryName.equals("")) {
                HelpImageGenerator.generateMainMenu(userName);
                MessageService.sendMessageFromClipboard(true);
            } else {
                MessageService.sendMessage("Invalid help command");
            }

        } else {
            HelpImageGenerator.generateGameHelp(categoryName, userName);
            MessageService.sendMessageFromClipboard(true);
        }
    }

    public static void handleDailyCommand(CommandContext context) {
        String userName = context.getUserName();
        
        try {
            if (RewardsRepository.hasReceivedDailyReward(userName)) {
                MessageService.sendMessage("You have already claimed your daily reward.");
                Logger.logInfo("User " + userName + " tried to claim daily reward but already received it.","CommandService.handleDailyCommand()");
                return;
            }
            
            int currentBalance = UserRepository.getCurrentUserBalance(userName, true);
            int newBalance = currentBalance + dailyRewardPrize;
    
            UserRepository.updateUserBalance(userName, newBalance);
            RewardsRepository.updateDailyReward(userName);
    
            MessageService.sendMessage(userName + " has claimed the daily reward. Current balance: " + newBalance);
            Logger.logInfo("User " + userName + " claimed daily reward. New balance: " + newBalance, "CommandService.handleDailyCommand()");
            RewardsHistoryRepository.addRewardHistory(userName, "Daily", dailyRewardPrize);
        } catch (Exception e) {
            Logger.logError("Error processing daily reward for user " + userName, "CommandService.handleDailyCommand()", e);
            MessageService.sendMessage("An error occurred while claiming your daily reward. Please try again later.");
        }
    }

    public static void handleWeeklyCommand(CommandContext context) {
        String userName = context.getUserName();
        
        try {
            if (RewardsRepository.hasReceivedWeeklyReward(userName)) {
                MessageService.sendMessage("You have already claimed your weekly reward.");
                return;
            }
            
            int currentBalance = UserRepository.getCurrentUserBalance(userName, true);
            int weeklyRewardPrize = 5 * dailyRewardPrize;
            int newBalance = currentBalance + weeklyRewardPrize;
    
            UserRepository.updateUserBalance(userName, newBalance);
            RewardsRepository.updateWeeklyReward(userName);
    
            MessageService.sendMessage(userName + " has claimed the weekly reward. Current balance: " + newBalance);
            RewardsHistoryRepository.addRewardHistory(userName, "Weekly", weeklyRewardPrize);
        } catch (Exception e) {
            System.out.println(e);
              MessageService.sendMessage("An error occurred while claiming your weekly reward. Please try again later.");
        }
    }

    public static void handleHourlyCommand(CommandContext context) {
        String userName = context.getUserName();
        LocalTime now = LocalTime.now();
        int currentMinute = now.getMinute();
        if (currentMinute != 0 && currentMinute != 1) {
            MessageService.sendMessage("Command can only be used at the start of an hour.");
            return;
        }

        if (RewardsRepository.hasReceivedHourlyReward(userName)) {
            MessageService.sendMessage(userName + ", you have already claimed your reward for this hour.");
            return;
        }

        RewardsRepository.updateHourlyReward(userName);

        try {
            int currentBalance = UserRepository.getCurrentUserBalance(userName, true);
            int newBalance = currentBalance + hourlyRewardPrize;

            UserRepository.updateUserBalance(userName, newBalance);

            MessageService.sendMessage(userName + " has claimed the hourly reward " + hourlyRewardPrize + " coins. Current balance: " + newBalance);
            Logger.logInfo("User " + userName + " claimed hourly reward. New balance: " + newBalance,"CommandService.handleHourlyCommand()");
            RewardsHistoryRepository.addRewardHistory(userName, "Hourly", hourlyRewardPrize);
        } catch (Exception e) {
            Logger.logError("Error processing hourly reward for user " + userName, "CommandService.handleHourlyCommand()", e);
            MessageService.sendMessage("An error occurred while claiming your hourly reward. Please try again later.");
        }
    }

    public static void handleCoinflipCommand(CommandContext context) {
        String command = context.getFirstArgument();
        String username = context.getUserName();
    
        if (command.equalsIgnoreCase("bet")) {
            if (coinFlipCurrentPlayer.isEmpty()) {
                try {
                    coinFlipAmount = Integer.parseInt(context.getSecondArgument());
                    if (coinFlipAmount <= 0) {
                        coinFlipAmount = 0;
                        MessageService.sendMessage("Invalid bet amount. Please provide a valid number.");
                        return;
                    }
    
                    int userBalance = UserRepository.getCurrentUserBalance(username, false);
                    if (userBalance < coinFlipAmount) {
                        MessageService.sendMessage("Insufficient balance. You have " + userBalance + " coins, but your bet is " + coinFlipAmount);
                        return;
                    }
    
                    coinFlipCurrentPlayer = username;
                    MessageService.sendMessage(username + " has started a coinflip with a bet of " + coinFlipAmount + ". Use /bot coinflip accept to join.");
                } catch (NumberFormatException e) {
                    MessageService.sendMessage("Invalid bet amount. Please provide a valid number.");
                }
            } else {
                MessageService.sendMessage("A coinflip is already in progress. Please wait for it to finish.");
            }
        } else if (command.equalsIgnoreCase("accept")) {
            if (!coinFlipCurrentPlayer.isEmpty()) {
                int result = new Random().nextInt(2); // 50% chance
                int userBalance = UserRepository.getCurrentUserBalance(username, false);
    
                if (userBalance < coinFlipAmount) {
                    MessageService.sendMessage("Insufficient balance to accept the coinflip. You need at least " + coinFlipAmount + "coins.");
                    return;
                }
    
                if (result == 1) {
                    MessageService.sendMessage(username + " won " + coinFlipAmount + " coins!");
                    userBalance += coinFlipAmount;
                    UserRepository.updateUserBalance(coinFlipCurrentPlayer, UserRepository.getCurrentUserBalance(coinFlipCurrentPlayer, false) - coinFlipAmount);
                } else {
                    MessageService.sendMessage(coinFlipCurrentPlayer + " won " + coinFlipAmount + " coins!");
                    userBalance -= coinFlipAmount;
                    UserRepository.updateUserBalance(coinFlipCurrentPlayer, UserRepository.getCurrentUserBalance(coinFlipCurrentPlayer, false) + coinFlipAmount);
                }
    
                UserRepository.updateUserBalance(username, userBalance);
    
                // Reset game state
                coinFlipCurrentPlayer = "";
                coinFlipAmount = 0;
            } else {
                MessageService.sendMessage("No active coinflip game to join. Use /bot coinflip bet <amount> to start one.");
            }
        } else if (command.equalsIgnoreCase("cancel")) {
            if (username.equals(coinFlipCurrentPlayer)) {
                UserRepository.updateUserBalance(coinFlipCurrentPlayer, UserRepository.getCurrentUserBalance(coinFlipCurrentPlayer, false) + coinFlipAmount);
                coinFlipAmount = 0;
                coinFlipCurrentPlayer = "";
                MessageService.sendMessage(username + " canceled the coinflip game.");
            } else {
                MessageService.sendMessage("Only the player who started the coinflip can cancel it.");
            }
        } else if (command.equalsIgnoreCase("")) {
            if (!coinFlipCurrentPlayer.isEmpty()) {
                MessageService.sendMessage("Active coinflip: " + coinFlipCurrentPlayer + " has bet " + coinFlipAmount + " coins.");
            } else {
                MessageService.sendMessage("No active coinflip game at the moment.");
            }
        } else {
            MessageService.sendMessage("Invalid command. Use /bot coinflip bet <amount>, /bot coinflip accept, or /bot coinflip cancel.");
        }
    }

    public static void handleBindCommand(CommandContext context) {
        String command = context.getCommand();
        String firstArg = context.getFirstArgument();
        String arguments = context.getArgumentsJoined();
        String allArguments = context.getAllArgumentsJoined();
        String userName = context.getUserName();
        if (command.equalsIgnoreCase("bind")) {
            if (firstArg == null) {
                MessageService.sendMessage(userName + ", you must specify a bind ID (0-9) or 'list'.");
                return;
            }

            if (firstArg.equalsIgnoreCase("list")) {
                MessageService.sendMessage(BindService.listUserBinds(userName));
                return;
            }

            int bindId;
            try {
                bindId = Integer.parseInt(firstArg);
            } catch (NumberFormatException e) {
                MessageService.sendMessage(userName + ", invalid bind ID. Must be a number between 0 and 9.");
                return;
            }

            if (bindId < 0 || bindId > 9) {
                MessageService.sendMessage(userName + ", bind ID must be between 0 and 9.");
                return;
            }

            if (arguments.isEmpty()) {
                MessageService.sendMessage(userName + ", you must provide a command to bind.");
                return;
            }

            BindService.saveUserCommand(userName, bindId, arguments);
            return;
        }

        int bindId;
        try {
            bindId = Integer.parseInt(command);
        } catch (NumberFormatException e) {
            return;
        }

        if (bindId < 0 || bindId > 9) {
            return;
        }

        String bindedCommand = BindService.getUserCommand(userName, bindId);
        if (bindedCommand == null) {
            MessageService.sendMessage(userName + ", no command bound to ID " + bindId + ".");
            return;
        }
        
        CommandContext bindedContext = CommandController.parseCommand(bindedCommand + " " + allArguments, userName);
        CommandController.processCommand(bindedContext);
    }


    public static void handleAdminCommand(CommandContext context) {
        String userName = context.getUserName();
        String adminName = ConfigReader.getAdminName();
        String command = context.getFirstArgument();

        if (!userName.equals(adminName)) {
            MessageService.sendMessage(userName + ", you have no rights to use admin commands!");
            return;
        }

        if (command.equals("addmoney")) {
            List<String> arguments = context.getArguments();
            if (arguments.size() < 3) {
                MessageService.sendMessage("Usage: addMoney <amount> <user name>");
                return;
            }

            String amount = arguments.get(1);
            String receiverFullName = String.join(" ", arguments.subList(2, arguments.size()));

            if (receiverFullName.startsWith("@")) {
                receiverFullName = receiverFullName.substring(1);
            }

            if (!UserRepository.validateTransferParams(amount, receiverFullName)) return;

            int parsedAmount = UserRepository.parseTransferAmount(amount);
            if (parsedAmount == -1) return;

            UserService.updateAndRetriveUserBalance(receiverFullName, parsedAmount);

            MessageService.sendMessage(receiverFullName + " balance successfully increased");

        } else if (command.equals("execsql")) {

            List<String> arguments = context.getArguments();
            if (arguments.size() < 2) {
                MessageService.sendMessage("Usage: execsql <SQL statement>");
                return;
            }

            String sql = String.join(" ", arguments.subList(1, arguments.size()));

            try (Connection conn = DatabaseConnectionManager.getConnection();
                Statement stmt = conn.createStatement()) {

                boolean hasResultSet = stmt.execute(sql);

                if (hasResultSet) {
                    ResultSet rs = stmt.getResultSet();
                    StringBuilder sb = new StringBuilder("Result:\n");

                    ResultSetMetaData meta = rs.getMetaData();
                    int columnCount = meta.getColumnCount();

                    while (rs.next()) {
                        for (int i = 1; i <= columnCount; i++) {
                            sb.append(meta.getColumnName(i)).append(": ").append(rs.getString(i)).append(" | ");
                        }
                        sb.append("\n");
                    }

                    MessageService.sendMessage(sb.toString());

                } else {
                    int updateCount = stmt.getUpdateCount();
                    MessageService.sendMessage("SQL executed. Rows affected: " + updateCount);
                }

            } catch (SQLException e) {
                MessageService.sendMessage("SQL Error: " + e.getMessage());
            }

        } else {
            MessageService.sendMessage("Invalid admin command!");
        }
    }
}
