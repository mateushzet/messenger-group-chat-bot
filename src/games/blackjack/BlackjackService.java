package games.blackjack;

import model.BlackjackGame;
import model.CommandContext;
import repository.GameHistoryRepository;
import repository.UserAvatarRepository;
import repository.UserRepository;
import service.MessageService;
import service.UserService;

import java.util.ArrayList;
import java.util.List;

public class BlackjackService {

    public static void handleBlackjackCommand(CommandContext context) {
        String userName = context.getUserName();
        String firstArg = context.getFirstArgument();
        String secondArg = context.getSecondArgument();

        if (firstArg.equalsIgnoreCase("bet") || firstArg.equalsIgnoreCase("b")) {
            startGame(userName, secondArg, context);
            return;
        }

        if (firstArg.equalsIgnoreCase("hit") || firstArg.equalsIgnoreCase("h")) {
            hitCard(userName, context);
            return;
        }

        if (firstArg.equalsIgnoreCase("stand") || firstArg.equalsIgnoreCase("s")) {
            stand(userName, context);
            return;
        }

        String helpMessage = "/bot blackjack bet [bet amount]\n" +
                             "/bot blackjack hit\n" +
                             "/bot blackjack stand\n" +
                             "The goal is to get as close to 21 as possible without exceeding it.";
        MessageService.sendMessage(helpMessage);
        
    }

    private static void startGame(String userName, String betAmountArg, CommandContext context) {
        BlackjackGame existingGame = BlackjackGameRepository.getGameByUserName(userName);
        if (existingGame != null && existingGame.isGameInProgress()) {
            MessageService.sendMessage(userName + " you already have an active game. Finish that game before starting a new one.");
            return;
        }
    
        int betAmount = UserService.validateAndParseBetAmount(userName, betAmountArg);

        if (betAmount == -1) {
            return;
        }
        
        int userBalance = UserService.updateAndRetriveUserBalance(userName, -betAmount);

        List<String> playerHand = new ArrayList<>();
        List<String> dealerHand = new ArrayList<>();
    
        playerHand.add(drawCard());
        playerHand.add(drawCard());
        dealerHand.add(drawCard());
        dealerHand.add(drawCard());
        BlackjackGame game = new BlackjackGame(userName, betAmount, playerHand, dealerHand, true, userBalance);
        BlackjackGameRepository.saveGame(game);
    
        int playerScore = calculateHandValue(playerHand);
        int dealerScore = calculateSecondCardScore(dealerHand);
    
        if (playerScore == 21 ) {
            dealerScore = calculateHandValue(dealerHand);
            if(dealerScore != 21){
            int winnings = (int) (betAmount * 1.5);
            userBalance = UserService.updateAndRetriveUserBalance(userName, winnings);

            UserAvatarRepository.assignAvatarToUser(userName, "blackjack");

            String gameStatus = userName + " Blackjack! You won " + winnings + "!";
            GameHistoryRepository.addGameHistory(userName, "Blackjack", context.getFullCommand(), betAmount, winnings + betAmount, "Player hand: " + handToString(playerHand) + " Dealer hand: " + handToString(dealerHand));
            
            BlackjackImageGenerator.generateBlackjackImage(userName, playerHand, dealerHand, gameStatus, userBalance, betAmount, true, playerScore, dealerScore);
            MessageService.sendMessageFromClipboard(true);
            BlackjackGameRepository.deleteGame(userName);
            return;
            }
            else{
                String gameStatus = userName + " draw!";
                GameHistoryRepository.addGameHistory(userName, "Blackjack", context.getFullCommand(), betAmount, betAmount, "Player hand: " + handToString(playerHand) + " Dealer hand: " + handToString(dealerHand));
                
                userBalance = UserService.updateAndRetriveUserBalance(userName, betAmount);

                BlackjackImageGenerator.generateBlackjackImage(userName, playerHand, dealerHand, gameStatus, userBalance, betAmount, true, playerScore, dealerScore);
                MessageService.sendMessageFromClipboard(true);
                BlackjackGameRepository.deleteGame(userName);
            }
        }

        BlackjackImageGenerator.generateBlackjackImage(userName, playerHand, dealerHand, userName + " game started", userBalance, betAmount, false, playerScore, dealerScore);
        MessageService.sendMessageFromClipboard(true);
    }
    
