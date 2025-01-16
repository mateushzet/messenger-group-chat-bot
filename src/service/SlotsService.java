package service;

import java.util.Random;

import model.CommandContext;
import utils.ConfigReader;
import utils.Logger;
import utils.SlotsImageGenerator;
import repository.SlotsRepository;
import repository.UserRepository;
import repository.GameHistoryRepository;
import repository.JackpotRepository;

public class SlotsService {

    private static final int slotsAccessCost = ConfigReader.getSlotsAccessCost();
    //private static final String[] symbols = {
    //    ConfigReader.getCherryEmojiUrl(),
    //    ConfigReader.getLemonEmojiUrl(),
    //    ConfigReader.getOrangeEmojiUrl(),
    //    ConfigReader.getLobsterEmojiUrl(),
    //    ConfigReader.getWatermelonEmojiUrl(),
    //    ConfigReader.getAppleEmojiUrl(),
    //    ConfigReader.getSlotMachineEmojiUrl()
    //};

    public static void handleSlotsCommand(CommandContext context) {
        String playerName = context.getUserName();
        String firstArgument = context.getFirstArgument();
        String betAmountMulti = context.getSecondArgument();

        if(firstArgument.equals("multi")){
            context.setFirstArgument(betAmountMulti);
            for (int i = 0; i < 5; i++) {
                try {
                    Thread.sleep(50);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                handleSlotsCommand(context);
            }
            return;
        }

        if(firstArgument.equals("jackpot")){
            handleSlotsJackpotCommand();
            return;
        }

        if(firstArgument.isEmpty()){
            MessageService.sendMessage("Avaiable slots commands: buy slots, slots multi <betAmount>, slots jackpot");
            return;
        }

        String betAmount = firstArgument;
        int currentBalance = UserRepository.getUserBalance(playerName, false);

        if (validateSlotsGame(playerName, betAmount, currentBalance)) {
            int betAmountInt = Integer.parseInt(firstArgument);
            playSlots(playerName, betAmountInt, currentBalance, context);
        }
    }

    private static boolean validateSlotsGame(String playerName, String betAmount, int currentBalance) {
        if (!SlotsRepository.hasSlotsAccess(playerName)) {
            MessageService.sendMessage("You need to purchase access to play slots. Cost: %d coins. /bot buy slots", slotsAccessCost);
            Logger.logInfo("%s attempted to play slots without access.", "SlotsService.validateSlotsGame()", playerName);
            return false;
        }
        
        int minimalBet = (int) (UserRepository.getTotalUserBalance(playerName) * 0.005);
        if(minimalBet < 10) minimalBet = 10;

        try {
            int betAmountInt = Integer.parseInt(betAmount);
            if (currentBalance < betAmountInt) {
                MessageService.sendMessage("You can't afford it, your balance is: %d", currentBalance);
                Logger.logInfo("Player %s can't afford the bet. Current balance: %d", "SlotsService.validateSlotsGame()", playerName, currentBalance);
                return false;
            }

            if (betAmountInt < minimalBet) {
                MessageService.sendMessage("Your bet amount must be at least %d coins (0.5%% of total balance or 10 coins). Your current balance is: %d", minimalBet, currentBalance);
                Logger.logInfo("Player %s attempted to place a bet of %d coins, which is less than the minimum required bet of %d coins. Current balance: %d", "SlotsService.validateSlotsGame()", playerName, betAmountInt, minimalBet, currentBalance);
                return false;
            }

        } catch (NumberFormatException e) {
            MessageService.sendMessage("Invalid bet amount. Please enter a valid number.");
            Logger.logError("Failed to parse bet amount: %s", "SlotsService.validateSlotsGame()", e, betAmount);
            return false;
        }

        return true;
    }

    public static void handleBuySlotsCommand(CommandContext context) {
        String userName = context.getUserName();
        if (SlotsRepository.hasSlotsAccess(userName)) {
            MessageService.sendMessage("%s, you already have access to the slots.", userName);
        } else {
            buySlotsAccess(userName);
        }
    }

    private static void buySlotsAccess(String userName) {
        int balance = UserRepository.getUserBalance(userName, true);
        Logger.logInfo("%s is attempting to buy slots.", "SlotsService.buySlotsAccess()", userName);

        if (balance < slotsAccessCost) {
            MessageService.sendMessage("%s, you don't have enough coins to buy access to slots. You need %d coins.", userName, slotsAccessCost);
            Logger.logInfo("%s doesn't have enough coins to buy slots. Current balance: %d", "SlotsService.buySlotsAccess()", userName, balance);
            return;
        }

        int newBalance = balance - slotsAccessCost;
        UserRepository.updateUserBalance(userName, newBalance);

        if (SlotsRepository.giveSlotsAccess(userName)) {
            MessageService.sendMessage("%s has successfully bought access to slots for %d coins. New balance: %d", userName, slotsAccessCost, newBalance);
            Logger.logInfo("%s purchased slots access. New balance: %d", "SlotsService.buySlotsAccess()", userName, newBalance);
        }
    }

    private static void playSlots(String playerName, int betAmount, int currentBalance, CommandContext context) {
        int newBalance = currentBalance - betAmount;
        UserRepository.updateUserBalance(playerName, newBalance);
        Logger.logInfo("%s placed a bet of %d coins. New balance: %d", "SlotsService.playSlots()", playerName, betAmount, newBalance);

        int[] result = spinSlotsWithWildcard();
        //MessageService.clickEmoji(result[0], result[0] == symbols[3] ? "lobster" : "fruit");
        //MessageService.clickEmoji(result[1], result[1] == symbols[3] ? "lobster" : "fruit");
        //MessageService.clickEmoji(result[2], result[2] == symbols[3] ? "lobster" : "fruit");

        double multiplier = getMultiplier(result);

        int winnings;
        if (!isJackpot(result)) winnings = (int) (betAmount * multiplier);
        else winnings = (int) ((betAmount * 5) + multiplier);

        newBalance += winnings;
        if(winnings == 0) winnings = betAmount * -1;

        UserRepository.updateUserBalance(playerName, newBalance);

        if (winnings > 0) {
            //MessageService.sendMessage(playerName + " won " + winnings + " coins! New balance: " + newBalance);
            Logger.logInfo("%s won %d coins. New balance: %d", "SlotsService.playSlots()", playerName, winnings, newBalance);
            GameHistoryRepository.addGameHistory(playerName, "Slots", context.getFullCommand(), betAmount, winnings, "Result: " + result[0] + "-" + result[1] + "-" + result[2]);
        } else {
            JackpotRepository.addToJackpotPool(betAmount);
            //MessageService.sendMessage(playerName + " lost the bet. New balance: " + newBalance);
            Logger.logInfo("%s lost the bet. New balance: %d", "SlotsService.playSlots()", playerName, newBalance);
            GameHistoryRepository.addGameHistory(playerName, "Slots", context.getFullCommand(), betAmount, winnings, "Result: " + result[0] + "-" + result[1] + "-" + result[2]);
        }

        int jackpotAmount = JackpotRepository.getJackpot();

        SlotsImageGenerator.generateSlotsResultImage(result, playerName, winnings, newBalance, betAmount, jackpotAmount);
        MessageService.sendMessageFromClipboard(false);
    }

    private static double getMultiplier(int[] result) {
        if (isJackpot(result)) {
            double jackpotMultiplier = JackpotRepository.getJackpot();
            JackpotRepository.resetJackpot();
            return jackpotMultiplier;
        }

        if (result[0] == (result[1]) && result[1]==(result[2])) {
            return 5;
        }

        if (result[0] == (result[1]) && result[2] == (3)
            || result[1] == (result[2]) && result[0] == (3)
            || result[0] == (result[2]) && result[1] == (3)) {
            return 2;
        }

        if((result[0] == (3) && result[1] == (3)) 
            || (result[1] == (3) && result[2] == (3))    
            || (result[0] == (3) && result[2] == (3))) {
            return 2;
        }

        if (result[0] == (result[1]) || result[1] == (result[2]) || result[0] == (result[2])) {
            return 1.5;
        } else if ((result[0] == (3) || result[1] == (3) || result[2] == (3))) {
            return 1.1;
        }

        return 0;
    }

    private static boolean isJackpot(int[] result) {
        return result[0] == (6) && result[1] == (6) && result[2] == (6);
    }

    private static int[] spinSlotsWithWildcard() {
        Random rand = new Random();
        int[] result = new int[3];

        for (int i = 0; i < 3; i++) {
            result[i] = rand.nextInt(7);
        }
        return result;
    }

    public static void handleSlotsJackpotCommand() {
        int currentJackpot = JackpotRepository.getJackpot();
        MessageService.sendMessage("Current Jackpot is: %d", currentJackpot);
        Logger.logInfo("Current Jackpot is: %d", "SlotsService.handleSlotsJackpotCommand()", currentJackpot);
    }

}