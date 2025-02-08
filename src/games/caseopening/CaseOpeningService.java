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
            if (!caseCostInput.equals("200") && !caseCostInput.equals("150")) {
                MessageService.sendMessage(userName + " you must choose which case to open: 200 (StatTraks included) or 150 (no StatTraks)");
                return;
            }

            int caseCost = Integer.parseInt(caseCostInput);
            boolean isStatTrak = caseCost == 200;

            if (userBalance < caseCost) {
                MessageService.sendMessage(userName + " insufficient balance: " + userBalance + ", this case costs: " + caseCost);
                return;
            }

            userBalance -= caseCost;
            UserRepository.updateUserBalance(userName, userBalance);

            int winnings = CaseOpeningGifGenerator.generateCaseOpeningGif(userName, userBalance, isStatTrak);
            userBalance += winnings;
            UserRepository.updateUserBalance(userName, userBalance);

            GameHistoryRepository.addGameHistory(userName, "Case", context.getFullCommand(), caseCost, winnings, "");
            MessageService.sendMessageFromClipboard(true);

        } catch (Exception e) {
            MessageService.sendMessage(userName + " error while processing command");
            e.printStackTrace();
        }
    }
}