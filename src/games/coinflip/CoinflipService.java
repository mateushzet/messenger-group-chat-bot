package games.coinflip;

import repository.GameHistoryRepository;
import repository.UserRepository;
import service.MessageService;
import utils.Logger;
import model.CoinflipGame;
import model.CommandContext;

import java.util.List;
import java.util.Random;

public class CoinflipService {

    public static void handleCoinflipCommand(CommandContext context) {
        String command = context.getFirstArgument();
        String username = context.getUserName();
        int userBalance = UserRepository.getCurrentUserBalance(username, false);

        if (command.equalsIgnoreCase("bet")) {
            handleBetCommand(context, username, userBalance);
        } else if (command.equalsIgnoreCase("accept")) {
            handleAcceptCommand(context, username, userBalance);
        } else if (command.equalsIgnoreCase("cancel")) {
            handleCancelCommand(context, username, userBalance);
        } else if (command.equalsIgnoreCase("games")) {
            handleCheckActiveGamesCommand();
        } else {
            MessageService.sendMessage("Invalid command.");
        }
    }

    private static void handleBetCommand(CommandContext context, String username, int userBalance) {
        try {
            int coinFlipAmount = Integer.parseInt(context.getSecondArgument());
            if (coinFlipAmount <= 0) {
                MessageService.sendMessage("Invalid bet amount.");
                return;
            }
            if (userBalance < coinFlipAmount) {
                MessageService.sendMessage("Insufficient balance.");
                return;
            }

            Integer gameId = CoinflipRepository.addCoinflipGame(username, coinFlipAmount);
            if (gameId != null) {
                UserRepository.updateUserBalance(username, userBalance - coinFlipAmount);
                MessageService.sendMessage("%s has started a coinflip with a bet of %d and ID: %d", username, coinFlipAmount, gameId);
            } else {
                MessageService.sendMessage("Failed to start the coinflip");
            }
        } catch (NumberFormatException e) {
            MessageService.sendMessage("Invalid bet amount");
        }
    }

    private static void handleAcceptCommand(CommandContext context, String username, int userBalance) {
        String gameId = context.getSecondArgument();
        int gameIdParsed = parseGameId(gameId);
        if (gameIdParsed == -1) return;

        CoinflipGame game = CoinflipRepository.getGameById(gameIdParsed);
        if (game == null) {
            MessageService.sendMessage("Invalid game ID");
            return;
        }

        int betAmount = game.getBetAmount();
        if (betAmount > userBalance) {
            MessageService.sendMessage("You don't have enough coins to accept this coinflip.");
            return;
        }

        String opponent = game.getPlayer1Username();
        int result = new Random().nextInt(2);
        String winner;
        if(result == 1){
            winner = username;
            GameHistoryRepository.addGameHistory(opponent, "Coinflip", context.getFullCommand(), betAmount, -betAmount, "Result: " + result);
            GameHistoryRepository.addGameHistory(username, "Coinflip", context.getFullCommand(), betAmount, betAmount, "Result: " + result);
        } else {
            winner = opponent;
            GameHistoryRepository.addGameHistory(opponent, "Coinflip", context.getFullCommand(), betAmount, betAmount, "Result: " + result);
            GameHistoryRepository.addGameHistory(username, "Coinflip", context.getFullCommand(), betAmount, -betAmount, "Result: " + result);
        }
        CoinflipRepository.updateGameResult(gameIdParsed, winner);
        UserRepository.updateUserBalance(winner, UserRepository.getCurrentUserBalance(winner, false) + betAmount);
        MessageService.sendMessage("%s won %d in the coinflip battle!", winner, betAmount);
    }

    private static void handleCancelCommand(CommandContext context, String username, int userBalance) {
        String gameId = context.getSecondArgument();
        int gameIdParsed = parseGameId(gameId);
        if (gameIdParsed == -1) return;

        CoinflipGame game = CoinflipRepository.getGameById(gameIdParsed);
        if (game == null) {
            MessageService.sendMessage("Invalid game ID");
            return;
        }

        String owner = game.getPlayer1Username();
        int betAmount = game.getBetAmount();

        if (owner.equals(username)) {
            CoinflipRepository.cancelGame(gameIdParsed);
            UserRepository.updateUserBalance(username, userBalance + betAmount);
            MessageService.sendMessage("%s has canceled the coinflip.", username);
        } else {
            MessageService.sendMessage("You can only cancel the game if you're the host.");
        }
    }

    private static int parseGameId(String gameId) {
        try {
            return Integer.parseInt(gameId);
        } catch (Exception e) {
            Logger.logError("Invalid gameId", "CoinflipService.parseGameId()", e);
            MessageService.sendMessage("Invalid game ID");
            return -1;
        }
    }

    private static void handleCheckActiveGamesCommand() {
        List<CoinflipGame> openGames = CoinflipRepository.getOpenGames();
        
        if (openGames.isEmpty()) {
            MessageService.sendMessage("There are no active coinflip games at the moment.");
        } else {
            CoinflipGamesImageGenerator.generateActiveGamesImage(openGames);
            MessageService.sendMessageFromClipboard(true);
        }
    }

}
