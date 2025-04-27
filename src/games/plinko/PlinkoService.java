package games.plinko;

import model.CommandContext;
import repository.GameHistoryRepository;
import repository.UserRepository;
import service.MessageService;

public class PlinkoService {
    
    public static void handlePlinkoCommand(CommandContext context) {
        String playerName = context.getUserName();
        String betAmount = context.getFirstArgument();
        String risk = context.getSecondArgument().toLowerCase();
        int betAmountParsed = parseBetAmount(betAmount);
        int currentBalance = UserRepository.getCurrentUserBalance(playerName, false);

        if (betAmountParsed == -1) return; 

        if (currentBalance < betAmountParsed) {
                MessageService.sendMessage("You can't afford it, your balance is: " + currentBalance);
                return;
            } 

        if (!risk.equals("low") && !risk.equals("l") && !risk.equals("medium") && !risk.equals("m") && !risk.equals("high") && !risk.equals("h")) {
                MessageService.sendMessage("Invalid game risk. Please choose from: low, medium, or high.");
                return;
            }  

        Double multiplier = PlinkoGifGenerator.playAndGenerateGif(playerName, betAmountParsed, currentBalance - betAmountParsed, risk);
        
        int resultAmount = ((int)(multiplier * betAmountParsed));

        GameHistoryRepository.addGameHistory(playerName, "Plinko", context.getFullCommand(), betAmountParsed, resultAmount, String.valueOf(multiplier));
        UserRepository.updateUserBalance(playerName, currentBalance - betAmountParsed + resultAmount);
        MessageService.sendMessageFromClipboardWindows(true);
    }

    public static int parseBetAmount(String betAmount) {
        try {
            int bet = Integer.parseInt(betAmount);
            if (bet <= 0) {
                MessageService.sendMessage("Bet must be greater than 0");
                return -1;
            }
            return bet;
        } catch (NumberFormatException e) {
            MessageService.sendMessage("Incorrect bet amount");
            return -1;
        }
    }

}
