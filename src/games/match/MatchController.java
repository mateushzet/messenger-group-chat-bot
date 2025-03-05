package games.match;

import model.CommandContext;
import service.MessageService;

public class MatchController {
    
   public static void handleSportsBettingCommand(CommandContext context) {
    String firstArgument = context.getFirstArgument();

    switch (firstArgument.toLowerCase()) {
        case "bet":
            SportsBettingService.placeBet(context);
            break;
                
        case "checkresults":
                SportsBettingService.showAllResults();
                SportsBettingService.checkAndPayOutBets(context);
                break;
            
        case "showmatches":
            SportsBettingService.showAllMatches();
            break;

        default:
            MessageService.sendMessage("Invalid command. Avaiable commands: /sports bet <bet amount> <match id> <outcome: home, away, draw>, /sports checkresults, /sports showmatches");
            break;
    }
}
}
