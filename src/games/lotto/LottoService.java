package games.lotto;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Objects;
import java.util.Random;

import model.CommandContext;
import repository.GameHistoryRepository;
import repository.UserAvatarRepository;
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
        boolean isMulti = context.getFirstArgument().equals("multi");
        if (betAmount.isEmpty()) {
            MessageService.sendMessage("Avaiable lotto commands: lotto random, lotto <betAmount> <num1,num2,num3,num4,num5,num6>");
            return;
        }

        if(isMulti){
            betAmount = context.getSecondArgument();
            numbers = context.getThirdArgument();
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

        if(isMulti && currentBalance < 5*betAmountParsed || currentBalance < betAmountParsed){
            MessageService.sendMessage("You don't have enough coins. Your balance: %d", currentBalance);
            return;
        }

        if(isMulti){
            playLottoMulti(playerName, playerNumbersParsed, currentBalance, betAmountParsed);
        } else playLotto(playerName, playerNumbersParsed, currentBalance, betAmountParsed);
    }

    private static void playLotto(String playerName, int[] playerNumbers, int currentBalance, int betAmount) {
        int[] winningNumbers =  generateNumbers();
        int matches = countMatches(playerNumbers, winningNumbers);
        int prizePool = getPrizePool();

        int winnings = calculateWinnings(matches, betAmount, prizePool, playerName);
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

    private static void playLottoMulti(String playerName, int[] playerNumbers, int currentBalance, int betAmount) {
        int[][] winningNumbers = new int[5][5];
        int matches[] = new int[5];
        int prizePool = getPrizePool();
        int winnings = 0;
        for (int i = 0; i < 5; i++) {
            winningNumbers[i] = generateNumbers();
            matches[i] = countMatches(playerNumbers, winningNumbers[i]);
            winnings += calculateWinnings(matches[i], betAmount, prizePool, playerName);
        }
        int newBalance = currentBalance + winnings;
        UserRepository.updateUserBalance(playerName, newBalance);
        LottoImageGenerator.drawLottoMultiResults(winningNumbers, playerNumbers, winnings, 5*betAmount, newBalance, playerName, prizePool);
        MessageService.sendMessageFromClipboard(false);
        GameHistoryRepository.addGameHistory(playerName, "Lotto", arrayToString(playerNumbers), betAmount, winnings 
        ,"Winning Numbers 1: " + arrayToString(winningNumbers[0]) + "Matches: " + matches[0]
        + " Winning Numbers 2: " + arrayToString(winningNumbers[1]) + "Matches: " + matches[1]
        + " Winning Numbers 3: " + arrayToString(winningNumbers[2]) + "Matches: " + matches[2]
        + " Winning Numbers 4: " + arrayToString(winningNumbers[3]) + "Matches: " + matches[3]
        + " Winning Numbers 5: " + arrayToString(winningNumbers[4]) + "Matches: " + matches[4]
        );
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
    
    private static int calculateWinnings(int matches, int betAmount, int prizePool, String playerName) {
        switch (matches) {
            case 1:
                return -betAmount;
            case 2:
                return -betAmount + ((int) calculateProportionalValueB(prizePool,betAmount/2, betAmount + betAmount/2));
            case 3:
                return (int) (calculateProportionalValueB(prizePool,10,30) * betAmount);
            case 4:
                UserAvatarRepository.assignAvatarToUser(playerName, "lotto 4");
                return (int) (calculateProportionalValueB(prizePool,300,600) * betAmount);
            case 5:
                UserAvatarRepository.assignAvatarToUser(playerName, "lotto 5");
                return (int) (0.001 * prizePool * betAmount);
            case 6:
                UserAvatarRepository.assignAvatarToUser(playerName, "lotto 6");
                return (int) (0.01 * prizePool * betAmount);
            default:
                return -betAmount;
        }
    }

    public static int getPrizePool() {
        LocalDateTime currentDateTime = LocalDateTime.now();
    
        int currentHour = currentDateTime.getHour();
        int currentMinute = currentDateTime.getMinute();
        currentMinute = (currentMinute / 10) * 10;

        int seed = Objects.hash(currentDateTime.toLocalDate(), currentHour, currentMinute * 7919);
        Random random = new Random(seed);
    
        double chance = random.nextDouble();
    
        int lowerBound, upperBound;
    
        if (chance < 0.7) {
            lowerBound = 1_000_000;
            upperBound = 10_000_000;
        } else {
            lowerBound = 10_000_000;
            upperBound = 20_000_000;
        }
    
        int prizePool = lowerBound + random.nextInt(upperBound - lowerBound + 1);
    
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
        
        return rangeMin + normalizedPrize * (rangeMax - rangeMin);
    }

}