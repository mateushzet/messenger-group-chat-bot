package games.crash;

import repository.GameHistoryRepository;
import repository.UserRepository;
import service.MessageService;
import model.CommandContext;

import java.util.Random;

public class CrashService {
    private static final double HOUSE_EDGE = 0.01;
    private static final double MAX_MULTIPLIER = 100.0;

    public static void handleCrashCommand(CommandContext context) {
        String username = context.getUserName();
        String betAmountStr = context.getFirstArgument();
        String multiplierStr = context.getSecondArgument();
        
        int betAmount = parseBetAmount(betAmountStr);
        double playerCashout = parseMultiplier(multiplierStr);
        
        if (betAmount == -1 || playerCashout < 1.0 || playerCashout > MAX_MULTIPLIER) {
            MessageService.sendMessage("Invalid bet or cashout multiplier. Bet must be positive, and multiplier must be between 1 and 100.");
            return;
        }

        int userBalance = UserRepository.getCurrentUserBalance(username, false);
        if (userBalance < betAmount) {
            MessageService.sendMessage("You can't afford it, your balance is: %d", userBalance);
            return;
        }
        
        UserRepository.updateUserBalance(username, userBalance - betAmount);
        
        double crashMultiplier = calculateCrashMultiplier();
        boolean cashoutSuccess = playerCashout <= crashMultiplier;
        int winnings = cashoutSuccess ? (int) (betAmount * playerCashout) : 0;
        
        double finalMultiplier = CrashGifGenerator.playAndGenerateGif(username, betAmount, userBalance, playerCashout, crashMultiplier);
        
        GameHistoryRepository.addGameHistory(username, "Crash", context.getFullCommand(), betAmount, winnings, String.valueOf(finalMultiplier));
        UserRepository.updateUserBalance(username, userBalance - betAmount + winnings);
        MessageService.sendMessageFromClipboard(true);
    }

    private static double calculateCrashMultiplier() {
        Random random = new Random();
        double fairMultiplier = 1.0 / (random.nextDouble() * (1 - HOUSE_EDGE) + HOUSE_EDGE);
        return Math.min(fairMultiplier, MAX_MULTIPLIER);
    }

    private static int parseBetAmount(String betAmountStr) {
        try {
            int betAmount = Integer.parseInt(betAmountStr);
            return betAmount > 0 ? betAmount : -1;
        } catch (NumberFormatException e) {
            return -1;
        }
    }

    private static double parseMultiplier(String multiplierStr) {
        try {
            return Double.parseDouble(multiplierStr);
        } catch (NumberFormatException e) {
            return -1.0;
        }
    }
}
