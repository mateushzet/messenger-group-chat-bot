package controller;

import model.CommandContext;
import service.MessageService;
import service.SportsBettingService;

public class MatchController {
    
   public static void handleSportsBettingCommand(CommandContext context) {
    String firstArgument = context.getFirstArgument();

    switch (firstArgument.toLowerCase()) {
        case "bet":
            SportsBettingService.placeBet(context);
            break;
                
        case "checkresults":
                SportsBettingService.showAllResults(context);
                SportsBettingService.checkAndPayOutBets(context);
                break;
            
        case "showmatches":
            SportsBettingService.showAllMatches(context);
            break;

        default:
            MessageService.sendMessage("Invalid command. Please try again with a valid command.");
            break;
    }
}
}
