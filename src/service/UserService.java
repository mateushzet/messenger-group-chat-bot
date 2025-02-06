package service;

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
}
