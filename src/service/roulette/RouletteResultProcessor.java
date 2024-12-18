package service.roulette;

public class RouletteResultProcessor {

    public static String generateResultMessage(int field, int randomNumber, int amount) {
        if (randomNumber == 0) {
            return field == BetType.GREEN.getCode() ? "Won " + amount * 12 : "Lost " + amount;
        }

        if (field == BetType.RED.getCode() && randomNumber % 2 != 0) {
            return "Won " + amount;
        } else if (field == BetType.BLACK.getCode() && randomNumber % 2 == 0) {
            return "Won " + amount;
        } else if (field >= 0 && field <= 12 && randomNumber == field) {
            return "Won " + (amount * 12);
        } else {
            return "Lost " + amount;
        }
    }

    public static int calculateBalanceChange(int field, int randomNumber, int amount) {
        if (field == BetType.RED.getCode() && randomNumber % 2 != 0 && randomNumber != 0) {
            return amount;
        } else if (field == BetType.BLACK.getCode() && randomNumber % 2 == 0 && randomNumber != 0) {
            return amount;
        } else if (field == BetType.GREEN.getCode() && randomNumber == 0) {
            return amount * 12;
        } else if (field >= 0 && field <= 12 && randomNumber == field) {
            return amount * 12;
        } else {
            return -amount;
        }
    }
}