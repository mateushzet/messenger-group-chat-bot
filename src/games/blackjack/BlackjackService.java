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

        if (firstArg.equalsIgnoreCase("split") || firstArg.equalsIgnoreCase("sp")) {
            splitHand(userName, context);
            return;
        }

        if (firstArg.equalsIgnoreCase("double") || firstArg.equalsIgnoreCase("d")) {
            BlackjackGame existingGame = BlackjackGameRepository.getGameByUserName(userName);
            if (existingGame == null || !existingGame.isGameInProgress()) {
                MessageService.sendMessage(userName + " no active game. Start a new game with /bot blackjack bet [bet amount].");
                return;
            }

            if (existingGame.isSplit()) {
                MessageService.sendMessage(userName + " you can't double after split.");
                return;
            }

            if (existingGame.getPlayerHand().size() != 2) {
                MessageService.sendMessage(userName + " you can only double on your first two cards.");
                return;
            }
        
            int currentBet = existingGame.getCurrentBet();
            int userBalance = UserRepository.getCurrentUserBalance(userName, false);
        
            if (currentBet > userBalance) {
                MessageService.sendMessage(userName + " Insufficient balance for double. Current balance: " + userBalance + ", required amount: " + currentBet);
                return;
            }
        
            userBalance = UserService.updateAndRetriveUserBalance(userName, -currentBet);
            existingGame.setCurrentBet(currentBet * 2);
        
            existingGame.getPlayerHand().add(drawCard());
        
            int playerScore = calculateHandValue(existingGame.getPlayerHand());
            String playerScoreString = calculateHandValueString(existingGame.getPlayerHand());

            int dealerScore = calculateSecondCardScore(existingGame.getDealerHand());
            String dealerScoreString = calculateSecondCardScoreString(existingGame.getDealerHand());

            BlackjackGameRepository.updateGame(existingGame);

            if (playerScore > 21) {
                endGame(userName, false, false, playerScore, dealerScore, context);
                BlackjackImageGenerator.generateBlackjackImage(userName, existingGame.getPlayerHand(), existingGame.getDealerHand(), userName + " you lost " + existingGame.getCurrentBet() + "!", userBalance, existingGame.getCurrentBet(), true, playerScoreString, dealerScoreString);
                MessageService.sendMessageFromClipboard(true);
                BlackjackGameRepository.deleteGame(userName);
                return;
            }
        
            stand(userName, context);
            return;
        }

        String helpMessage = "/bot blackjack bet [bet amount]\n" +
                             "/bot blackjack hit\n" +
                             "/bot blackjack stand\n" +
                             "/bot blackjack split\n" +
                             "The goal is to get as close to 21 as possible without exceeding it.";
        MessageService.sendMessage(helpMessage);
    }

    private static void startGame(String userName, String betAmountArg, CommandContext context) {
        BlackjackGame existingGame = BlackjackGameRepository.getGameByUserName(userName);
        if (existingGame != null && existingGame.isGameInProgress()) {

            int userBalance = UserRepository.getCurrentUserBalance(userName, false);
            String playerScore = calculateHandValueString(existingGame.getPlayerHand());
            String dealerScore = calculateSecondCardScoreString(existingGame.getDealerHand());
    
            BlackjackImageGenerator.generateBlackjackImage(
                userName,
                existingGame.getPlayerHand(),
                existingGame.getDealerHand(),
                userName + " you already have an active game.",
                userBalance,
                existingGame.getBetAmount(),
                false,
                playerScore,
                dealerScore
            );
    
            MessageService.sendMessageFromClipboard(true);
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
    
        String playerScoreString = calculateHandValueString(playerHand);
        String dealerScoreString = calculateSecondCardScoreString(dealerHand);

        if (playerScore == 21 ) {
            dealerScore = calculateHandValue(dealerHand);
            if(dealerScore != 21){
            int winnings = (int) (betAmount * 2.5);
            userBalance = UserService.updateAndRetriveUserBalance(userName, winnings);

            UserAvatarRepository.assignAvatarToUser(userName, "blackjack");

            String gameStatus = userName + " Blackjack! You won " + winnings + "!";
            GameHistoryRepository.addGameHistory(userName, "Blackjack", context.getFullCommand(), betAmount, winnings, "Player hand: " + handToString(playerHand) + " Dealer hand: " + handToString(dealerHand));
            
            BlackjackImageGenerator.generateBlackjackImage(userName, playerHand, dealerHand, gameStatus, userBalance, betAmount, true, playerScoreString, dealerScoreString);
            MessageService.sendMessageFromClipboard(true);
            BlackjackGameRepository.deleteGame(userName);
            return;
            }
            else{
                String gameStatus = userName + " draw!";
                GameHistoryRepository.addGameHistory(userName, "Blackjack", context.getFullCommand(), betAmount, betAmount, "Player hand: " + handToString(playerHand) + " Dealer hand: " + handToString(dealerHand));
                
                userBalance = UserService.updateAndRetriveUserBalance(userName, betAmount);

                BlackjackImageGenerator.generateBlackjackImage(userName, playerHand, dealerHand, gameStatus, userBalance, betAmount, true, playerScoreString, dealerScoreString);
                MessageService.sendMessageFromClipboard(true);
                BlackjackGameRepository.deleteGame(userName);
            }
        }

        BlackjackImageGenerator.generateBlackjackImage(userName, playerHand, dealerHand, userName + " game started", userBalance, betAmount, false, playerScoreString, dealerScoreString);
        MessageService.sendMessageFromClipboard(true);
    }
    
    private static boolean hitCard(String userName, CommandContext context) {
        BlackjackGame game = BlackjackGameRepository.getGameByUserName(userName);
        if (game == null || !game.isGameInProgress()) {
            MessageService.sendMessage(userName + " no active game. Start a new game with /bot blackjack bet [bet amount].");
            return false;
        }
    
        boolean isSplit = game.isSplit();
        List<String> activeHand = game.getPlayerHand();
    
        if (isSplit) {
            String handToHit = context.getSecondArgument(); 
            if (handToHit == null || (!handToHit.equals("1") && !handToHit.equals("2"))) {
                MessageService.sendMessage(userName + " choose which hand to hit: /bj hit 1 or /bj hit 2");
                return true;
            }
            if (handToHit.equals("2")) {
                activeHand = game.getSplitHand();
            }
        }

        activeHand.add(drawCard());
    
        int dealerScore = calculateHandValue(game.getDealerHand());
        int playerScore = calculateHandValue(activeHand);

        String dealerScoreString = calculateHandValueString(game.getDealerHand());
        String playerScoreString = calculateHandValueString(activeHand);

        int userBalance = UserRepository.getCurrentUserBalance(userName, false);
    
        if (playerScore > 21) {
            BlackjackGameRepository.updateGame(game);
            endGame(userName, false, false, playerScore, dealerScore, context);
            BlackjackImageGenerator.generateBlackjackImage(userName, activeHand, game.getDealerHand(), userName + " you lost " + game.getBetAmount() + "!", userBalance, game.getBetAmount(), true, playerScoreString, dealerScoreString);
            MessageService.sendMessageFromClipboard(true);
            if (!isSplit) BlackjackGameRepository.deleteGame(userName);
            return false;
        }
    
        BlackjackGameRepository.updateGame(game);
        dealerScoreString = calculateSecondCardScoreString(game.getDealerHand());
        BlackjackImageGenerator.generateBlackjackImage(userName, activeHand, game.getDealerHand(), userName + " you drew a card", userBalance, game.getBetAmount(), false, playerScoreString, dealerScoreString);
        MessageService.sendMessageFromClipboard(true);
        return true;
    }
    
    private static void stand(String userName, CommandContext context) {
        BlackjackGame game = BlackjackGameRepository.getGameByUserName(userName);
        if (game == null || !game.isGameInProgress()) {
            MessageService.sendMessage(userName + " no active game. Start a new game with /bot blackjack bet [bet amount].");
            return;
        }
    
        List<String> dealerHand = game.getDealerHand();
        int playerScore = calculateHandValue(game.getPlayerHand());
        int splitScore = game.isSplit() ? calculateHandValue(game.getSplitHand()) : 0;

        String playerScoreString = calculateHandValueString(game.getPlayerHand());
        String splitScoreString = game.isSplit() ? calculateHandValueString(game.getSplitHand()) : "0";

        while (calculateHandValue(dealerHand) < 17) {
            dealerHand.add(drawCard());
        }
    
        game.setDealerHand(dealerHand);
        BlackjackGameRepository.updateGame(game);
    
        int dealerScore = calculateHandValue(dealerHand);
        String dealerScoreString = calculateHandValueString(dealerHand);
        int userBalance;
        String gameStatusMain = resolveGame(userName, playerScore, dealerScore, context, game.getPlayerHand(), game.getBetAmount());
    
        if (game.isSplit()) {
            String gameStatusSplit = resolveGame(userName, splitScore, dealerScore, context, game.getSplitHand(), game.getBetAmount());
            userBalance = UserRepository.getCurrentUserBalance(userName, false);
            BlackjackImageGenerator.generateBlackjackImage(userName, game.getSplitHand(), dealerHand, gameStatusSplit, userBalance, game.getBetAmount(), true, splitScoreString, dealerScoreString);
            MessageService.sendMessageFromClipboard(true);
        }
    
        userBalance = UserRepository.getCurrentUserBalance(userName, false);
        BlackjackImageGenerator.generateBlackjackImage(userName, game.getPlayerHand(), dealerHand, gameStatusMain, userBalance, game.getBetAmount(), true, playerScoreString, dealerScoreString);
        MessageService.sendMessageFromClipboard(true);
    
        BlackjackGameRepository.deleteGame(userName);
    }
    
    private static String resolveGame(String userName, int playerScore, int dealerScore, CommandContext context, List<String> hand, int betAmount) {
        BlackjackGame game = BlackjackGameRepository.getGameByUserName(userName);
        if (game == null) {
            return userName + " game not found. Please start a new game.";
        }
    
        String gameStatus;
        if (playerScore == dealerScore && playerScore <= 21) {
            int winnings = betAmount;
            UserService.updateAndRetriveUserBalance(userName, winnings);
            gameStatus = userName + " draw!";
            GameHistoryRepository.addGameHistory(userName, "Blackjack", context.getFullCommand(), betAmount, winnings, "Player hand: " + handToString(hand) + " Dealer hand: " + handToString(game.getDealerHand()));
        } else if (game.isSplit() && playerScore == 21){
            int winnings = (int) (betAmount * 2.5);
            UserService.updateAndRetriveUserBalance(userName, winnings);
            UserAvatarRepository.assignAvatarToUser(userName, "blackjack");
            gameStatus = userName + " Blackjack! You won " + winnings + "!";
            GameHistoryRepository.addGameHistory(userName, "Blackjack", context.getFullCommand(), betAmount, winnings, "Player hand: " + handToString(hand) + " Dealer hand: " + handToString(game.getDealerHand()));
        } else if ((dealerScore > 21 || playerScore > dealerScore) && playerScore <= 21) {
            int winnings = (int) (betAmount * 2);
            UserService.updateAndRetriveUserBalance(userName, winnings);
            gameStatus = userName + " you won " + betAmount + "!";
            GameHistoryRepository.addGameHistory(userName, "Blackjack", context.getFullCommand(), betAmount, winnings, "Player hand: " + handToString(hand) + " Dealer hand: " + handToString(game.getDealerHand()));
        } else {
            gameStatus = userName + " you lost " + betAmount + "!";
            GameHistoryRepository.addGameHistory(userName, "Blackjack", context.getFullCommand(), betAmount, -betAmount, "Player hand: " + handToString(hand) + " Dealer hand: " + handToString(game.getDealerHand()));
        }
    
        return gameStatus;
    }
    

    private static String endGame(String userName, boolean win, boolean draw, int playerScore, int dealerScore, CommandContext context) {
        BlackjackGame game = BlackjackGameRepository.getGameByUserName(userName);
        if (game == null) {
            return userName + " game not found. Please start a new game.";
        }
    
        String gameStatus;
        if (draw) {
            int winnings = game.getBetAmount();
            UserService.updateAndRetriveUserBalance(userName, winnings);
            gameStatus = userName + " draw!";
            GameHistoryRepository.addGameHistory(userName, "Blackjack", context.getFullCommand(), game.getBetAmount(), winnings, "Player hand: " + handToString(game.getPlayerHand()) + " Dealer hand: " + handToString(game.getDealerHand()));
        } else if (win) {
            int winnings = game.getBetAmount() * 2;
            UserService.updateAndRetriveUserBalance(userName, winnings);
            gameStatus = userName + " you won " + game.getBetAmount() + "!";
            GameHistoryRepository.addGameHistory(userName, "Blackjack", context.getFullCommand(), game.getBetAmount(), winnings, "Player hand: " + handToString(game.getPlayerHand()) + " Dealer hand: " + handToString(game.getDealerHand()));
        } else {
            gameStatus = userName + " you lost " + game.getBetAmount() + "!";
            GameHistoryRepository.addGameHistory(userName, "Blackjack", context.getFullCommand(), game.getBetAmount(), -game.getBetAmount(), "Player hand: " + handToString(game.getPlayerHand()) + " Dealer hand: " + handToString(game.getDealerHand()));
        }
    
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

    private static String calculateHandValueString(List<String> hand) {
        int value = 0;
        int aces = 0;

        for (String card : hand) {
            String cardValue = card.replaceAll("[♠♣♦♥]", "");
            if (cardValue.equals("A")) {
                aces++;
                value += 1;
            } else if (cardValue.equals("K") || cardValue.equals("Q") || cardValue.equals("J") || cardValue.equals("10")) {
                value += 10;
            } else {
                value += Integer.parseInt(cardValue);
            }
        }

        int softValue = value;
        if (aces > 0 && softValue + 10 <= 21) {
            softValue += 10;
        }

        if (softValue > 21) {
            return String.valueOf(value);
        }

        if (aces > 0 && softValue != value) {
            return value + "/" + softValue;
        } else {
            return String.valueOf(value);
        }
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

    private static String calculateSecondCardScoreString(List<String> dealerHand) {
        List<String> handCopy = new ArrayList<>(dealerHand);
        
        if (handCopy.size() >= 2) {
            handCopy.remove(0);
            
            return calculateHandValueString(handCopy);
        }
        
        return "0";
    }

    private static void splitHand(String userName, CommandContext context) {
        BlackjackGame game = BlackjackGameRepository.getGameByUserName(userName);
        if (game == null || !game.isGameInProgress()) {
            MessageService.sendMessage(userName + " no active game. Start a new game with /bot blackjack bet [bet amount].");
            return;
        }
    
        if (!game.canSplit()) {
            MessageService.sendMessage(userName + " you cannot split your hand.");
            return;
        }
    
        int userBalance = UserRepository.getCurrentUserBalance(userName, false);
        int betAmount = game.getBetAmount();
        if (userBalance < betAmount) {
            MessageService.sendMessage(userName + " you do not have enough balance to split. Additional bet required: " + betAmount);
            return;
        }
    
        userBalance = UserService.updateAndRetriveUserBalance(userName, -betAmount);
    
        game.split();
        game.getPlayerHand().add(drawCard());
        game.getSplitHand().add(drawCard());
        BlackjackGameRepository.updateGame(game);
        String playerScore1 = calculateHandValueString(game.getPlayerHand());
        String playerScore2 = calculateHandValueString(game.getSplitHand());
        String dealerScore = calculateSecondCardScoreString(game.getDealerHand());
    
        BlackjackImageGenerator.generateBlackjackImage(userName, game.getPlayerHand(), game.getDealerHand(), userName + " split hand 1", userBalance, betAmount, false, playerScore1, dealerScore);
        MessageService.sendMessageFromClipboard(true);
        BlackjackImageGenerator.generateBlackjackImage(userName, game.getSplitHand(), game.getDealerHand(), userName + " split hand 2", userBalance, betAmount, false, playerScore2, dealerScore);
        MessageService.sendMessageFromClipboard(true);
        MessageService.sendMessage(userName + "choose which hand to hit: /bj hit 1 or /bj hit 2. At the end confirm both hands with /bj stand");
    }
    
}
