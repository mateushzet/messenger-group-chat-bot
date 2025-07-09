package games.colors;

import java.util.Queue;
import java.util.Random;

import model.CommandContext;
import repository.GameHistoryRepository;
import repository.UserAvatarRepository;
import repository.UserRepository;
import service.MessageService;

public class ColorsService {

    public static void handleColorsCommand(CommandContext context) {
        String playerName = context.getUserName();
        String betColor = context.getSecondArgument();
        int currentBalance = UserRepository.getCurrentUserBalance(playerName, false);

        Random random = new Random();
        int result = random.nextInt(53);
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

        if(resultColorNumber == 3 && winnings > 0) UserAvatarRepository.assignAvatarToUser(playerName, "colors gold");

        int updatedBalance = currentBalance + balanceChange;
        UserRepository.updateUserBalance(playerName, updatedBalance);

        if (winnings <= 0) winnings = balanceChange;
        Queue<Integer> colorsHisotry = GameHistoryRepository.getGameHistory(16, "Colors");
        GameHistoryRepository.addGameHistory(playerName, "Colors", context.getFullCommand(), betAmount, winnings, "Result: " + resultColorNumber);
        ColorsGifGenerator.generateColorsGif(winnings, playerName, updatedBalance, currentBalance, result, betAmount, colorsHisotry);
        MessageService.sendMessageFromClipboardWindows(true);
    }
    
    private static int[] handleMultiColorBet(CommandContext context, int currentBalance, int resultColorNumber) {
        String blackBet = context.getFirstArgument();
        String redBet = context.getSecondArgument();
        String blueBet = context.getThirdArgument();
        String goldBet = context.getFourthArgument();
    
        int blackBetParsed = parseBetAmount(blackBet);
        int redBetParsed = parseBetAmount(redBet);
        int blueBetParsed = parseBetAmount(blueBet);
        int goldBetParsed = parseBetAmount(goldBet);

        if(blackBet.isEmpty()){
            MessageService.sendMessage("/bot colors amountBlack amountRed amountBlue amountGold\n/bot colors amount color");
        }

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
            MessageService.sendMessage("You can't afford the bet, current balance: " + currentBalance);
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
            MessageService.sendMessage("Invalid bet amount. Please enter a valid number greater than 0. /bot colors amount color");
            return null; 
        }
    
        if (currentBalance < betAmountParsed) {
            MessageService.sendMessage("You can't afford the bet, current balance: " + currentBalance);
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
        int[] colorOrder = {3, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2};
        colorOrder = ColorsGifGenerator.rotateArray(colorOrder, shift);
        return colorOrder[0]; // wining position
    }

}