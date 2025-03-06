package games.moneytree;

import repository.GameHistoryRepository;
import repository.UserRepository;
import service.MessageService;
import model.CommandContext;
import utils.ImageUtils;

import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import javax.imageio.ImageIO;

public class MoneyTreeService {

    private static final int PHASE_COUNT = 6;
    private static final int MIN_PHASE_DURATION = 3600;
    private static final int MAX_PHASE_DURATION = 36000;

    private static final String TREE_IMAGES_PATH = "src/games/moneytree/";

    public static void handleTreeCommand(CommandContext context) {
        String userName = context.getUserName();
        String firstArg = context.getFirstArgument();

        if (firstArg.equalsIgnoreCase("plant")) {
            startGame(userName, context);
            return;
        }

        if (firstArg.equalsIgnoreCase("water")) {
            checkProgress(userName, context);
            return;
        }

        if (firstArg.equalsIgnoreCase("cut")) {
            cashout(userName, context);
            return;
        }

        if (firstArg.equalsIgnoreCase("help")) {
            String helpMessage = "/tree plant - Start the game by planting a tree.\n" +
                    "/tree water - Check the current status of your tree.\n" +
                    "/tree cut - Cash out and collect your earnings.\n";
            MessageService.sendMessage(helpMessage);
            return;
        }

        MessageService.sendMessage(userName + " available commands: tree plant, tree water, tree cut");
    }

    private static void startGame(String userName, CommandContext context) {
        if (MoneyTreeRepository.getGameByUserName(userName) != null) {
            MessageService.sendMessage(userName + " you already have an active tree game.");
            return;
        }

        String betAmount = context.getSecondArgument();
        int coins;
        try {
            coins = Integer.parseInt(betAmount);
        } catch (NumberFormatException e) {
            MessageService.sendMessage(userName + " please provide a valid number of coins.");
            return;
        }

        int userBalance = UserRepository.getCurrentUserBalance(userName, true);
        if (userBalance < coins || coins <= 0) {
            MessageService.sendMessage(userName + " you don't have enough coins to play.");
            return;
        }

        //int userTotalBalance = UserRepository.getTotalUserBalance(userName);
        //int userBalanceTenPercent = (int)(userTotalBalance/10);
        //if (userBalanceTenPercent < coins) {
        //    MessageService.sendMessage(userName + " you can plant up to 10%% of your balance ("+userBalanceTenPercent+" max).");
        //    return;
        //}

        UserRepository.updateUserBalance(userName, userBalance - coins);

        List<Integer> phaseDurations = generatePhaseDurations();
        Random random = new Random();

        int witherPhase;
        if (random.nextInt(100) < 10) {
            witherPhase = random.nextInt(PHASE_COUNT) + 1;
        } else {
            witherPhase = 7;
        }

        int totalPhaseTime = phaseDurations.stream().mapToInt(Integer::intValue).sum();
        int witherTime = totalPhaseTime + 3600;

        MoneyTreeRepository.saveGame(userName, coins, phaseDurations, witherPhase, witherTime);

        BufferedImage treeImage = loadTreeImage(0, userName);
        if (treeImage != null) {
            ImageUtils.setClipboardImage(treeImage);
            MessageService.sendMessageFromClipboard(true);
        }

        MessageService.sendMessage(userName + " you planted a tree!");
    }

    private static void checkProgress(String userName, CommandContext context) {
        MoneyTreeGame game = MoneyTreeRepository.getGameByUserName(userName);
        if (game == null || !game.isActive()) {
            MessageService.sendMessage(userName + " you don't have an active tree game.");
            return;
        }

        long currentTime = System.currentTimeMillis() / 1000;
        long elapsedTime = currentTime - game.getStartTime();

        if (elapsedTime >= game.getWitherTime()) {
            BufferedImage witheredImage = loadTreeImage(-1, userName);
            if (witheredImage != null) {
                ImageUtils.setClipboardImage(witheredImage);
                MessageService.sendMessageFromClipboard(true);
            }

            MessageService.sendMessage(userName + " unfortunately, your tree withered!");
            GameHistoryRepository.addGameHistory(userName, "MoneyTree", context.getCommand(), game.getInvestedCoins(), 0, "Phase: " + -1);
            MoneyTreeRepository.deleteGame(userName);
            return;
        }

        int currentPhase = 0;
        List<Integer> phaseDurations = game.getPhaseDurations();

        for (int i = 0; i < phaseDurations.size(); i++) {
            if (elapsedTime >= phaseDurations.get(i)) {
                elapsedTime -= phaseDurations.get(i);
                currentPhase++;
            } else {
                break;
            }
        }

        if (game.getWitherPhase() != 7 && currentPhase >= game.getWitherPhase()) {
            BufferedImage witheredImage = loadTreeImage(-1, userName);
            if (witheredImage != null) {
                ImageUtils.setClipboardImage(witheredImage);
                MessageService.sendMessageFromClipboard(true);
            }

            MessageService.sendMessage(userName + " unfortunately, your tree withered!");
            GameHistoryRepository.addGameHistory(userName, "MoneyTree", context.getCommand(), game.getInvestedCoins(), 0, "Phase: " + -1);
            MoneyTreeRepository.deleteGame(userName);
            return;
        }

        BufferedImage treeImage = loadTreeImage(currentPhase, userName);
        if (treeImage != null) {
            ImageUtils.setClipboardImage(treeImage);
            MessageService.sendMessageFromClipboard(true);
        }
    }

