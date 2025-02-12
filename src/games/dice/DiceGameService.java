package games.dice;

import model.DiceGame;
import model.CommandContext;
import repository.GameHistoryRepository;
import repository.UserRepository;
import service.MessageService;

public class DiceGameService {

    public static void handleDiceCommand(CommandContext context) {
        String userName = context.getUserName();
        String firstArg = context.getFirstArgument();
        String secondArg = context.getSecondArgument();

        if (firstArg.equalsIgnoreCase("bet") || firstArg.equalsIgnoreCase("b")) {
            startGame(userName, secondArg, context);
            return;
        }

        if (firstArg.equalsIgnoreCase("reroll") || firstArg.equalsIgnoreCase("r")) {
            rerollDice(userName, secondArg, context);
            return;
        }

        if (firstArg.equalsIgnoreCase("stand") || firstArg.equalsIgnoreCase("s")) {
            endGame(userName, context);
            return;
        }

        String helpMessage = "/bot dice bet [bet amount]\n" +
                             "/bot dice reroll [dice indices]\n" +
                             "/bot dice stand\n" +
                             "The goal is to get the highest dice multiplier after one reroll.";
        MessageService.sendMessage(helpMessage);
    }

    private static void startGame(String userName, String betAmountArg, CommandContext context) {
        DiceGame existingGame = DiceGameRepository.getGameByUserName(userName);
        if (existingGame != null && existingGame.isGameInProgress()) {
            MessageService.sendMessage(userName + " you already have an active game. Finish that game before starting a new one.");
            return;
        }

        int betAmount;
        try {
            betAmount = Integer.parseInt(betAmountArg);
        } catch (NumberFormatException e) {
            MessageService.sendMessage(userName + " invalid bet amount. Please provide a valid number.");
            return;
        }

        if (betAmount <= 0) {
            MessageService.sendMessage(userName + " invalid bet amount. Please provide a valid number.");
            return;
        }

        int userBalance = UserRepository.getCurrentUserBalance(userName, true);
        if (userBalance < betAmount) {
            MessageService.sendMessage(userName + " you don't have enough balance to place this bet.");
            return;
        }

        UserRepository.updateUserBalance(userName, userBalance - betAmount);

        int[] diceValues = generateDiceRoll();
        double multiplier = calculateMultiplier(diceValues);

        DiceGame game = new DiceGame(userName, betAmount, diceValues, true, userBalance);
        DiceGameRepository.saveGame(game);

        DiceImageGenerator.drawDiceResults(diceValues, betAmount, userBalance - betAmount, userName, multiplier, false);

        MessageService.sendMessageFromClipboard(true);
    }

    private static void rerollDice(String userName, String diceIndicesArg, CommandContext context) {
        DiceGame game = DiceGameRepository.getGameByUserName(userName);
        if (game == null || !game.isGameInProgress()) {
            MessageService.sendMessage(userName + " no active game. Start a new game with /bot dice bet [bet amount].");
            return;
        }
    
        String[] indices = diceIndicesArg.split(",");
        int[] diceToReroll = new int[indices.length];
        for (int i = 0; i < indices.length; i++) {
            try {
                diceToReroll[i] = Integer.parseInt(indices[i].trim());
            } catch (NumberFormatException e) {
                MessageService.sendMessage(userName + " invalid dice index.");
                return;
            }
        }
    
        int[] diceValues = game.getDiceValues();
        for (int index : diceToReroll) {
            if (index >= 1 && index <= 6) {
                diceValues[index - 1] = (int) (Math.random() * 6) + 1;
            }
        }
    
        game.setDiceValues(diceValues);
    
        DiceGameRepository.updateGame(game);
    
        endGame(userName, context);
    }

    private static void endGame(String userName, CommandContext context) {
        DiceGame game = DiceGameRepository.getGameByUserName(userName);
        if (game == null || !game.isGameInProgress()) {
            MessageService.sendMessage(userName + " no active game to end.");
            return;
        }

        int userBalance = UserRepository.getCurrentUserBalance(userName, false);
        double multiplier = calculateMultiplier(game.getDiceValues());
        int betAmount = game.getBetAmount();
        int winnings = (int) (betAmount * multiplier);

        UserRepository.updateUserBalance(userName, userBalance + winnings);

        String gameStatus = userName + " you won " + winnings + "!";
        GameHistoryRepository.addGameHistory(userName, "Dice", context.getFullCommand(), game.getBetAmount(), winnings - betAmount, gameStatus);

        DiceGameRepository.deleteGame(userName);

        DiceImageGenerator.drawDiceResults(game.getDiceValues(), game.getBetAmount(), userBalance + winnings, userName, multiplier, true);

        MessageService.sendMessageFromClipboard(true);
    }

    private static int[] generateDiceRoll() {
        int[] diceValues = new int[6];
        for (int i = 0; i < 6; i++) {
            diceValues[i] = (int) (Math.random() * 6) + 1;
        }
        return diceValues;
    }

    private static double calculateMultiplier(int[] diceValues) {

        int[] count = new int[6];
        
        for (int value : diceValues) {
            count[value - 1]++;
        }
    
        boolean hasSixOfSame = false;
        boolean hasFiveOfSame = false;
        boolean hasFourOfSame = false;
        boolean hasStrit = true;
        int pairs = 0;
        int threes = 0;
    
        for (int c : count) {
            if (c == 6) hasSixOfSame = true;
            if (c == 5) hasFiveOfSame = true;
            if (c == 4) hasFourOfSame = true;
            if (c == 3) threes++;
            if (c == 2) pairs++;
            if (c != 1) hasStrit = false;
        }
    
        if (hasSixOfSame) return 7;
        if (hasStrit) return 7;
        if (hasFiveOfSame) return 3;
        if (pairs == 3) return 3;
        if (hasFourOfSame && pairs == 1) return 2;
        if (threes == 2) return 1.5;
        if (hasFourOfSame) return 1.5;
        if (pairs == 1 && threes == 1) return 0.4;
        if (threes == 1) return 0.2;
    
        return 0;
    }
}
