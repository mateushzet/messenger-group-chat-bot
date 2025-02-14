package games.horseRace;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import model.CommandContext;
import model.Horse;
import repository.GameHistoryRepository;
import repository.UserAvatarRepository;
import repository.UserRepository;
import service.MessageService;

public class HorseRaceBettingService {
    
    public static List<Horse> allHorses = new ArrayList<>();

    static {
        allHorses.add(new Horse("Thunderbolt", 23, 48, 0.09, 1));
        allHorses.add(new Horse("Lightning", 28, 45, 0.12, 2));
        allHorses.add(new Horse("Shadow", 24, 47, 0.01, 3));
        allHorses.add(new Horse("Blaze", 24, 49, 0.185, 4));
        allHorses.add(new Horse("Spirit", 28, 40, 0.075, 5));
        allHorses.add(new Horse("Flash", 20, 40, 0, 6));
        allHorses.add(new Horse("Storm", 32, 45, 0.385, 7));
        allHorses.add(new Horse("Comet", 36, 48, 0.325, 8));
        allHorses.add(new Horse("Fury", 32, 48, 0.25, 9));
    }

        public static void handleRaceCommand(CommandContext context) {
            String playerName = context.getUserName();
            String raceCommand = context.getFirstArgument();
            String betAmmount = context.getSecondArgument();
            String horseNumber = context.getThirdArgument();
         
            if(raceCommand.isEmpty() || (!raceCommand.equals("bet") && !raceCommand.equals("horses"))){
                MessageService.sendMessage("Avaiable race commands: /race horses,  /race bet <bet amount> <horse number>");
                return;
            }

            if(raceCommand.equals("bet")){
            int currentBalance = UserRepository.getCurrentUserBalance(playerName, false);
            int betAmountParesd = parseBetAmount(betAmmount);
            int horseNumberParesd = parseHorseNumber(horseNumber);

            if(betAmountParesd == -1 || horseNumberParesd == -1){
                MessageService.sendMessage("Invalid arguments. Please use /race bet <bet amount> <horse number>");
                return;
            }

            if (currentBalance < betAmountParesd) {
                MessageService.sendMessage("You can't afford the bet, current balance: %d", currentBalance);
                return;
            }        

            int UserBalance = UserRepository.getCurrentUserBalance(playerName, false);
            int newBalance = UserBalance - betAmountParesd;
            UserRepository.updateUserBalance(playerName, newBalance);

            int winner = HorseRaceService.generateFrames(horseNumberParesd, newBalance, betAmountParesd, playerName);
            UserBalance = UserRepository.getCurrentUserBalance(playerName, false);

            if(winner == horseNumberParesd){
                int winnings = betAmountParesd + (betAmountParesd * 5);
                UserRepository.updateUserBalance(playerName, UserBalance + winnings);
                //MessageService.sendMessage("#%d %s won, you earnd %d coins, current balance: %d", winner, horseName, winnings, UserBalance + winnings);
                GameHistoryRepository.addGameHistory(playerName, "Race", context.getFullCommand(), betAmountParesd, winnings, "Horse number " + winner + " won" );
                UserAvatarRepository.assignAvatarToUser(playerName, "horse");
            } else {
                //MessageService.sendMessage("#%d %s won, you lost %d coins, current balance: %d", winner, horseName, betAmountParesd, UserBalance);
                GameHistoryRepository.addGameHistory(playerName, "Race", context.getFullCommand(), betAmountParesd, -betAmountParesd, "Horse number " + winner + " won" );
            }
        }

        if(raceCommand.equals("horses")){
            try {
                HorseRaceImageGenerator.showHorses();
            } catch (IOException e) {
                MessageService.sendMessage("Error while loading horses images");
                e.printStackTrace();
            }
            MessageService.sendMessageFromClipboard(true);
        }

        }

        private static int parseBetAmount(String betAmount) {
            try {
                int parsedAmount = Integer.parseInt(betAmount);
                if (parsedAmount < 0) {
                    MessageService.sendMessage("Bet amount must be greater than 0");
                    return -1;
                }
                return parsedAmount;
            } catch (NumberFormatException e) {
                return -1;
            }
        }

        private static int parseHorseNumber(String betAmount) {
            try {
                int parsedAmount = Integer.parseInt(betAmount);
                if (parsedAmount < 0 || parsedAmount > 9) {
                    MessageService.sendMessage("Please chose horse number between 1 and 9");
                    return -1;
                }
                return parsedAmount;
            } catch (NumberFormatException e) {
                return -1;
            }
        }
}
