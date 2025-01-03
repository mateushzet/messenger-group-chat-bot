package service;

import repository.UserRepository;
import repository.DailyRewardRepository;

import java.util.List;
import java.util.Random;

import utils.ConfigReader;
import utils.LoggerUtil;

import app.App;
import model.CommandContext;

public class CommandService {
    
    private static int dailyRewardPrize = ConfigReader.getDailyRewardPrize();
    private static int coinFlipAmount = 0;
    private static String coinFlipCurrentPlayer = "";


    public static void handleMoneyCommand(CommandContext context) {
        String userName = context.getUserName();
        int balance = UserRepository.getUserBalance(userName, true);
        MessageService.sendMessage("%s, current balance: %d", userName ,balance);
        LoggerUtil.logInfo("%s, current balance: %d",userName, balance);
    }

    public static void handleTimeCommand(CommandContext context) {
        MessageService.sendMessage("Current time: " + java.time.LocalTime.now());
    }

    public static void handleKillCommand(CommandContext context) {
        MessageService.sendMessage("Shutting down the bot");
        LoggerUtil.logInfo("Shutting down the bot at the request of %s", context.getUserName());
        System.exit(0);
    }

    public static void handleStopCommand(CommandContext context) {
        MessageService.sendMessage("Status: stopped");
        App.running = 0;
    }

    public static void handleStartCommand(CommandContext context) {
        MessageService.sendMessage("Status: running");
        App.running = 1;
    }

    public static void handleStatusCommand(CommandContext context) {
        String status = (App.running == 1) ? "running" : "stopped";
        MessageService.sendMessage("Status: %s", status);
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
        String receiverFullName = String.join(" ", receiverNameParts);
        String senderName = context.getUserName();

        boolean correctTransfer = UserRepository.handleTransfer(senderName, amount, receiverNameParts.toArray(new String[0]));

        if (correctTransfer) {
            MessageService.sendMessage("Transferred %s coins to %s", amount, receiverFullName);
        } else {
            MessageService.sendMessage("Transfer failed");
            LoggerUtil.logWarning("Transfer failed sender: %s, amount: %s, receiver: %s", senderName, amount, receiverFullName);
        }
    }

    public static void handleRankCommand(CommandContext context) {
        String rankingString = UserRepository.getRanking();
        MessageService.sendMessage(rankingString);
    }

    public static void handleHelpCommand(CommandContext context) {

        String[] helpMessages = {
            "Command list:",
            "> money - Shows your current balance.",
            "> roulette - /bot roulette <bet> <number or color (red, black, green)>",
            "> say - /bot say <text>",
            "> answer - /bot answer <number>",
            "> transfer - /bot transfer <amount> <first name> <last name>",
            "> rank - Shows the balance ranking",
            "> stop - Stops the bot",
            "> start - Starts the bot",
            "> kill - Completely shuts down the bot",
            "> help - Displays this list of available commands",
            "> slots - /bot slots <bet> - Play the slot machine.",
            "> slots jackpot - Check the current jackpot value.",
            "> buy slots - Buy access to the slot machine."
        };

        String helpMessageString = String.join("\n", helpMessages);
        MessageService.sendMessage(helpMessageString);
    }

    public static void handleDailyCommand(CommandContext context) {
        String userName = context.getUserName();
        
        try {
            if (DailyRewardRepository.hasReceivedDailyReward(userName)) {
                MessageService.sendMessage("You have already claimed your daily reward.");
                LoggerUtil.logInfo("User %s tried to claim daily reward but already received it.", userName);
                return;
            }
            
            int currentBalance = UserRepository.getUserBalance(userName, true);
            int newBalance = currentBalance + dailyRewardPrize;
    
            UserRepository.updateUserBalance(userName, newBalance);
            DailyRewardRepository.updateDailyReward(userName);
    
            MessageService.sendMessage("%s has claimed the daily reward. Current balance: %d", userName, newBalance);
            LoggerUtil.logInfo("User %s claimed daily reward. New balance: %d", userName, newBalance);
        } catch (Exception e) {
            LoggerUtil.logError("Error processing daily reward for user %s: %s", e, userName);
            MessageService.sendMessage("An error occurred while claiming your daily reward. Please try again later.");
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
    
                    int userBalance = UserRepository.getUserBalance(username, false);
                    if (userBalance < coinFlipAmount) {
                        MessageService.sendMessage("Insufficient balance. You have %d coins, but your bet is %d.", userBalance, coinFlipAmount);
                        return;
                    }
    
                    coinFlipCurrentPlayer = username;
                    MessageService.sendMessage("%s has started a coinflip with a bet of %d. Use /bot coinflip accept to join.", username, coinFlipAmount);
                } catch (NumberFormatException e) {
                    MessageService.sendMessage("Invalid bet amount. Please provide a valid number.");
                }
            } else {
                MessageService.sendMessage("A coinflip is already in progress. Please wait for it to finish.");
            }
        } else if (command.equalsIgnoreCase("accept")) {
            if (!coinFlipCurrentPlayer.isEmpty()) {
                int result = new Random().nextInt(2); // 50% chance
                int userBalance = UserRepository.getUserBalance(username, false);
    
                if (userBalance < coinFlipAmount) {
                    MessageService.sendMessage("Insufficient balance to accept the coinflip. You need at least %d coins.", coinFlipAmount);
                    return;
                }
    
                if (result == 1) {
                    MessageService.sendMessage("%s won %d coins!", username, coinFlipAmount);
                    userBalance += coinFlipAmount;
                    UserRepository.updateUserBalance(coinFlipCurrentPlayer, UserRepository.getUserBalance(coinFlipCurrentPlayer, false) - coinFlipAmount);
                } else {
                    MessageService.sendMessage("%s won %d coins!", coinFlipCurrentPlayer, coinFlipAmount);
                    userBalance -= coinFlipAmount;
                    UserRepository.updateUserBalance(coinFlipCurrentPlayer, UserRepository.getUserBalance(coinFlipCurrentPlayer, false) + coinFlipAmount);
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
                UserRepository.updateUserBalance(coinFlipCurrentPlayer, UserRepository.getUserBalance(coinFlipCurrentPlayer, false) + coinFlipAmount);
                coinFlipAmount = 0;
                coinFlipCurrentPlayer = "";
                MessageService.sendMessage("%s canceled the coinflip game.", username);
            } else {
                MessageService.sendMessage("Only the player who started the coinflip can cancel it.");
            }
        } else if (command.equalsIgnoreCase("")) {
            if (!coinFlipCurrentPlayer.isEmpty()) {
                MessageService.sendMessage("Active coinflip: %s has bet %d coins.", coinFlipCurrentPlayer, coinFlipAmount);
            } else {
                MessageService.sendMessage("No active coinflip game at the moment.");
            }
        } else {
            MessageService.sendMessage("Invalid command. Use /bot coinflip bet <amount>, /bot coinflip accept, or /bot coinflip cancel.");
        }
    }

}
