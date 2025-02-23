package games.jackpot;

import model.CommandContext;
import repository.UserRepository;
import service.MessageService;
import service.UserService;
import utils.ImageUtils;

import java.io.IOException;
import java.sql.Timestamp;

public class JackpotService {

    public static void handleJackpotCommand(CommandContext context) {
        String playerName = context.getUserName();
        String betAmount = context.getFirstArgument();

        int parsedBetAmount = UserService.validateAndParseBetAmount(playerName, betAmount);
        if (parsedBetAmount == -1) return;

        int userBalance = UserRepository.getCurrentUserBalance(playerName, false);

        UserRepository.updateUserBalance(playerName, userBalance - parsedBetAmount);

        Timestamp timestamp = new Timestamp(System.currentTimeMillis());
        JackpotGameRepository.addJackpotBet(playerName, betAmount, timestamp);

        MessageService.sendMessage(playerName + " successfully joined the jackpot game with a bet of " + parsedBetAmount + ". The game will start in 10 minutes.");
    }

    public static void startJackpotGame() {

        JackpotResult result;
        try {
            result = JackpotGifGenerator.generateJackpotGif();
        
        if (result.getGifBytes() != null) {
            ImageUtils.setClipboardGif(result.getGifBytes());
        } else {
            MessageService.sendMessage("Error while starting jackpot game!");
            return;
        }
        int winnerBalance = UserRepository.getCurrentUserBalance(result.getWinnerName(), false);
        UserRepository.updateUserBalance(result.getWinnerName(), winnerBalance + result.getPrizeAmount());
        JackpotGameRepository.deleteAllJackpotBets();
        MessageService.sendMessageFromClipboard(false);
        } catch (IOException e) {
            MessageService.sendMessage("Error while starting jackpot game!");
            e.printStackTrace();
        }
        return;
    }

    public static boolean hasTenMinutesPassedSinceOldestTimestamp() {
        Timestamp oldestTimestamp = JackpotGameRepository.getOldestTimestamp();
        if (oldestTimestamp == null) {
            return false;
        }

        long currentTimeMillis = System.currentTimeMillis();
        long oldestTimestampMillis = oldestTimestamp.getTime();

        long timeDifferenceMillis = currentTimeMillis - oldestTimestampMillis;

        return timeDifferenceMillis >= 600_000;
    }

}