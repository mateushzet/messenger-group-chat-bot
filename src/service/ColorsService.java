package service;

import java.util.LinkedList;
import java.util.Queue;
import java.util.Random;

import model.CommandContext;
import repository.ColorsRepository;
import repository.UserRepository;
import utils.ColorsImageGenerator;
import utils.ConfigReader;
import utils.Logger;

public class ColorsService {

    private static final int colorsAccessCost = ConfigReader.getColorsAccessCost();
    private static final Queue<Integer> colorsHistory = new LinkedList<>();

    public static void handleColorsCommand(CommandContext context) {
        String playerName = context.getUserName();
        String betColor = context.getSecondArgument();
        int currentBalance = UserRepository.getUserBalance(playerName, false);
    
        if (!ColorsRepository.hasColorsAccess(playerName)) {
            MessageService.sendMessage("You need to purchase access to play colors. Cost: %d coins. /bot buy colors", colorsAccessCost);
            return;
        }
    
        Random random = new Random();
        int result = random.nextInt(53) + 1;
        int resultColorNumber = getResult(result);
        int winnings = 0;
        int[] betResult;
        int balanceChange;
        int betAmount;
        if (isMultiColorBet(betColor)) {
            betResult = handleMultiColorBet(context, currentBalance, resultColorNumber);
        } else {
            betResult = handleSingleColorBet(context, currentBalance, resultColorNumber, betColor);
        }

        if(betResult == null) return;

        winnings = betResult[0];
        balanceChange = betResult[1];
        betAmount = betResult[2];
    
            int updatedBalance = currentBalance + balanceChange;
            UserRepository.updateUserBalance(playerName, updatedBalance);
    
            storeColorsColor(resultColorNumber);

            if (winnings <= 0) winnings = balanceChange;
            ColorsImageGenerator.generateColorsImage(winnings, playerName, updatedBalance, result, betAmount, colorsHistory);
            MessageService.sendMessageFromClipboard();
    }
    
    private static int[] handleMultiColorBet(CommandContext context, int currentBalance, int resultColorNumber) {
        String blackBet = context.getFirstArgument();
        String redBet = context.getSecondArgument();
        String blueBet = context.getThirdArgument();
        String goldBet = context.getFourthArgument();

        System.out.println(blackBet+"-"+redBet+"-"+blueBet+"-"+goldBet+"-" );
    
        int blackBetParsed = parseBetAmount(blackBet);
        int redBetParsed = parseBetAmount(redBet);
        int blueBetParsed = parseBetAmount(blueBet);
        int goldBetParsed = parseBetAmount(goldBet);

        System.out.println(blackBet+"-"+redBet+"-"+blueBet+"-"+goldBet+"-" );
    
        if (blackBetParsed == Integer.MIN_VALUE || redBetParsed == Integer.MIN_VALUE || blueBetParsed == Integer.MIN_VALUE || goldBetParsed == Integer.MIN_VALUE) {
            MessageService.sendMessage("Invalid bet amount. Please enter valid numbers. /bot colors amountBlack amountRed amountBlue amountGold");
            return null;
        }
    
        int totalBetAmount = blackBetParsed + redBetParsed + blueBetParsed + goldBetParsed;
        if (totalBetAmount == 0) {
            MessageService.sendMessage("Bet amounts must be greater than 0");
            return null;
        }
    
        if (currentBalance < totalBetAmount) {
            MessageService.sendMessage("You can't afford the bet, current balance: %d", currentBalance);
            return null;
        }
    
        int winnings = calculateMultiColorWinnings(resultColorNumber, blackBetParsed, redBetParsed, blueBetParsed, goldBetParsed);
        
        int balanceChange = winnings - totalBetAmount;
    
        return new int[]{winnings, balanceChange, totalBetAmount};
    }
    
