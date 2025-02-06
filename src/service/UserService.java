package service;

import repository.UserRepository;

public class UserService {
    
    public static boolean validateBetAmount(String username, String betAmountString){
        int paresdBetAmount;
        int currentBalnace = UserRepository.getCurrentUserBalance(username, false);

        try {
            paresdBetAmount = Integer.parseInt(betAmountString);
        } catch (NumberFormatException e) {
            MessageService.sendMessage(username + " invalid bet amount format!");
            return false;
        }

        if(paresdBetAmount <= 0){
            MessageService.sendMessage(username + " bet amount must be greater than 0!");
            return false;
        }

        if(paresdBetAmount < currentBalnace){
            MessageService.sendMessage(username + " insufficient balance! Current balance: " + currentBalnace);
            return false;
        }

        return true;
    }

    public static int updateAndRetriveUserBalance(String username, int amount){
        int currentBalnace = UserRepository.getCurrentUserBalance(username, false);
        int newBalance = currentBalnace + amount;
        UserRepository.updateUserBalance(username, newBalance);
        return newBalance;
    }
}
