package games.caseopening;

import model.CommandContext;
import repository.UserRepository;
import service.MessageService;

public class CaseOpeningService {

    public static void handleCaseCommand(CommandContext context) {
        String userName = context.getUserName();
        String stattrak = context.getFirstArgument();

        int userBalance = UserRepository.getCurrentUserBalance(userName, true);

        try {
            boolean isStatTrak = stattrak.equalsIgnoreCase("stattrak") || stattrak.equalsIgnoreCase("s");
            int caseCost = isStatTrak ? 230 : 190;

            if (userBalance < caseCost) {
                MessageService.sendMessage(userName + " insufficient balance: " + userBalance + ", this case costs: " + caseCost);
                return;
            }

            userBalance -= caseCost;
            UserRepository.updateUserBalance(userName, userBalance);

            int winnings = CaseOpeningGifGenerator.generateCaseOpeningGif(userName, userBalance, isStatTrak);
            userBalance += winnings;
            UserRepository.updateUserBalance(userName, userBalance);

            MessageService.sendMessageFromClipboard(true);

        } catch (Exception e) {
            MessageService.sendMessage(userName + " error while processing command");
            e.printStackTrace();
        }
    }
}