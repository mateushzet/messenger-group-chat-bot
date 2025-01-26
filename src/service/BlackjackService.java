package service;

import model.BlackjackGame;
import model.CommandContext;
import repository.BlackjackGameRepository;
import repository.UserRepository;
import utils.BlackjackImageGenerator;

import java.util.ArrayList;
import java.util.List;

public class BlackjackService {

    public static void handleBlackjackCommand(CommandContext context) {
        String userName = context.getUserName();
        String firstArg = context.getFirstArgument();
        String secondArg = context.getSecondArgument();

        if (firstArg.equalsIgnoreCase("start")) {
            startGame(userName, secondArg);
            return;
        }

        if (firstArg.equalsIgnoreCase("hit")) {
            hitCard(userName);
            return;
        }

        if (firstArg.equalsIgnoreCase("stand")) {
            stand(userName);
            return;
        }

        String helpMessage = "/bot blackjack start [bet amount]\n" +
                             "/bot blackjack hit\n" +
                             "/bot blackjack stand\n" +
                             "The goal is to get as close to 21 as possible without exceeding it.";
        MessageService.sendMessage(helpMessage);
        
    }

    private static void startGame(String userName, String betAmountArg) {
        BlackjackGame existingGame = BlackjackGameRepository.getGameByUserName(userName);
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

        int userBalance = UserRepository.getUserBalance(userName, true);
        if (userBalance < betAmount) {
            MessageService.sendMessage(userName + " you don't have enough balance to place this bet.");
            return;
        }

        UserRepository.updateUserBalance(userName, userBalance - betAmount);

        List<String> playerHand = new ArrayList<>();
        List<String> dealerHand = new ArrayList<>();

        playerHand.add(drawCard());
        playerHand.add(drawCard());
        dealerHand.add(drawCard());

        BlackjackGame game = new BlackjackGame(userName, betAmount, playerHand, dealerHand, true, userBalance);
        BlackjackGameRepository.saveGame(game);

        BlackjackImageGenerator.generateBlackjackImage(userName, playerHand, dealerHand, "Game Started", userBalance);
        MessageService.sendMessageFromClipboard(false);
    }

    private static void hitCard(String userName) {
        BlackjackGame game = BlackjackGameRepository.getGameByUserName(userName);
        if (game == null || !game.isGameInProgress()) {
            MessageService.sendMessage(userName + " no active game. Start a new game with /bot blackjack start [bet amount].");
            return;
        }

        List<String> playerHand = game.getPlayerHand();
        playerHand.add(drawCard());
        game.setPlayerHand(playerHand);

        if (calculateHandValue(playerHand) > 21) {
            endGame(userName, false);
            return;
        }

        int userBalance = UserRepository.getUserBalance(userName, false);
        BlackjackGameRepository.updateGame(game);
        BlackjackImageGenerator.generateBlackjackImage(userName, playerHand, game.getDealerHand(), "You drew a card", userBalance);
        MessageService.sendMessageFromClipboard(false);

    }

    private static void stand(String userName) {
        BlackjackGame game = BlackjackGameRepository.getGameByUserName(userName);
        if (game == null || !game.isGameInProgress()) {
            MessageService.sendMessage(userName + " no active game. Start a new game with /bot blackjack start [bet amount].");
            return;
        }

        List<String> dealerHand = game.getDealerHand();
        while (calculateHandValue(dealerHand) < 17) {
            dealerHand.add(drawCard());
        }

        game.setDealerHand(dealerHand);
        BlackjackGameRepository.updateGame(game);

        int playerScore = calculateHandValue(game.getPlayerHand());
        int dealerScore = calculateHandValue(dealerHand);

        if (dealerScore > 21 || playerScore > dealerScore) {
            endGame(userName, true);
        } else {
            endGame(userName, false);
        }

        int userBalance = UserRepository.getUserBalance(userName, false);
        BlackjackImageGenerator.generateBlackjackImage(userName, game.getPlayerHand(), dealerHand, "Game Over", userBalance);
        MessageService.sendMessageFromClipboard(false);
    }

    private static void endGame(String userName, boolean win) {
        BlackjackGame game = BlackjackGameRepository.getGameByUserName(userName);
        if (game == null) {
            return;
        }

        int userBalance = UserRepository.getUserBalance(userName, true);
        if (win) {
            int winnings = game.getBetAmount() * 2;
            UserRepository.updateUserBalance(userName, userBalance + winnings);
            MessageService.sendMessage(userName + " you won! Your new balance: " + (userBalance + winnings));
        } else {
            MessageService.sendMessage(userName + " you lost! Your new balance: " + userBalance);
        }

        BlackjackGameRepository.deleteGame(userName);
    }

    private static String drawCard() {
        int cardValue = (int) (Math.random() * 10) + 1;
        return String.valueOf(cardValue);
    }

    private static int calculateHandValue(List<String> hand) {
        return hand.stream().mapToInt(Integer::parseInt).sum();
    }

    private static String handToString(List<String> hand) {
        return String.join(", ", hand);
    }
}
