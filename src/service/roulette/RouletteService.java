package service.roulette;

import service.EmojiService;
import repository.UserRepository;
import service.MessageService;
import utils.ConfigReader;
import utils.Logger;
import utils.RouletteImageGenerator;
import model.CommandContext;

import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import java.util.Queue;
import java.util.Random;

public class RouletteService {

    private static final Queue<Integer> rouletteHistory = new LinkedList<>();

    public static void handleRouletteCommand(CommandContext context) {
        String userName = context.getUserName();
        String amount = context.getFirstArgument();
        String field = context.getSecondArgument();

        if (amount.equalsIgnoreCase("history")) {
           int colorCount = 5;
            try {
                colorCount = Integer.parseInt(field.trim());
                showHistory(colorCount);
            } catch (Exception e) {
                showHistory(colorCount);
            }
            return;
        }

        Logger.logInfo("%s bet: %s on %s", "RouletteService.handleRouletteCommand()", userName, amount, field);

        if (!BetValidator.validateBetArguments(amount, field, userName)) {
            return;
        }

        int userBalance = UserRepository.getUserBalance(userName, true);

        int amountInteger = Integer.parseInt(amount.trim());
        int fieldParsed = parseFieldArgument(field);

        if (userBalance < amountInteger) {
            MessageService.sendMessage("You can't afford it, your balance is: %d", userBalance);
            Logger.logInfo("%s tried to bet: %d but has balance equal to %d", "RouletteService.handleRouletteCommand()", userName, amountInteger, userBalance);
            return;
        }

        int randomNumber = new Random().nextInt(13); // Random number between 0 and 12

        if (!BetValidator.isValidBet(fieldParsed)) {
            MessageService.sendMessage("You placed a bet on an invalid field. Bet on a number from 0 to 12 or red, black, or green!");
            Logger.logWarning("%s placed invalid bet: parsed field = %d, field = %s", "RouletteService.handleRouletteCommand()", userName, fieldParsed, field);
            return;
        }

        storeNumberColor(randomNumber);

        processRouletteOutcome(fieldParsed, randomNumber, amountInteger, userBalance, userName);
    }

    public static void processRouletteOutcome(int field, int randomNumber, int amount, int userBalance, String userName) {
        //String resultMessage = RouletteResultProcessor.generateResultMessage(field, randomNumber, amount);
        int winAmount = RouletteResultProcessor.calculateBalanceChange(field, randomNumber, amount);
        int updatedBalance = winAmount + userBalance;
        
        //resultMessage = userName + resultMessage + " Balance: " + updatedBalance;

        UserRepository.updateUserBalance(userName, updatedBalance);

        RouletteImageGenerator.generateImage(randomNumber, winAmount, updatedBalance, userName, amount, rouletteHistory);
        MessageService.sendMessageFromClipboard();

        //MessageService.sendMessage(resultMessage);

    }

    private static void showHistory(int numberOfColors) {
        if (rouletteHistory.isEmpty()) {
            MessageService.sendMessage("No roulette history available.");
            return;
        }

        numberOfColors = Math.max(5, Math.min(numberOfColors, 10));

        List<Integer> historyList = new ArrayList<>(rouletteHistory);

        int start = Math.max(0, historyList.size() - numberOfColors);
        List<Integer> latestColors = historyList.subList(start, historyList.size());


        for (int colorNumber : latestColors) {
            String heartEmoji = EmojiService.getRouletteColorEmoji(colorNumber);
            MessageService.clickEmoji(heartEmoji, ConfigReader.getHeartsEmojisName());
        }
            MessageService.sendMessage(""); 
    }

    private static void storeNumberColor(int colorNumber) {
        if (rouletteHistory.size() >= 13) {
            rouletteHistory.poll();
        }
        rouletteHistory.offer(colorNumber);
    }

    private static void handleEmoji(int randomNumber) {
        EmojiService.sendRouletteResultEmojis(randomNumber);
    }

    private static int parseFieldArgument(String field) {
        try {
            return Integer.parseInt(field.trim());
        } catch (NumberFormatException e) {
            return BetType.fromString(field.trim()).getCode();
        }
    }

    private static int getColorNumber(int number) {
        return number == 0 ? 2 : number % 2; // 0 = black, 1 = red, 2 = green
    }
}