    private static void hitCard(String userName, CommandContext context) {
        BlackjackGame game = BlackjackGameRepository.getGameByUserName(userName);
        if (game == null || !game.isGameInProgress()) {
            MessageService.sendMessage(userName + " no active game. Start a new game with /bot blackjack bet [bet amount].");
            return;
        }
    
        List<String> playerHand = game.getPlayerHand();
        playerHand.add(drawCard());
        game.setPlayerHand(playerHand);
    
        int dealerScore = calculateHandValue(game.getDealerHand());
        int playerScore = calculateHandValue(playerHand);
        int userBalance = UserRepository.getCurrentUserBalance(userName, false);
        if ( playerScore > 21) {
            BlackjackGameRepository.updateGame(game);
            endGame(userName, false, false, playerScore, dealerScore, context);
            BlackjackImageGenerator.generateBlackjackImage(userName, playerHand, game.getDealerHand(), userName + " you lost " + game.getBetAmount() + "!", userBalance, game.getBetAmount(), true, playerScore, 0);
            MessageService.sendMessageFromClipboard(true);
            return;
        }
    
        BlackjackGameRepository.updateGame(game);
        dealerScore = calculateSecondCardScore(game.getDealerHand());
        BlackjackImageGenerator.generateBlackjackImage(userName, playerHand, game.getDealerHand(), userName + " you drew a card", userBalance, game.getBetAmount(), false, playerScore, dealerScore);
        MessageService.sendMessageFromClipboard(true);
    }
    
    private static void stand(String userName, CommandContext context) {
        BlackjackGame game = BlackjackGameRepository.getGameByUserName(userName);
        if (game == null || !game.isGameInProgress()) {
            MessageService.sendMessage(userName + " no active game. Start a new game with /bot blackjack bet [bet amount].");
            return;
        }
    
        List<String> dealerHand = game.getDealerHand();
        int playerHand = calculateHandValue(game.getPlayerHand()) ;
        while (calculateHandValue(dealerHand) <= playerHand && calculateHandValue(dealerHand) != 21) {
            dealerHand.add(drawCard());
        }
    
        game.setDealerHand(dealerHand);
        BlackjackGameRepository.updateGame(game);
    
        int playerScore = calculateHandValue(game.getPlayerHand());
        int dealerScore = calculateHandValue(dealerHand);
    
        String gameStatus;
        if (playerScore == dealerScore){
            gameStatus = endGame(userName, true, true, playerScore, dealerScore, context);
        }
        else if (dealerScore > 21 || playerScore > dealerScore) {
            gameStatus = endGame(userName, true, false, playerScore, dealerScore, context);
        } else {
            gameStatus = endGame(userName, false, false, playerScore, dealerScore, context);
        }
    
        int userBalance = UserRepository.getCurrentUserBalance(userName, false);
    
        BlackjackImageGenerator.generateBlackjackImage(userName, game.getPlayerHand(), dealerHand, gameStatus, userBalance, game.getBetAmount(), true, playerScore, dealerScore);
        MessageService.sendMessageFromClipboard(true);
    }

    private static String endGame(String userName, boolean win, boolean draw, int playerScore, int dealerScore, CommandContext context) {
        BlackjackGame game = BlackjackGameRepository.getGameByUserName(userName);
        if (game == null) {
            return null;
        }

        String gameStatus;
        if (draw){
            int winnings = game.getBetAmount();
            UserService.updateAndRetriveUserBalance(userName, winnings);
            gameStatus = userName + " draw!";
            GameHistoryRepository.addGameHistory(userName, "Blackjack", context.getFullCommand(), game.getBetAmount(), winnings, "Player hand: " + handToString(game.getPlayerHand()) + " Dealer hand: " + handToString(game.getDealerHand()));
        }
        else if (win) {
            int winnings = game.getBetAmount() * 2;
            UserService.updateAndRetriveUserBalance(userName, winnings);
            gameStatus = userName + " you won " + game.getBetAmount() + "!";
            GameHistoryRepository.addGameHistory(userName, "Blackjack", context.getFullCommand(), game.getBetAmount(), winnings, "Player hand: " + handToString(game.getPlayerHand()) + " Dealer hand: " + handToString(game.getDealerHand()));
        } else {
            gameStatus = userName + " you lost " + game.getBetAmount() + "!";
            GameHistoryRepository.addGameHistory(userName, "Blackjack", context.getFullCommand(), game.getBetAmount(), -game.getBetAmount(), "Player hand: " + handToString(game.getPlayerHand()) + " Dealer hand: " + handToString(game.getDealerHand()));
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
            } else if (cardValue.equals("K") || cardValue.equals("Q") || cardValue.equals("J") || cardValue.equals("10")) {
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

    private static int calculateSecondCardScore(List<String> dealerHand) {
        List<String> handCopy = new ArrayList<>(dealerHand);
        
        if (handCopy.size() >= 2) {
            handCopy.remove(0);
            
            return calculateHandValue(handCopy);
        }
        
        return 0;
    }
    
}
