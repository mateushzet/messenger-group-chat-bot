package service;

import model.CommandContext;
import repository.UserRepository;
import utils.Logger;
import utils.PlinkoGifGenerator;

public class PlinkoService {
    
    public static void handlePlinkoCommand(CommandContext context) {
        String playerName = context.getUserName();
        String betAmount = context.getFirstArgument();
        int betAmountParsed = parseBetAmount(betAmount);
        int currentBalance = UserRepository.getUserBalance(playerName, false);

        if (betAmountParsed <= 0) {
                MessageService.sendMessage("Invalid bet amount");
                Logger.logInfo("Player %s attempted to place a bet of %d coins", "LottoService.HandlePlinkoCommand()", playerName, betAmountParsed);
                return;
            }   

        if (currentBalance < betAmountParsed) {
                MessageService.sendMessage("You can't afford it, your balance is: %d", currentBalance);
                Logger.logInfo("Player %s can't afford the bet. Current balance: %d", "SlotsService.HandlePlinkoCommand()", playerName, currentBalance);
                return;
            } 

        Double multiplier = PlinkoGifGenerator.playAndGenerateGif(playerName, betAmountParsed, currentBalance - betAmountParsed);
        
        UserRepository.updateUserBalance(playerName, (currentBalance - betAmountParsed) + ((int)(multiplier * betAmountParsed)));
        MessageService.sendMessageFromClipboard(true);
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
