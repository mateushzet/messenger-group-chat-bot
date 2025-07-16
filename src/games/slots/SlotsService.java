package games.slots;

import java.util.Random;
import model.CommandContext;
import utils.Logger;
import repository.UserRepository;
import service.MessageService;
import service.UserService;
import repository.GameHistoryRepository;
import repository.UserAvatarRepository;

public class SlotsService {

    public static void handleSlotsCommand(CommandContext context) {
        String playerName = context.getUserName();
        String firstArgument = context.getFirstArgument();
        String betAmountMulti = context.getSecondArgument();

        if(firstArgument.equals("multi") || firstArgument.equals("m")){
            context.setFirstArgument(betAmountMulti);
            firstArgument = context.getFirstArgument();
            int betAmountInt = UserService.validateAndParseBetAmount(playerName, betAmountMulti);

            if(betAmountInt == -1) return;

            int currentBalance = UserRepository.getCurrentUserBalance(playerName, true);
            int totalBalance = UserRepository.getTotalUserBalance(playerName);
            int minimalBet = (int) (totalBalance * 0.005);
            if(minimalBet < 10) minimalBet = 10;

            if (betAmountInt < minimalBet) {
                MessageService.sendMessage("Your bet amount must be at least " + minimalBet + " coins (0.5%% of total balance or 10 coins). Your current balance is: " + currentBalance);
                return;
            }

            if (betAmountInt * 5 > currentBalance) {
                MessageService.sendMessage(playerName + " you don't have enough balance to play. Current balance: " + currentBalance + ", required balance: " + (betAmountInt * 5));
                return;
            }

            playSlotsMulti(playerName, betAmountInt, currentBalance, context);

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

        int betAmount = UserService.validateAndParseBetAmount(playerName, firstArgument);
        int currentBalance = UserRepository.getCurrentUserBalance(playerName, true);

        if (validateSlotsGame(playerName, betAmount, currentBalance)) {
            playSlots(playerName, betAmount, currentBalance, context);
        }
    }

    private static boolean validateSlotsGame(String playerName, int betAmount, int currentBalance) {      
        int minimalBet = (int) (UserRepository.getTotalUserBalance(playerName) * 0.005);
        if(minimalBet < 10) minimalBet = 10;

        try {
            if (betAmount == -1) {
                MessageService.sendMessage("You can't afford it, your balance is: " + currentBalance);
                return false;
            }

            if (betAmount < minimalBet) {
                MessageService.sendMessage("Your bet amount must be at least " + minimalBet + " coins (0.5%% of total balance or 10 coins). Your current balance is: " + currentBalance);
                return false;
            }

        } catch (NumberFormatException e) {
            MessageService.sendMessage("Invalid bet amount. Please enter a valid number.");
            Logger.logError("Failed to parse bet amount: " + betAmount, "SlotsService.validateSlotsGame()", e);
            return false;
        }

        return true;
    }

    private static void playSlots(String playerName, int betAmount, int currentBalance, CommandContext context) {
        int newBalance = currentBalance - betAmount;
        UserRepository.updateUserBalance(playerName, newBalance);
        Logger.logInfo(playerName + " placed a bet of " + betAmount + " coins. New balance: " + newBalance, "SlotsService.playSlots()");

        int[] result = spinSlotsWithWildcard();

        double multiplier = getMultiplier(result);

        int winnings = 0;

        if (isJackpot(result)){
            double jackpotAmount = getJackpotProportionalAmount(betAmount);
            winnings += (int) (betAmount * multiplier + jackpotAmount);
            UserAvatarRepository.assignAvatarToUser(playerName, "jackpot");
        } else {
            winnings += (int) (betAmount * multiplier);
        }

        newBalance += winnings;
        if(winnings == 0) winnings = betAmount * -1;

        UserRepository.updateUserBalance(playerName, newBalance);

        if (winnings > 0) {
            //MessageService.sendMessage(playerName + " won " + winnings + " coins! New balance: " + newBalance);
            Logger.logInfo(playerName + " won " + winnings + " coins. New balance: " + newBalance, "SlotsService.playSlots()");
            GameHistoryRepository.addGameHistory(playerName, "Slots", context.getFullCommand(), betAmount, winnings, "Result: " + result[0] + "-" + result[1] + "-" + result[2]);
        } else {
            JackpotRepository.addToJackpotPool(betAmount);
            //MessageService.sendMessage(playerName + " lost the bet. New balance: " + newBalance);
            Logger.logInfo(playerName + " lost the bet. New balance: " + newBalance, "SlotsService.playSlots()");
            GameHistoryRepository.addGameHistory(playerName, "Slots", context.getFullCommand(), betAmount, winnings, "Result: " + result[0] + "-" + result[1] + "-" + result[2]);
        }

        int jackpotAmount = JackpotRepository.getJackpot();

        SlotsImageGenerator.generateSlotsResultImage(result, playerName, winnings, newBalance, betAmount, jackpotAmount);
        MessageService.sendMessageFromClipboard(false);
    }

    private static void playSlotsMulti(String playerName, int betAmount, int currentBalance, CommandContext context) {

        int totalBetAmount = 5 * betAmount; 

        int[][] result = new int[5][3];;
        double multiplier[] = new double[5];
        int winnings = 0;
        for (int i = 0; i < 5; i++) {
            result[i] = spinSlotsWithWildcard();
            multiplier[i] = getMultiplier(result[i]);

            if (isJackpot(result[i])){
                double jackpotAmount = getJackpotProportionalAmount(betAmount);
                winnings += (int) (betAmount * multiplier[i] + jackpotAmount);
                UserAvatarRepository.assignAvatarToUser(playerName, "jackpot");
            } else {
                winnings += (int) (betAmount * multiplier[i]);
            }
        }

        int newBalance = currentBalance + winnings - totalBetAmount;

        UserRepository.updateUserBalance(playerName, newBalance);
        GameHistoryRepository.addGameHistory(playerName, "Slots", context.getFullCommand(), totalBetAmount, winnings - totalBetAmount, "Result: " + result[0] + "-" + result[1] + "-" + result[2]);

        if (winnings - totalBetAmount < 0) {
            JackpotRepository.addToJackpotPool(-1 * (winnings - totalBetAmount));
        }

        int jackpotAmount = JackpotRepository.getJackpot();

        SlotsImageGenerator.generateSlotsResultImageMulti(result, playerName, winnings - totalBetAmount, newBalance, betAmount * 5, jackpotAmount);
        MessageService.sendMessageFromClipboard(false);
    }

    private static double getJackpotProportionalAmount(int betAmount) { 
        double jackpotAmount = JackpotRepository.getJackpot();
        
        double maxJackpotAmount = betAmount * 100;
    
        double proportionalJackpotAmount = Math.min(jackpotAmount, maxJackpotAmount);
    
        jackpotAmount = Math.max((jackpotAmount - proportionalJackpotAmount), 0);

        JackpotRepository.setJackpot(jackpotAmount);
    
        return proportionalJackpotAmount;
    }

    private static double getMultiplier(int[] result) {

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
        MessageService.sendMessage("Current Jackpot is: " + currentJackpot);
        Logger.logInfo("Current Jackpot is: " + currentJackpot, "SlotsService.handleSlotsJackpotCommand()");
    }

}