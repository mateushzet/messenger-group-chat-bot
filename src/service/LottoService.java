package service;

import java.time.LocalDateTime;
import java.util.Random;

import model.CommandContext;
import repository.GameHistoryRepository;
import repository.UserRepository;
import utils.Logger;
import utils.LottoImageGenerator;

public class LottoService {

    private static final int LOTTO_NUMBERS = 6;
    private static final int MAX_NUMBER = 49;

    public static void handleLottoCommand(CommandContext context) {
        String playerName = context.getUserName();
        String betAmount = context.getFirstArgument();
        String numbers = context.getSecondArgument();
        int betAmountParsed;

        if (betAmount.isEmpty()) {
            MessageService.sendMessage("Avaiable lotto commands: lotto <betAmount> <num1,num2,num3,num4,num5,num6>");
            return;
        }

        if(validateAndParseNumbers(numbers) == null){
            return;
        }
        betAmountParsed = parseBetAmount(betAmount);
        if(betAmountParsed == -1) return;
        int currentBalance = UserRepository.getUserBalance(playerName, false);

        if (currentBalance < betAmountParsed) {
            MessageService.sendMessage("You don't have enough coins. Your balance: %d", currentBalance);
            return;
        }

        int[] playerNumbers = validateAndParseNumbers(numbers);

        playLotto(playerName, playerNumbers, currentBalance, betAmountParsed);
    }

    private static void playLotto(String playerName, int[] playerNumbers, int currentBalance, int betAmount) {
        int newBalance = currentBalance - betAmount;
        UserRepository.updateUserBalance(playerName, newBalance);
        Logger.logInfo("%s placed a Lotto bet. New balance: %d", "LottoService.playLotto()", playerName, newBalance);
    
        int[] winningNumbers = generateWinningNumbers();
        int matches = countMatches(playerNumbers, winningNumbers);
        int prizePool = getPrizePool();

        int winnings = calculateWinnings(matches, betAmount, prizePool);
        newBalance += winnings;
        UserRepository.updateUserBalance(playerName, newBalance);
    
        if (winnings > 0) {
            Logger.logInfo("%s won %d coins in Lotto. New balance: %d", "LottoService.playLotto()", playerName, winnings, newBalance);
        } else {
            Logger.logInfo("%s did not win in Lotto. New balance: %d", "LottoService.playLotto()", playerName, newBalance);
        }

        LottoImageGenerator.drawLottoResults(winningNumbers, playerNumbers, winnings, betAmount, newBalance, playerName, prizePool);
        MessageService.sendMessageFromClipboard(true);
    
        GameHistoryRepository.addGameHistory(playerName, "Lotto", arrayToString(playerNumbers), betAmount, winnings, "Winning Numbers: " + arrayToString(winningNumbers));
    }
    
    private static String arrayToString(int[] array) {
        StringBuilder sb = new StringBuilder();
        for (int num : array) {
            sb.append(num).append(" ");
        }
        return sb.toString().trim();
    }


    private static int[] generateWinningNumbers() {
        Random rand = new Random();
        int[] winningNumbers = new int[LOTTO_NUMBERS];
        int count = 0;
        
        while (count < LOTTO_NUMBERS) {
            int num = rand.nextInt(MAX_NUMBER) + 1;
            boolean isUnique = true;
    
            for (int i = 0; i < count; i++) {
                if (winningNumbers[i] == num) {
                    isUnique = false;
                    break;
                }
            }
    
            if (isUnique) {
                winningNumbers[count] = num;
                count++;
            }
        }
        return winningNumbers;
    }

    private static int countMatches(int[] playerNumbers, int[] winningNumbers) {
        int matches = 0;
        for (int playerNum : playerNumbers) {
            for (int winningNum : winningNumbers) {
                if (playerNum == winningNum) {
                    matches++;
                }
            }
        }
        return matches;
    }

    private static int calculateWinnings(int matches, int betAmount, int prizePool) {
        switch (matches) {
            case 1:
                return (int) (2 * betAmount);
            case 2:
                return (int) (8 * betAmount);
            case 3:
                return (int) (57 * betAmount);
            case 4:
                return (int) (0.0002 * prizePool);
            case 5:
                return (int) (0.01 * prizePool);
            case 6:
                return (int) (0.5 * prizePool);
            default:
                return 1;
        }
    }

    public static int getPrizePool() {

        LocalDateTime currentDate = LocalDateTime.now();
        
        int hashValue = currentDate.hashCode();
        
        Random random = new Random(hashValue);
        
        int prizePool = random.nextInt(18000000) + 2000000;
        
        prizePool = (prizePool / 1000) * 1000;
        
        return prizePool;
    }

    public static int[] validateAndParseNumbers(String numbers) {
        numbers = numbers.trim();
        
        String[] parts = numbers.split(",");
        
        if (parts.length != 6) {
            MessageService.sendMessage("You must provide exactly 6 numbers.");
            return null;
        }
        
        int[] parsedNumbers = new int[6];
        
        try {
            for (int i = 0; i < parts.length; i++) {
                int num = Integer.parseInt(parts[i].trim());
                

                if (num < 1 || num > 49) {
                    MessageService.sendMessage("Each number must be between 1 and 49.");
                    return null;
                }
                
                for (int j = 0; j < i; j++) {
                    if (parsedNumbers[j] == num) {
                        MessageService.sendMessage("Duplicate numbers are not allowed.");
                        return null;
                    }
                }
                
                parsedNumbers[i] = num;
            }
        } catch (NumberFormatException e) {
            MessageService.sendMessage("Invalid numbers");
            return null;
        }
        
        return parsedNumbers;
    }

    public static int parseBetAmount(String betAmount) {
        try {
            int bet = Integer.parseInt(betAmount);
            if (bet <= 0) {
                MessageService.sendMessage("Bet must be greater than 0");
                return -1;
            }
            return bet;
        } catch (NumberFormatException e) {
            MessageService.sendMessage("Incorrect bet amount");
            return -1;
        }
    }

}