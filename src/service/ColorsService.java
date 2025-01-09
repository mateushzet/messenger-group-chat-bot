package service;

import java.util.Random;

import model.CommandContext;
import repository.ColorsRepository;
import repository.UserRepository;
import utils.ColorsImageGenerator;
import utils.ConfigReader;
import utils.LoggerUtil;

public class ColorsService {

    private static final int colorsAccessCost = ConfigReader.getColorsAccessCost();

    public static void handleColorsCommand(CommandContext context) {
        String playerName = context.getUserName();
        String betAmount = context.getFirstArgument();
        String betColor = context.getSecondArgument();
        int currentBalance = UserRepository.getUserBalance(playerName, false);
        int betAmountParsed;

        if(!ColorsRepository.hasColorsAccess(playerName)){
            MessageService.sendMessage("You need to purchase access to play colors. Cost: %d coins. /bot buy colors", colorsAccessCost);
            return;
        }

        Random random = new Random();
        int result = random.nextInt(53) + 1;
        int resultColorNumber = getResult(result);
        int winnings = 0;
        int balanceChange = 0;
        
        if (isMultiColorBet(betColor)) {
            String blackBet = context.getFirstArgument();
            String redBet = context.getSecondArgument();
            String blueBet = context.getThirdArgument();
            String goldBet = context.getFourthArgument();

            int blackBetParsed, redBetParsed, blueBetParsed, goldBetParsed;
            try {
                blackBetParsed = Integer.parseInt(blackBet);
                redBetParsed = Integer.parseInt(redBet);
                blueBetParsed = Integer.parseInt(blueBet);
                goldBetParsed = Integer.parseInt(goldBet);

                if (blackBetParsed < 0 || redBetParsed < 0 || blueBetParsed < 0 || goldBetParsed < 0) {
                    throw new NumberFormatException("Bet amounts must be non-negative");
                }

                if (blackBetParsed + redBetParsed + blueBetParsed + goldBetParsed == 0) {
                    throw new NumberFormatException("Bet amounts must be greater than 0");
                }

            } catch (NumberFormatException e) {
                MessageService.sendMessage("Invalid bet amount. Please enter a valid number. /bot colors amount (black,red,blue,gold) or /bot colors amountBlack amountRed amountBlue amountGold");
                return;
            }

            if(currentBalance < (blackBetParsed + redBetParsed + blueBetParsed + goldBetParsed)){
                MessageService.sendMessage("You can't afford the bet, current balance: %d", currentBalance);
                return;
            }

            winnings = calculateMultiColorWinnings(resultColorNumber, blackBetParsed, redBetParsed, blueBetParsed, goldBetParsed);
            balanceChange = winnings - (blackBetParsed + redBetParsed + blueBetParsed + goldBetParsed);

        } else {

            try {
                betAmountParsed = Integer.parseInt(betAmount);
                if (betAmountParsed <= 0) {
                    throw new NumberFormatException("Bet amount must be greater than 0");
                }
            } catch (NumberFormatException e) {
                MessageService.sendMessage("Invalid bet amount. Please enter a valid number greater than 0. /bot colors amount (black,red,blue,gold) or /bot colors amountBlack amountRed amountBlue amountGold");
                return;
            }

            if(currentBalance < betAmountParsed){
                MessageService.sendMessage("You can't afford the bet, current balance: %d", currentBalance);
                return;
            }

            winnings = calculateSingleColorWinnings(betColor, resultColorNumber, betAmountParsed);
            balanceChange = winnings - betAmountParsed;
        }

        int updatedBalance = currentBalance + balanceChange;
        UserRepository.updateUserBalance(playerName, updatedBalance);

        ColorsImageGenerator.generateColorsImage(winnings, playerName, updatedBalance, result);
        MessageService.sendMessageFromClipboard();
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
        LoggerUtil.logInfo("%s is attempting to buy colors.", userName);

        if (balance < colorsAccessCost) {
            MessageService.sendMessage("%s, you don't have enough coins to buy access to colors. You need %d coins.", userName, colorsAccessCost);
            LoggerUtil.logInfo("%s doesn't have enough coins to buy colors. Current balance: %d", userName, balance);
            return;
        }

        int newBalance = balance - colorsAccessCost;
        UserRepository.updateUserBalance(userName, newBalance);
        LoggerUtil.logInfo("%s purchased colors access. New balance: %d", userName, newBalance);

        if (ColorsRepository.addUserToColorsFile(userName)) {
            MessageService.sendMessage("%s has successfully bought access to colors for %d coins. New balance: %d", userName, colorsAccessCost, newBalance);
            LoggerUtil.logInfo("%s purchased colors access. New balance: %d", userName, newBalance);
        }
    }
}
