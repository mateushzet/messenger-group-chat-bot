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
    
        // Obliczanie sum punktów gracza i dealera
        int playerScore = calculateHandValue(playerHand);
        int dealerScore = calculateHandValue(dealerHand);
    
        // Przekazanie sum punktów do generatora obrazu
        BlackjackImageGenerator.generateBlackjackImage(userName, playerHand, dealerHand, userName + " game Started", userBalance, betAmount, false, playerScore, dealerScore);
        MessageService.sendMessageFromClipboard(true);
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
    
        int dealerScore = calculateHandValue(game.getDealerHand());
        int playerScore = calculateHandValue(playerHand);
        if ( playerScore > 21) {
            BlackjackGameRepository.updateGame(game);
            endGame(userName, false, playerScore, dealerScore);
            return;
        }
    
        int userBalance = UserRepository.getUserBalance(userName, false);
        BlackjackGameRepository.updateGame(game);
    
        BlackjackImageGenerator.generateBlackjackImage(userName, playerHand, game.getDealerHand(), userName + " you drew a card", userBalance, game.getBetAmount(), false, playerScore, 0);
        MessageService.sendMessageFromClipboard(true);
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
    
        String gameStatus;
        if (dealerScore > 21 || playerScore > dealerScore) {
            gameStatus = endGame(userName, true, playerScore, dealerScore);
        } else {
            gameStatus = endGame(userName, false, playerScore, dealerScore);
        }
    
        int userBalance = UserRepository.getUserBalance(userName, false);
    
        BlackjackImageGenerator.generateBlackjackImage(userName, game.getPlayerHand(), dealerHand, gameStatus, userBalance, game.getBetAmount(), true, playerScore, dealerScore);
        MessageService.sendMessageFromClipboard(true);
    }

    private static String endGame(String userName, boolean win, int playerScore, int dealerScore) {
        BlackjackGame game = BlackjackGameRepository.getGameByUserName(userName);
        if (game == null) {
            return null;
        }

        String gameStatus;
        int userBalance = UserRepository.getUserBalance(userName, true);
        if (win) {
            int winnings = game.getBetAmount() * 2;
            UserRepository.updateUserBalance(userName, userBalance + winnings);
            gameStatus = userName + "you won! Your new balance: " + (userBalance + winnings);
        } else {
            gameStatus = userName + " you lost! Your new balance: " + userBalance;
        }

        BlackjackGameRepository.deleteGame(userName);
        return gameStatus;
    }

    private static String drawCard() {
        String[] suits = {"♠", "♣", "♦", "♥"};
        int cardValue = (int) (Math.random() * 13) + 1;
        String suit = suits[(int) (Math.random() * suits.length)];
    
        String card;
        if (cardValue == 1) {
            card = "A" + suit;
        } else if (cardValue == 11) {
            card = "J" + suit;
        } else if (cardValue == 12) {
            card = "Q" + suit;
        } else if (cardValue == 13) {
            card = "K" + suit;
        } else {
            card = cardValue + suit;
        }
        
        return card;
    }

    private static int calculateHandValue(List<String> hand) {
        int value = 0;
        int aces = 0;
    
        for (String card : hand) {
            String cardValue = card.replaceAll("[♠♣♦♥]", "");
            if (cardValue.equals("A")) {
                aces++;
                value += 11;
            } else if (cardValue.equals("K") || cardValue.equals("Q") || cardValue.equals("J")) {
                value += 10;
            } else {
                value += Integer.parseInt(cardValue);
            }
        }
    
        while (value > 21 && aces > 0) {
            value -= 10;
            aces--;
        }
    
        return value;
    }

    private static String handToString(List<String> hand) {
        return String.join(", ", hand);
    }
}
