package service;

import java.util.Map;

import model.CommandContext;
import repository.UserRepository;

public class UserService {
    
    public static int validateAndParseBetAmount(String username, String betAmountString){
        int paresdBetAmount;
        int currentBalnace = UserRepository.getCurrentUserBalance(username, false);

        try {
            paresdBetAmount = Integer.parseInt(betAmountString);
        } catch (NumberFormatException e) {
            MessageService.sendMessage(username + " invalid bet amount format!");
            return -1;
        }

        if(paresdBetAmount <= 0){
            MessageService.sendMessage(username + " bet amount must be greater than 0!");
            return -1;
        }

        if(paresdBetAmount > currentBalnace){
            MessageService.sendMessage(username + " insufficient balance! Current balance: " + currentBalnace);
            return -1;
        }

        return paresdBetAmount;
    }

    public static int updateAndRetriveUserBalance(String username, int amount){
        int currentBalnace = UserRepository.getCurrentUserBalance(username, false);
        int newBalance = currentBalnace + amount;
        UserRepository.updateUserBalance(username, newBalance);
        return newBalance;
    }

    public static void handleBuyCommand(CommandContext context) {
        String playerName = context.getUserName();
        String firstArgument = context.getFirstArgument();

        if (firstArgument == null || firstArgument.isEmpty()) {
            MessageService.sendMessage(playerName + ", you must specify a game to buy access to.");
            return;
        }

        Map<String, Integer> gamePrices = Map.ofEntries(
            Map.entry("slots", 50),
            Map.entry("roulette", 50),
            Map.entry("blackjack", 50),
            Map.entry("plinko", 50),
            Map.entry("dice", 50),
            Map.entry("crash", 50),
            Map.entry("case", 50),
            Map.entry("colors", 50),
            Map.entry("mines", 50),
            Map.entry("lotto", 50),
            Map.entry("race", 50)
        );

        Integer gamePrice = gamePrices.get(firstArgument.toLowerCase());
        if (gamePrice == null) {
            MessageService.sendMessage(playerName + ", invalid game name.");
            return;
        }

        if (UserRepository.hasGameAccess(playerName, firstArgument)) {
            MessageService.sendMessage(playerName + ", you already have access to " + firstArgument + ".");
            return;
        }

        int currentBalance = UserRepository.getCurrentUserBalance(playerName, false);
        if (currentBalance < gamePrice) {
            MessageService.sendMessage(playerName + ", insufficient balance! You need " + gamePrice + " to buy access to " + firstArgument + ".");
            return;
        }

        int newBalance = currentBalance - gamePrice;
        UserRepository.updateUserBalance(playerName, newBalance);
        UserRepository.giveGameAccess(playerName, firstArgument);

        MessageService.sendMessage(playerName + ", you have successfully bought access to " + firstArgument + " for " + gamePrice + ". Your new balance is " + newBalance + ".");
    }

}