    private static void cashout(String userName, CommandContext context) {
        MoneyTreeGame game = MoneyTreeRepository.getGameByUserName(userName);
        if (game == null || !game.isActive()) {
            MessageService.sendMessage(userName + " you don't have an active tree game.");
            return;
        }

        long currentTime = System.currentTimeMillis() / 1000;
        long elapsedTime = currentTime - game.getStartTime();

        if (elapsedTime >= game.getWitherTime()) {
            BufferedImage witheredImage = loadTreeImage(-1, userName);
            if (witheredImage != null) {
                ImageUtils.setClipboardImage(witheredImage);
                MessageService.sendMessageFromClipboard(true);
            }

            MessageService.sendMessage(userName + " unfortunately, your tree withered!");
            MoneyTreeRepository.deleteGame(userName);
            return;
        }

        int currentPhase = 0;
        List<Integer> phaseDurations = game.getPhaseDurations();

        for (int i = 0; i < phaseDurations.size(); i++) {
            if (elapsedTime >= phaseDurations.get(i)) {
                elapsedTime -= phaseDurations.get(i);
                currentPhase++;
            } else {
                break;
            }
        }

        if (currentPhase >= game.getWitherPhase()) {
            BufferedImage witheredImage = loadTreeImage(-1, userName);
            if (witheredImage != null) {
                ImageUtils.setClipboardImage(witheredImage);
                MessageService.sendMessageFromClipboard(true);
            }

            MessageService.sendMessage(userName + " unfortunately, your tree withered!");
            MoneyTreeRepository.deleteGame(userName);
            return;
        }

        int profit = calculateProfit(game.getInvestedCoins(), currentPhase);
        UserRepository.updateUserBalance(userName, UserRepository.getCurrentUserBalance(userName, true) + profit);

        BufferedImage treeImage = loadTreeImage(currentPhase, userName);
        if (treeImage != null) {
            ImageUtils.setClipboardImage(treeImage);
            MessageService.sendMessageFromClipboard(true);
        }

        MessageService.sendMessage(userName + " you collected your coins! Your profit: " + profit + ". Current balance: " + UserRepository.getCurrentUserBalance(userName, true));

        GameHistoryRepository.addGameHistory(userName, "MoneyTree", context.getCommand(), game.getInvestedCoins(), profit, "Phase: " + currentPhase);

        MoneyTreeRepository.deleteGame(userName);
    }

    private static List<Integer> generatePhaseDurations() {
        List<Integer> durations = new ArrayList<>();
        Random random = new Random();
        for (int i = 0; i < PHASE_COUNT; i++) {
            durations.add(random.nextInt(MAX_PHASE_DURATION - MIN_PHASE_DURATION) + MIN_PHASE_DURATION);
        }
        return durations;
    }

    private static int calculateProfit(int investedCoins, int currentPhase) {
        if (investedCoins <= 0 || currentPhase < 0) {
            return 0;
        }

        switch (currentPhase) {
            case 0:
                return (int) (investedCoins * 0.5);
            case 1:
                return (int) (investedCoins * 1.05);
            case 2:
                return (int) (investedCoins * 1.1);
            case 3:
                return (int) (investedCoins * 1.15);
            case 4:
                return (int) (investedCoins * 1.25);
            case 5:
                return (int) (investedCoins * 1.5);
            default:
                return 0;
        }
    }

    private static BufferedImage loadTreeImage(int phase, String userName) {
        try {

            String fileName = (phase == -1) ? "withered.png" : "phase_" + phase + ".png";
            File imageFile = new File(TREE_IMAGES_PATH + fileName);
            BufferedImage treeImage = ImageIO.read(imageFile);
    
            BufferedImage combinedImage = new BufferedImage(
                    treeImage.getWidth(), treeImage.getHeight(), BufferedImage.TYPE_INT_ARGB);
            Graphics2D g = combinedImage.createGraphics();
    
            g.drawImage(treeImage, 0, 0, null);
    
            int avatarWidth = 50;
            int avatarHeight = 50;
            int avatarX = treeImage.getWidth() - avatarWidth - 10;
            int avatarY = 10;
    
            ImageUtils.drawUserAvatar(g, userName, avatarX, avatarY, avatarWidth, avatarHeight);
    
            g.dispose();
            return combinedImage;
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
    }
}