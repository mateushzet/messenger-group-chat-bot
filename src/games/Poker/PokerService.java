package games.Poker;

import model.CommandContext;
import service.MessageService;

public class PokerService {
    
        public static void handlePokerCommand(CommandContext context) {
        String userName = context.getUserName();
        String firstArg = context.getFirstArgument();
        String secondArg = context.getSecondArgument();

        if (firstArg.equalsIgnoreCase("start") || firstArg.equalsIgnoreCase("s")) {
            startGame(userName, secondArg, context);
            return;
        }

        if (firstArg.equalsIgnoreCase("check") || firstArg.equalsIgnoreCase("ch")) {
            check(userName, context);
            return;
        }

        if (firstArg.equalsIgnoreCase("call") || firstArg.equalsIgnoreCase("c")) {
            call(userName, context);
            return;
        }

        if (firstArg.equalsIgnoreCase("raise") || firstArg.equalsIgnoreCase("r")) {
            raise(userName, context);
            return;
        }

        String helpMessage = "/bot poker start [bet amount]\n" +
                             "/bot poker check\n" +
                             "/bot poker call\n" +
                             "/bot poker raise";
        MessageService.sendMessage(helpMessage);
    }

    private static void startGame(String userName, String secondArg, CommandContext context) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'startGame'");
    }    

    private static void check(String userName, CommandContext context) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'check'");
    }

    private static void call(String userName, CommandContext context) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'call'");
    }
    
    private static void raise(String userName, CommandContext context) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'raise'");
    }

}
