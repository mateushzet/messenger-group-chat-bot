package games.caseopening;

import model.CommandContext;
import repository.GameHistoryRepository;
import repository.UserRepository;
import service.MessageService;

public class CaseOpeningService {

    private static final int CASE_COST = 100;

    public static void handleCaseCommand(CommandContext context) {
        String userName = context.getUserName();
        int userBalance = UserRepository.getCurrentUserBalance(userName, true);

        try {
            if (userBalance < CASE_COST) {
                MessageService.sendMessage(userName + " insufficient balance: " + userBalance + ", this case costs: " + CASE_COST);
                return;
            }

            userBalance -= CASE_COST;
            UserRepository.updateUserBalance(userName, userBalance);

            int winnings = CaseOpeningGifGenerator.generateCaseOpeningGif(userName, userBalance);
            userBalance += winnings;
            UserRepository.updateUserBalance(userName, userBalance);

            GameHistoryRepository.addGameHistory(userName, "Case", context.getFullCommand(), CASE_COST, winnings, "");
            MessageService.sendMessageFromClipboard(true);

        } catch (Exception e) {
            MessageService.sendMessage(userName + " error while processing command");
            e.printStackTrace();
        }
    }
}