    private static int[] handleSingleColorBet(CommandContext context, int currentBalance, int resultColorNumber, String betColor) {
        String betAmount = context.getFirstArgument();
    
        int betAmountParsed = parseBetAmount(betAmount);
        if (betAmountParsed == Integer.MIN_VALUE || betAmountParsed <= 0) {
            MessageService.sendMessage("Invalid bet amount. Please enter a valid number greater than 0. /bot colors amountColor");
            return null; 
        }
    
        if (currentBalance < betAmountParsed) {
            MessageService.sendMessage("You can't afford the bet, current balance: %d", currentBalance);
            return null;
        }
    
        int winnings = calculateSingleColorWinnings(betColor, resultColorNumber, betAmountParsed);
    
        int balanceChange = winnings - betAmountParsed;
    
        return new int[]{winnings, balanceChange, betAmountParsed};
    }
    
    private static int parseBetAmount(String betAmount) {
        try {
            int parsedAmount = Integer.parseInt(betAmount);
            if (parsedAmount < 0) {
                throw new NumberFormatException("Bet amount must be greater than 0");
            }
            return parsedAmount;
        } catch (NumberFormatException e) {
            return Integer.MIN_VALUE;
        }
    }

    private static boolean isMultiColorBet(String betColor) {
        return !betColor.equals("black") && !betColor.equals("red") && !betColor.equals("gold") && !betColor.equals("blue");
    }

    private static int calculateMultiColorWinnings(int resultColorNumber, int blackBet, int redBet, int blueBet, int goldBet) {
        switch (resultColorNumber) {
            case 0: return 2 * blackBet;
            case 1: return 3 * redBet;
            case 2: return 5 * blueBet;
            case 3: return 50 * goldBet;
            default: return 0;
        }
    }

    private static int calculateSingleColorWinnings(String betColor, int resultColorNumber, int betAmountParsed) {
        switch (betColor) {
            case "black": return resultColorNumber == 0 ? 2 * betAmountParsed : 0;
            case "red": return resultColorNumber == 1 ? 3 * betAmountParsed : 0;
            case "blue": return resultColorNumber == 2 ? 5 * betAmountParsed : 0;
            case "gold": return resultColorNumber == 3 ? 50 * betAmountParsed : 0;
            default: return 0;
        }
    }

    public static int getResult(int shift) {
        int[] colorOrder = {3, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 3, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2};
        colorOrder = ColorsImageGenerator.rotateArray(colorOrder, shift);
        System.out.println("Colors result: " + colorOrder[40]);
        return colorOrder[40]; // wining position
    }

        public static void handleBuyColorsCommand(CommandContext context) {
        String userName = context.getUserName();
        if (ColorsRepository.hasColorsAccess(userName)) {
            MessageService.sendMessage("%s, you already have access to the colors.", userName);
        } else {
            buyColorsAccess(userName);
        }
    }

    private static void buyColorsAccess(String userName) {
        int balance = UserRepository.getUserBalance(userName, true);
        Logger.logToConsole("INFO", userName + " is attempting to buy colors.", "ColorsService.buyColorsAccess()");

        if (balance < colorsAccessCost) {
            MessageService.sendMessage("%s, you don't have enough coins to buy access to colors. You need %d coins.", userName, colorsAccessCost);
            Logger.logToConsole("INFO", userName + " doesn't have enough coins to buy colors. Current balance: " + balance,  "ColorsService.buyColorsAccess()");
            return;
        }

        int newBalance = balance - colorsAccessCost;
        UserRepository.updateUserBalance(userName, newBalance);

        if (ColorsRepository.addUserToColorsFile(userName)) {
            MessageService.sendMessage("%s has successfully bought access to colors for %d coins. New balance: %d", userName, colorsAccessCost, newBalance);
            Logger.logInfo("%s purchased colors access. New balance: %d", "ColorsService.buyColorsAccess()", userName, newBalance);
        }
    }

    private static void storeColorsColor(int colorNumber) {
        if (colorsHistory.size() >= 17) {
            colorsHistory.poll();
        }
        colorsHistory.offer(colorNumber);
    }
}