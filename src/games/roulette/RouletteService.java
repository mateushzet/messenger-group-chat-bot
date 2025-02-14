package games.roulette;

import repository.GameHistoryRepository;
import repository.UserAvatarRepository;
import service.MessageService;
import service.UserService;
import model.CommandContext;

import java.util.Random;

public class RouletteService {

    private static final int RED = -1;
    private static final int BLACK = -2;
    private static final int GREEN = -3;
    private static final int INVALID = -4;

    public static void handleRouletteCommand(CommandContext context) {
        String username = context.getUserName();
        String betAmountString = context.getFirstArgument();
        String fieldStr = context.getSecondArgument();

        int betAmountParsed = UserService.validateAndParseBetAmount(username, betAmountString);
        int field = parseFieldArgument(fieldStr);

        if (field == INVALID) {
            MessageService.sendMessage("Invalid bet. Provide a valid amount and color/number.");
            return;
        }

        if (betAmountParsed == -1) {
            return;
        }

        int randomNumber = new Random().nextInt(13); // 0-12
        if(randomNumber == 0) UserAvatarRepository.assignAvatarToUser(username, "roulette green");
        processRouletteOutcome(field, randomNumber, betAmountParsed, username, context);
    }

    private static void processRouletteOutcome(int field, int randomNumber, int amount, String username, CommandContext context) {
        int winAmount = calculateBalanceChange(field, randomNumber, amount);

        int userBalance = UserService.updateAndRetriveUserBalance(username, winAmount);
        GameHistoryRepository.addGameHistory(username, "Roulette", context.getFullCommand(), amount, winAmount, "Result: " + randomNumber);

        RouletteImageGenerator.generateImage(randomNumber, winAmount, userBalance, username, amount, GameHistoryRepository.getGameHistory(13, "Roulette"));
        MessageService.sendMessageFromClipboard(false);
    }

    private static int parseFieldArgument(String field) {
        try {
            return Integer.parseInt(field.trim());
        } catch (NumberFormatException e) {
            return parseBetType(field.trim());
        }
    }

    private static int parseBetType(String field) {
        switch (field.toLowerCase()) {
            case "red":
                return RED;
            case "black":
                return BLACK;
            case "green":
                return GREEN;
            default:
                return INVALID;
        }
    }

    private static int calculateBalanceChange(int field, int randomNumber, int amount) {
        if (field == RED && randomNumber % 2 != 0 && randomNumber != 0) return amount;
        if (field == BLACK && randomNumber % 2 == 0 && randomNumber != 0) return amount;
        if (field == GREEN && randomNumber == 0) return amount * 12;
        if (field >= 0 && field <= 12 && randomNumber == field) return amount * 12;
        return -amount;
    }

}
