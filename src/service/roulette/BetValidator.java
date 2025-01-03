package service.roulette;

import service.MessageService;
import utils.LoggerUtil;

public class BetValidator {

    public static boolean validateBetArguments(String amount, String field, String userName) {
        if (amount == null || field == null) {
            LoggerUtil.logWarning("%s amount or field is null: %s, %s", userName, amount, field);
            MessageService.sendMessage("param1 or param2 is empty");
            return false;
        }

        int amountInteger;
        try {
            amountInteger = Integer.parseInt(amount.trim());
        } catch (NumberFormatException e) {
            MessageService.sendMessage("param1 is not a valid number");
            LoggerUtil.logWarning("%s amount is not a valid number: %s", userName, amount);
            return false;
        }

        if (amountInteger <= 0) {
            MessageService.sendMessage("Bet must be greater than 0. Please place a valid bet.");
            LoggerUtil.logWarning("%s placed an invalid bet: %d", userName, amountInteger);
            return false;
        }

        int fieldParsed = parseFieldArgument(field);
        if (fieldParsed == BetType.INVALID.getCode()) {
            MessageService.sendMessage("param2 is not a valid color or number");
            LoggerUtil.logWarning("%s fieldParsed is not a valid color or number: %s", userName, field);
            return false;
        }

        return true;
    }

    public static boolean isValidBet(int field) {
        return field >= 0 && field <= 12 || field == BetType.RED.getCode() || field == BetType.BLACK.getCode() || field == BetType.GREEN.getCode();
    }

    private static int parseFieldArgument(String field) {
        try {
            return Integer.parseInt(field.trim());
        } catch (NumberFormatException e) {
            return BetType.fromString(field.trim()).getCode();
        }
    }
}