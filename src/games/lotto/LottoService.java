package games.lotto;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Random;

import model.CommandContext;
import repository.GameHistoryRepository;
import repository.UserRepository;
import service.MessageService;
import utils.Logger;

public class LottoService {

    private static final int LOTTO_NUMBERS = 6;
    private static final int MAX_NUMBER = 49;

    public static void handleLottoCommand(CommandContext context) {
        String playerName = context.getUserName();
        String betAmount = context.getFirstArgument();
        String numbers = context.getSecondArgument();
        int[] playerNumbersParsed;
        int betAmountParsed;

        if (betAmount.isEmpty()) {
            MessageService.sendMessage("Avaiable lotto commands: lotto random, lotto <betAmount> <num1,num2,num3,num4,num5,num6>");
            return;
        }

        if(context.getFirstArgument().equals("multi")){
            context.setFirstArgument(context.getSecondArgument());
            context.setSecondArgument(context.getThirdArgument());
            betAmount = context.getFirstArgument();
            betAmountParsed = parseBetAmount(betAmount);

            if (betAmountParsed < 10) {
                MessageService.sendMessage("Your bet amount must be greater than 10");
                Logger.logInfo("Player %s attempted to place a bet of %d coins, which is less than 10", "LottoService.handleLottoCommand()", playerName, betAmountParsed);
                return;
            }    

            for (int i = 0; i < 5; i++) {
                try {
                    Thread.sleep(300);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                handleLottoCommand(context);
            }
            return;
        }
        
        if (numbers.equals("random") || numbers.equals("r")) {
            playerNumbersParsed = generateNumbers();
        } else {
            playerNumbersParsed = validateAndParseNumbers(numbers);
            if(playerNumbersParsed == null){
                return;
            }
        }

        betAmountParsed = parseBetAmount(betAmount);
        if(betAmountParsed == -1) return;
        int currentBalance = UserRepository.getCurrentUserBalance(playerName, false);

        if (betAmountParsed < 10) {
            MessageService.sendMessage("Your bet amount must be greater than 10");
            Logger.logInfo("Player %s attempted to place a bet of %d coins, which is less than 10", "LottoService.handleLottoCommand()", playerName, betAmountParsed);
            return;
        }

        if (currentBalance < betAmountParsed) {
            MessageService.sendMessage("You don't have enough coins. Your balance: %d", currentBalance);
            return;
        }

        playLotto(playerName, playerNumbersParsed, currentBalance, betAmountParsed);
    }

    private static void playLotto(String playerName, int[] playerNumbers, int currentBalance, int betAmount) {
        Logger.logInfo("%s placed a Lotto bet.", "LottoService.playLotto()", playerName);
    
        int[] winningNumbers =  generateNumbers();
        int matches = countMatches(playerNumbers, winningNumbers);
        int prizePool = getPrizePool();

        int winnings = calculateWinnings(matches, betAmount, prizePool);
        int newBalance = currentBalance + winnings;
        UserRepository.updateUserBalance(playerName, newBalance);
    
        if (winnings > 0) {
            Logger.logInfo("%s won %d coins in Lotto. New balance: %d", "LottoService.playLotto()", playerName, winnings, newBalance);
        } else {
            Logger.logInfo("%s did not win in Lotto. New balance: %d", "LottoService.playLotto()", playerName, newBalance);
        }

        LottoImageGenerator.drawLottoResults(winningNumbers, playerNumbers, winnings, betAmount, newBalance, playerName, prizePool);
        MessageService.sendMessageFromClipboard(false);
    
        GameHistoryRepository.addGameHistory(playerName, "Lotto", arrayToString(playerNumbers), betAmount, winnings, "Winning Numbers: " + arrayToString(winningNumbers) + "Matches: " + matches);
    }
    
    private static String arrayToString(int[] array) {
        StringBuilder sb = new StringBuilder();
        for (int num : array) {
            sb.append(num).append(" ");
        }
        return sb.toString().trim();
    }


    private static int[] generateNumbers() {
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
                return -betAmount + ((int) calculateProportionalValueB(prizePool,0, betAmount + 1));
            case 2:
                return -betAmount + ((int) calculateProportionalValueB(prizePool,betAmount/2, betAmount + betAmount/2));
            case 3:
                return (int) (calculateProportionalValueB(prizePool,25,30) * betAmount);
            case 4:
                return (int) (calculateProportionalValueB(prizePool,500,600) * betAmount);
            case 5:
                return (int) (0.001 * prizePool * betAmount);
            case 6:
                return (int) (0.01 * prizePool * betAmount);
            default:
                return -betAmount;
        }
    }

    public static int getPrizePool() {
        LocalDateTime currentDateTime = LocalDateTime.now();
        
        int currentHour = currentDateTime.getHour();
        int currentMinute = currentDateTime.getMinute();
        
        int minPrize = 1_000_000;
        int maxPrize = 20_000_000;
        
        LocalDate currentDate = currentDateTime.toLocalDate();
        
        if (currentMinute >= 0 && currentMinute <= 19) {
            currentHour *= 2;
        } else if (currentMinute >= 20 && currentMinute <= 39) {
            currentHour *= 3;
        }

        int hashValue = currentDate.hashCode() + currentHour;

        Random random = new Random(hashValue);
        
        int prizePool = random.nextInt(maxPrize - minPrize) + minPrize;
        
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
    
    public static double calculateProportionalValueB(int prizePool, int rangeMin, int rangeMax) {
        double minValue = 1_000_000;
        double maxValue = 20_000_000;
        
        double normalizedPrize = (prizePool - minValue) / (maxValue - minValue);
        
        normalizedPrize = Math.sqrt(normalizedPrize);
        
        return rangeMin + normalizedPrize * (rangeMax - rangeMin);
    }
    
}