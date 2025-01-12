package service;

import repository.UserRepository;
import repository.MinesGameRepository;
import model.CommandContext;
import model.MinesGame;
import utils.MinesImageGenerator;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class MinesService {

    private static final int BOARD_SIZE = 5;

    public static void handleMinesCommand(CommandContext context) {
        String userName = context.getUserName();
        String firstArg = context.getFirstArgument();
        String secondArg = context.getSecondArgument();
        String thirdArg = context.getThirdArgument();

        if (firstArg.equalsIgnoreCase("start")) {
            startGame(userName, secondArg, thirdArg);
            return;
        }

        if (firstArg.equalsIgnoreCase("cashout")) {
            handleCashout(userName);
            return;
        }

        if (firstArg.equalsIgnoreCase("help")) {
            String helpMessage = "/bot mines start [bet amount] [bomb count (default 3)] \n" +
                                 "/bot mines cashout \n" +
                                 "after start /bot mines [field number 1-25] to reveal field \n" +
                                 "The game ends when you either hit a bomb or reveal all safe fields or cashout. \n";
            MessageService.sendMessage(helpMessage);
            return;
        }

        MinesGame game = MinesGameRepository.getGameByUserName(userName);
        if (game != null && game.isGameInProgress()) {
            String currentPlayer = game.getUserName();
            if (userName.equals(currentPlayer)) {
                try {
                    int fieldNumber = Integer.parseInt(firstArg);
                    revealField(userName, fieldNumber);
                } catch (NumberFormatException e) {
                    MessageService.sendMessage(userName + " invalid field number. Please provide a valid number.");
                }
            } else {
                MessageService.sendMessage(userName + " it's not your turn!");
            }
        } else {
            MessageService.sendMessage(userName + " no game in progress.");
        }
    }

    private static void startGame(String userName, String betAmount, String bombCountArg) {
        MinesGame existingGame = MinesGameRepository.getGameByUserName(userName);
        if (existingGame != null && existingGame.isGameInProgress()) {
            MessageService.sendMessage(userName + " you already have an active game. Finish that game before starting a new one.");
            return;
        }
    
        int bet;
        try {
            bet = Integer.parseInt(betAmount);
        } catch (NumberFormatException e) {
            MessageService.sendMessage(userName + " invalid bet amount. Please provide a valid number.");
            return;
        }
    
        int userBalance = UserRepository.getUserBalance(userName, true);
        if (userBalance < bet) {
            MessageService.sendMessage(userName + " you don't have enough balance to play.");
            return;
        }
    
        int bombCount = 3;
        try {
            if (bombCountArg != null && !bombCountArg.isEmpty()) {
                bombCount = Integer.parseInt(bombCountArg);
                if (bombCount < 1 || bombCount > ((BOARD_SIZE * BOARD_SIZE) - 1)) {
                    MessageService.sendMessage(userName + " invalid bomb count. Please choose a number between 1 and " + ((BOARD_SIZE * BOARD_SIZE) - 1));
                    return;
                }
            }
        } catch (NumberFormatException e) {
            MessageService.sendMessage(userName + " invalid bomb count. Please provide a valid number.");
            return;
        }
    
        int userBet = bet;
        int totalBombs = bombCount;
        int revealedFields = 0;
    
        boolean[][] bombBoard = new boolean[BOARD_SIZE][BOARD_SIZE];
        boolean[][] revealedBoard = new boolean[BOARD_SIZE][BOARD_SIZE];
    
        placeBombsOnBoard(totalBombs, bombBoard);
    
        UserRepository.updateUserBalance(userName, userBalance - bet);

        MinesGame game = new MinesGame(userName, bet, totalBombs, revealedFields, true,
        bombBoard, revealedBoard);
        MinesGameRepository.saveGame(game);

        totalBombs = game.getTotalBombs();
        Double multiplier = calculateMultiplier(game);

        List<String> status = List.of(userName, "Bet: " + betAmount, "Reward: " + (int) Math.round(multiplier * userBet), "Bombs: " + totalBombs, "Multiplier: " + multiplier);
        MinesImageGenerator.generateMinesweeperImage(game.getRevealedBoard(), game.getBombBoard(), userName, status, null, userBalance);
    
        MessageService.sendMessageFromClipboard(true);
    }

    private static void placeBombsOnBoard(int bombCount, boolean[][] bombBoard) {
        List<Integer> allPositions = new ArrayList<>();
        for (int i = 0; i < BOARD_SIZE * BOARD_SIZE; i++) {
            allPositions.add(i);
        }

        Collections.shuffle(allPositions);

        for (int i = 0; i < bombCount; i++) {
            int position = allPositions.get(i);
            int row = position / BOARD_SIZE;
            int col = position % BOARD_SIZE;
            bombBoard[row][col] = true;
        }
    }

    private static void revealField(String userName, int fieldNumber) {

        String gameStatus = null;

        MinesGame game = MinesGameRepository.getGameByUserName(userName);
        if (game == null || !game.isGameInProgress()) {
            MessageService.sendMessage(userName + " no game in progress.");
            return;
        }
    
        int fieldIndex = fieldNumber - 1;
        if (fieldIndex < 0 || fieldIndex >= BOARD_SIZE * BOARD_SIZE) {
            MessageService.sendMessage(userName + " invalid field number. Try again.");
            return;
        }
    
        int row = fieldIndex / BOARD_SIZE;
        int col = fieldIndex % BOARD_SIZE;
    
        if (game.getRevealedBoard()[row][col]) {
            MessageService.sendMessage(userName + " this field has already been revealed.");
            return;
        }
    
        game.getRevealedBoard()[row][col] = true;
    
        if (game.getBombBoard()[row][col]) {
            endGame(userName, false, game);
            gameStatus = "Game over!";
        }
    
        if (checkIfAllSafeFieldsRevealed(game)) {
            int betAmount = game.getBetAmount();
            Double multiplier = calculateMultiplier(game);
            endGame(userName, true, game);
            gameStatus = "You won " + (int) Math.round(multiplier * betAmount);
        }

        int revealedFields = game.getRevealedFields();
        game.setRevealedFields(revealedFields + 1);

        int betAmount = game.getBetAmount();
        int totalBombs = game.getTotalBombs();
        Double multiplier = calculateMultiplier(game);
        int userBalance = UserRepository.getUserBalance(userName, false);

        MinesGameRepository.updateGame(game);

        List<String> status = List.of(userName, "Bet: " + betAmount, "Reward: " + (int) Math.round(multiplier * betAmount), "Bombs: " + totalBombs, "Multiplier: " + multiplier);
        MinesImageGenerator.generateMinesweeperImage(game.getRevealedBoard(), game.getBombBoard(), userName, status, gameStatus, userBalance);
    
        MessageService.sendMessageFromClipboard(false);
    }

    private static void endGame(String userName, boolean win, MinesGame game) {
        if (game != null) {
            if (win) {
                int userBalance = UserRepository.getUserBalance(userName, true);
                int totalAmount = (int) Math.round(game.getBetAmount() * calculateMultiplier(game));
                UserRepository.updateUserBalance(userName, userBalance + totalAmount);
                MessageService.sendMessage(userName + " has cashed out! You won " + totalAmount + "!" + "Current balance: " + (userBalance + totalAmount));
            }
            MinesGameRepository.deleteGame(userName);
        }
    }

    private static double calculateMultiplier(MinesGame game) {
        double probability = 1.0;
        int revealedFields = game.getRevealedFields();
        int totalBombs = game.getTotalBombs();

        for (int i = 0; i < revealedFields; i++) {
            probability *= (double)(BOARD_SIZE * BOARD_SIZE - totalBombs - i) / (BOARD_SIZE * BOARD_SIZE - i);
        }
    
        double multiplier = 1 / probability;
    
        multiplier = Math.max(multiplier, 1.0);
    
        return Math.round(multiplier * 100.0) / 100.0;
    }
    

    private static void handleCashout(String userName) {
        MinesGame game = MinesGameRepository.getGameByUserName(userName);
        if (game == null || !game.isGameInProgress()) {
            MessageService.sendMessage(userName + " you don't have an active game to cash out from.");
            return;
        }
    
        endGame(userName, true, game);
    }

    private static boolean checkIfAllSafeFieldsRevealed(MinesGame game) {
        int safeFields = 0;
        int totalSafeFields = 0;
    
        for (int row = 0; row < BOARD_SIZE; row++) {
            for (int col = 0; col < BOARD_SIZE; col++) {
                if (!game.getBombBoard()[row][col]) {
                    totalSafeFields++;
                    if (game.getRevealedBoard()[row][col]) {
                        safeFields++;
                    }
                }
            }
        }
    
        return safeFields == totalSafeFields;
    }

}
