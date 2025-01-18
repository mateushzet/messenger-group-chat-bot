package service;

import java.io.IOException;

import model.CommandContext;
import repository.UserRepository;
import utils.HorseRaceImageGenerator;

public class HorseRaceBettingService {
    
        public static void handleRaceCommand(CommandContext context) {
            String playerName = context.getUserName();
            String raceCommand = context.getFirstArgument();
            String betAmmount = context.getSecondArgument();
            String horseNumber = context.getThirdArgument();


            if(raceCommand.equals("bet")){
            int currentBalance = UserRepository.getUserBalance(playerName, false);
            int betAmountParesd = parseBetAmount(betAmmount);
            int horseNumberParesd = parseHorseNumber(horseNumber);

            if (currentBalance < betAmountParesd) {
                MessageService.sendMessage("You can't afford the bet, current balance: %d", currentBalance);
                return;
            }        

            int UserBalance = UserRepository.getUserBalance(playerName, false);
            int newBalance = UserBalance - betAmountParesd;
            UserRepository.updateUserBalance(playerName, newBalance);

            int winner = HorseRaceService.startRace(horseNumberParesd);
            UserBalance = UserRepository.getUserBalance(playerName, false);
            if(winner == horseNumberParesd){
                int winnings = betAmountParesd * 6;
                UserRepository.updateUserBalance(playerName, UserBalance + winnings);
                MessageService.sendMessage("Horse number %d won, you earnd %d coins, current balance: %d", winner, winnings, UserBalance + winnings);
            } else {
                MessageService.sendMessage("Horse number %d won, you lost %d coins, current balance: %d", winner, betAmountParesd, UserBalance);
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
                    throw new NumberFormatException("Bet amount must be greater than 0");
                }
                return parsedAmount;
            } catch (NumberFormatException e) {
                return Integer.MIN_VALUE;
            }
        }

        private static int parseHorseNumber(String betAmount) {
            try {
                int parsedAmount = Integer.parseInt(betAmount);
                if (parsedAmount < 0 || parsedAmount > 9) {
                    throw new NumberFormatException("Please chose horse number between 1 and 9");
                }
                return parsedAmount;
            } catch (NumberFormatException e) {
                return Integer.MIN_VALUE;
            }
        }
}
