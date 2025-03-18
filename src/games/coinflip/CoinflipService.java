package games.coinflip;

import repository.GameHistoryRepository;
import repository.UserAvatarRepository;
import repository.UserRepository;
import service.MessageService;
import service.UserService;
import utils.Logger;
import model.CoinflipGame;
import model.CommandContext;

import java.io.IOException;
import java.util.List;
import java.util.Random;

public class CoinflipService {

    public static void handleCoinflipCommand(CommandContext context) {
        String command = context.getFirstArgument();
        String username = context.getUserName();
        String secondArgument = context.getSecondArgument();
        int userBalance = UserRepository.getCurrentUserBalance(username, false);

        if (command.equalsIgnoreCase("bet")) {
            handleBetCommand(context, username, secondArgument);
            handleCheckActiveGamesCommand();
        } else if (command.equalsIgnoreCase("accept")) {
            handleAcceptCommand(context, username, userBalance);
        } else if (command.equalsIgnoreCase("cancel")) {
            handleCancelCommand(context, username, userBalance);
        } else if (command.equalsIgnoreCase("games")) {
            handleCheckActiveGamesCommand();
        } else {
            handleCheckActiveGamesCommand();
            MessageService.sendMessage("Avaiable commands: bet, accept, cancel, games");
        }
    }

    private static void handleBetCommand(CommandContext context, String username, String betAmountString) {
            int betAmountParsed = UserService.validateAndParseBetAmount(username, betAmountString);
            if (betAmountParsed == -1) {
                return;
            }

            Integer gameId = CoinflipRepository.addCoinflipGame(username, betAmountParsed);
            if (gameId != null) {
                UserService.updateAndRetriveUserBalance(username, -betAmountParsed);
                MessageService.sendMessage(username + " has started a coinflip with a bet of " + betAmountParsed + " and ID: " + gameId);
            } else {
                MessageService.sendMessage("Failed to start the coinflip");
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
            UserAvatarRepository.assignAvatarToUser(username, "coin");
            GameHistoryRepository.addGameHistory(opponent, "Coinflip", context.getFullCommand(), betAmount, -betAmount, "Result: " + result);
            GameHistoryRepository.addGameHistory(username, "Coinflip", context.getFullCommand(), betAmount, betAmount, "Result: " + result);
        } else {
            winner = opponent;
            UserAvatarRepository.assignAvatarToUser(opponent, "coin");
            GameHistoryRepository.addGameHistory(opponent, "Coinflip", context.getFullCommand(), betAmount, betAmount, "Result: " + result);
            GameHistoryRepository.addGameHistory(username, "Coinflip", context.getFullCommand(), betAmount, -betAmount, "Result: " + result);
        }
        CoinflipRepository.updateGameResult(gameIdParsed, winner);
        UserService.updateAndRetriveUserBalance(winner, betAmount);
        String message = winner + " won " + 2 * betAmount;
        try {
            CoinFlipGifGenerator.generateCoinFlipGif(username, opponent, winner, message);
        } catch (IOException e) {
            MessageService.sendMessage(message);
            e.printStackTrace();
        }
        MessageService.sendMessageFromClipboard(true);
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
            UserService.updateAndRetriveUserBalance(username, betAmount);
            MessageService.sendMessage(username + " has canceled the coinflip.");
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
