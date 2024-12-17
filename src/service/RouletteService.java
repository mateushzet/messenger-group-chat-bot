package service;

import repository.UserRepository;
import java.util.Arrays;
import java.util.Map;
import java.util.Random;

import utils.ConfigReader;
import utils.LoggerUtil;
import model.CommandContext;

public class RouletteService {

    private static final String redHeartEmojiUrl = ConfigReader.getRedHeartEmojiUrl();
    private static final String blackHeartEmojiUrl = ConfigReader.getBlackHeartEmojiUrl();
    private static final String greenHeartEmojiUrl = ConfigReader.getGreenHeartEmojiUrl();
    private static final String numbersEmojisName = ConfigReader.getNumbersEmojisName() ;
    private static final String heartsEmojisName = ConfigReader.getHeartsEmojisName();
    private static final String numberEmojiUrl0 = ConfigReader.getNumberEmojiUrl0();
    private static final String numberEmojiUrl1 = ConfigReader.getNumberEmojiUrl1();
    private static final String numberEmojiUrl2 = ConfigReader.getNumberEmojiUrl2();
    private static final String numberEmojiUrl3 = ConfigReader.getNumberEmojiUrl3();
    private static final String numberEmojiUrl4 = ConfigReader.getNumberEmojiUrl4();
    private static final String numberEmojiUrl5 = ConfigReader.getNumberEmojiUrl5();
    private static final String numberEmojiUrl6 = ConfigReader.getNumberEmojiUrl6();
    private static final String numberEmojiUrl7 = ConfigReader.getNumberEmojiUrl7();
    private static final String numberEmojiUrl8 = ConfigReader.getNumberEmojiUrl8();
    private static final String numberEmojiUrl9 = ConfigReader.getNumberEmojiUrl9();

    
    public static void handleRouletteCommand(CommandContext context) {
        String userName = context.getUserName();
        String amount = context.getFirstArgument();
        String field = context.getSecondArgument();

        LoggerUtil.logInfo("%s bet: %s on %s", userName, amount, field);
    
        if (!validateBetArguments(amount, field, userName)) {
            return;
        }
    
        int userBalance = UserRepository.getUserBalance(userName, true);
        if (userBalance == 0) {
            MessageService.sendMessage("You are broke!");
            LoggerUtil.logInfo("%s tried to bet: %s but has balance equal to %d", userName, amount, userBalance);
            return;
        }
    
        int amountInteger = Integer.parseInt(amount.trim());
        int fieldParesd = parseFieldArgument(field);
    
        if (userBalance < amountInteger) {
            MessageService.sendMessage("You can't afford it, your balance is: %d", userBalance);
            LoggerUtil.logInfo("%s tried to bet: %d but has balance equal to %d", userName, amountInteger, userBalance);
            return;
        }
    
        int[] rouletteNumbers = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12};
        Random random = new Random();
        int randomNumber = rouletteNumbers[random.nextInt(rouletteNumbers.length)];
    
        if (!isValidBet(fieldParesd, rouletteNumbers)) {
            MessageService.sendMessage("You placed a bet on an invalid field. Bet on a number from 0 to 12 or red, black, or green!");
            LoggerUtil.logWarning("%s placed invalid bet: paresed field = %d, field = %s", userName, fieldParesd, field);
            return;
        }
    
