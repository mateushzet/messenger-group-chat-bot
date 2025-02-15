package games.caseopening;

import model.CommandContext;
import repository.GameHistoryRepository;
import repository.UserRepository;
import service.MessageService;

public class CaseOpeningService {

    public static void handleCaseCommand(CommandContext context) {
        String userName = context.getUserName();
        String caseCostInput = context.getFirstArgument();

        int userBalance = UserRepository.getCurrentUserBalance(userName, true);

        try {
            if (!caseCostInput.equals("1000") && !caseCostInput.equals("100") && !caseCostInput.equals("10")) {
                MessageService.sendMessage(userName + ", you must choose which case to open: 1000 or 100 or 10");
                return;
            }

            int caseCost = Integer.parseInt(caseCostInput);

            int minPrice, maxPrice;
            if (caseCost == 100) {
                minPrice = 0;
                maxPrice = 1400;
            } else if (caseCost == 1000) {
                minPrice = 50;
                maxPrice = 13000;
            }else {
                minPrice = 0;
                maxPrice = 65;
            }

            if (userBalance < caseCost) {
                MessageService.sendMessage(userName + ", insufficient balance: " + userBalance + ", this case costs: " + caseCost);
                return;
            }

            userBalance -= caseCost;
            UserRepository.updateUserBalance(userName, userBalance);

            int winnings = CaseOpeningGifGenerator.generateCaseOpeningGif(userName, userBalance, minPrice, maxPrice);
            userBalance += winnings;
            UserRepository.updateUserBalance(userName, userBalance);

            GameHistoryRepository.addGameHistory(userName, "Case", context.getFullCommand(), caseCost, winnings, "");

            MessageService.sendMessageFromClipboard(true);

        } catch (Exception e) {
            MessageService.sendMessage(userName + ", error while processing command.");
            e.printStackTrace();
        }
    }
}