        processRouletteOutcome(fieldParesd, randomNumber, amountInteger, userBalance, userName);
    }

    public static boolean isValidBet(int field, int[] rouletteNumbers) {
        LoggerUtil.logInfo("Validating field: %d", field);
        return field == -1 || field == -2 || field == -3 || Arrays.stream(rouletteNumbers).anyMatch(num -> num == field);
    }

    public static void processRouletteOutcome(int field, int randomNumber, int amount, int userBalance, String userName) {
        String resultMessage = generateResultMessage(field, randomNumber, amount, userBalance);
        int updatedBalance = calculateUpdatedBalance(field, randomNumber, amount, userBalance);
        
        resultMessage += " Balance: " + updatedBalance;

        handleEmoji(randomNumber);
        
        MessageService.sendMessage(resultMessage);
        UserRepository.updateUserBalance(userName, updatedBalance);
    }

    public static int getColorCode(String word) {
        switch (word) {
            case "red":
                return -1;
            case "black":
                return -2;
            case "green":
                return -3;
            default:
                return -4;
        }
    }

    private static String generateResultMessage(int field, int randomNumber, int amount, int userBalance) {
        String resultMessage = getRouletteResult(field, randomNumber, amount);
        return resultMessage;
    }
    
    private static String getRouletteResult(int field, int randomNumber, int amount) {
        if (randomNumber == 0) {
            return "Won " + (field == -3 ? amount * 12 : 0);
        }
        
        if (field == -1 && randomNumber % 2 != 0) {
            return "Won " + amount;
        } else if (field == -2 && randomNumber % 2 == 0) {
            return "Won " + amount;
        } else if (field > 0 && field <= 12 && randomNumber == field) {
            return "Won " + (amount * 12);
        } else {
            return "Lost " + amount;
        }
    }

    private static Map<Integer, String> emojiMap = Map.of(
        0, redHeartEmojiUrl,
        1, blackHeartEmojiUrl,
        2, greenHeartEmojiUrl
    );

    private static void handleEmoji(int randomNumber) {
        String heartEmoji = emojiMap.getOrDefault(randomNumber % 2, emojiMap.get(1)); // 1 for odd, 2 for even
        MessageService.clickEmoji(heartEmoji, heartsEmojisName);

        if (randomNumber >= 10) {
            int tens = randomNumber / 10; // Pierwsza cyfra
            int ones = randomNumber % 10; // Druga cyfra
            MessageService.clickEmoji(getNumbersUrls()[tens], numbersEmojisName);
            MessageService.clickEmoji(getNumbersUrls()[ones], numbersEmojisName);
        } else {
            MessageService.clickEmoji(getNumbersUrls()[randomNumber], numbersEmojisName);
        }
    }
    
    private static String[] getNumbersUrls() {
        String[] numbersUrl = new String[10];
        numbersUrl[0] = numberEmojiUrl0;
        numbersUrl[1] = numberEmojiUrl1;
        numbersUrl[2] = numberEmojiUrl2;
        numbersUrl[3] = numberEmojiUrl3;
        numbersUrl[4] = numberEmojiUrl4;
        numbersUrl[5] = numberEmojiUrl5;
        numbersUrl[6] = numberEmojiUrl6;
        numbersUrl[7] = numberEmojiUrl7;
        numbersUrl[8] = numberEmojiUrl8;
        numbersUrl[9] = numberEmojiUrl9;
        return numbersUrl;
    }

    private static int calculateUpdatedBalance(int field, int randomNumber, int amount, int userBalance) {
        int balanceChange = calculateBalanceChange(field, randomNumber, amount);
        return userBalance + balanceChange;
    }

    private static boolean validateBetArguments(String amount, String field, String userName) {
        if (amount == null || field == null) {
            LoggerUtil.logWarning("%s amount or field is null: %s, %s",userName, amount, field);
            MessageService.sendMessage("param1 or param2 is empty");
            return false;
        }
    
        int amountInteger;
        try {
            amountInteger = Integer.parseInt(amount.trim());
        } catch (NumberFormatException e) {
            MessageService.sendMessage("param1 is not valid number");
            LoggerUtil.logWarning("%s amount is not valid number: ",userName, amount);
            return false;
        }
        
        if (amountInteger <= 0) {
            MessageService.sendMessage("Bet must be greater than 0. Please place a valid bet.");
            LoggerUtil.logWarning("%s placed an invalid bet: %d",userName, amountInteger);
            return false;
        }
    
        int fieldParesd;
        try {
            fieldParesd = Integer.parseInt(field.trim());
        } catch (NumberFormatException e) {
            String field2Lower = field.trim().toLowerCase();
            fieldParesd = getColorCode(field2Lower);
            
            if (fieldParesd == -4) {
                MessageService.sendMessage("param2 is not valid color or number");
                LoggerUtil.logWarning("%s fieldParesd is not valid color or number: %d", userName, fieldParesd);
                return false;
            }
        }
    
        return true;
    }

    private static int calculateBalanceChange(int field, int randomNumber, int amount) {
        if (field == -1 && randomNumber % 2 != 0 && randomNumber != 0) {
            return amount;
        } else if (field == -2 && randomNumber % 2 == 0 && randomNumber != 0) {
            return amount;
        } else if (field == -3 && randomNumber == 0) {
            return amount * 12;
        } else if (field > 0 && field <= 12 && randomNumber == field) {
            return amount * 12;
        } else {
            return -amount;
        }
    }

    private static int parseFieldArgument(String field) {
        try {
            return Integer.parseInt(field.trim());
        } catch (NumberFormatException e) {
            return getColorCode(field.trim().toLowerCase());
        }
    }
}
