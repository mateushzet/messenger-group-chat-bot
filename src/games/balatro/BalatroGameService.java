package games.balatro;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import javax.imageio.ImageIO;
import model.CommandContext;
import repository.GameHistoryRepository;
import repository.UserRepository;
import service.MessageService;
import service.UserService;
import utils.GradientGenerator;
import utils.ImageUtils;

import java.awt.GradientPaint;
import java.awt.Paint;
import java.awt.image.BufferedImage;
import java.io.File;
import java.nio.file.Paths;

public class BalatroGameService {

    private static final File JOCKERS_DIR = Paths.get("src", "resources", "balatro_jocker_images").toFile();

    public static class Joker {
        private final int id;
        private final String description;
        private final String imagePath;

        public Joker(int id, String description, String imagePath) {
            this.id = id;
            this.description = description;
            this.imagePath = imagePath;
        }

        public int getId() { return id; }
        public String getDescription() { return description; }
        public String getImagePath() { return imagePath; }
    }

    public static final List<Joker> ALL_JOKERS = List.of(
        new Joker(1, "Each pair in hand +3 mult", "Joker_Wilson.png"),
        new Joker(2, "Each face card discarded +20 chips", "Joker_Willow.png"),
        new Joker(3, "Each King in hand +25 chips", "Joker_Wolfgang.png"),
        //new Joker(4, "Each discard that becomes the same suit +5 chips +2 mult", "Joker_Wendy.png"),
        //new Joker(5, "Each heart kept once then discarded +2 mult", "Joker_WX-78.png"),
        new Joker(6, "Each Queen in hand +1 mult", "Joker_Wickerbottom.png"),
        new Joker(7, "Each card discarded +7 chips", "Joker_Woodie.png"),
        //new Joker(8, "Hand is worse after discard +30 chips", "Joker_Wes.png"),
        new Joker(9, "Each heart discarded +1 mult", "Joker_Maxwell.png"),
        new Joker(10, "Each Spade in hand +25 chips", "Joker_Wigfrid.png"),
        //new Joker(11, "Each Heart or Diamond replaced by a club or spade +2 mult", "Joker_Webber.png"),
        new Joker(12, "Hand contains a heart, a club, a diamond and a spade +4 mult", "Joker_Warly.png"),
        new Joker(13, "Each heart kept +1 mult", "Joker_Winona.png"),
        new Joker(14, "Each heart discarded +15 chips", "Joker_Wortox.png"),
        new Joker(15, "Each heart in hand -11 chips +1 mult", "Joker_Wormwood.png"),
        new Joker(16, "Each club kept +15 chips", "Joker_Wurt.png"),
        new Joker(17, "Each face card kept +10 chips per face card", "Joker_Walter.png"),
        new Joker(18, "Each suit in discard +15 chips. Start with 80. Each discard -15", "Joker_Wanda.png")
    );

    private static final List<String> DECK;

    static {
        List<String> tempDeck = new ArrayList<>();
        String[] ranks = { "A", "2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K" };
        char[] suits = { '♠', '♥', '♦', '♣' };
        for (String rank : ranks) {
            for (char suit : suits) {
                tempDeck.add(rank + suit);
            }
        }
        DECK = Collections.unmodifiableList(tempDeck);
    }

    public static final int STATUS_NEW = 0;
    public static final int STATUS_JOKER_SELECTED = 1;
    public static final int STATUS_CARDS_EXCHANGED = 2;
    public static final int STATUS_GAME_OVER = 3;

    public static BalatroGame startNewGame(String userName, int betAmount, int startingBalance) {
        List<String> deck = new ArrayList<>(DECK);
        Collections.shuffle(deck);
        List<String> playerHand = new ArrayList<>();
        for (int i = 0; i < 5; i++) {
            playerHand.add(deck.remove(0));
        }

        List<Joker> shuffledJokers = new ArrayList<>(ALL_JOKERS);
        Collections.shuffle(shuffledJokers);

        List<Integer> availableJokerIds = List.of(
            shuffledJokers.get(0).getId(),
            shuffledJokers.get(1).getId(),
            shuffledJokers.get(2).getId()
        );

        BalatroGame game = new BalatroGame(
            userName,
            betAmount,
            playerHand,
            new ArrayList<>(),
            true,
            startingBalance - betAmount
        );

        game.setAvailableJokerIds(availableJokerIds);
        game.setDeck(deck);
        game.setSelectedJokerId(0);
        game.setGameStatus(STATUS_NEW);

        ImageUtils.setClipboardImage(generateJokersSelectionImage(game));
        MessageService.sendMessageFromClipboard(true);
        return game;
    }

    public static void playTurn(BalatroGame game, String action, Object param) {
        int status = game.getGameStatus();
        switch (status) {
            case STATUS_NEW:
                if ("chooseJoker".equalsIgnoreCase(action) && param instanceof Integer) {
                    int chosenJokerId = (Integer) param;
                    if (game.getAvailableJokerIds().contains(chosenJokerId)) {
                        game.setSelectedJokerId(chosenJokerId);
                        game.setGameStatus(STATUS_JOKER_SELECTED);
                    }
                }

                ImageUtils.setClipboardImage(generateHandImage(game));
                MessageService.sendMessageFromClipboard(true);

                break;

            case STATUS_JOKER_SELECTED:
            case STATUS_CARDS_EXCHANGED:
            if ("discard".equalsIgnoreCase(action) && param instanceof List) {
                @SuppressWarnings("unchecked")
                List<String> toDiscard = (List<String>) param;
                List<String> playerHand = game.getPlayerHand();
                List<String> discardPile = game.getDiscardPile();
                List<String> deck = game.getDeck();

                for (String card : toDiscard) {
                    int index = playerHand.indexOf(card);
                    if (index != -1) {
                        playerHand.remove(index);
                        discardPile.add(card);

                        if (!deck.isEmpty()) {
                            String drawn = deck.remove(0);
                            playerHand.add(index, drawn);
                        }
                    }
                }

                game.setDeck(deck);

                if (status == STATUS_JOKER_SELECTED) {
                    ImageUtils.setClipboardImage(generateHandImage(game));
                    MessageService.sendMessageFromClipboard(true);
                    game.setGameStatus(STATUS_CARDS_EXCHANGED);
                } else {
                    game.setGameStatus(STATUS_GAME_OVER);
                }

            }
                break;

            case STATUS_GAME_OVER:
                break;

            default:
                break;
        }
    }

    public static int[] calculateResult(BalatroGame game) {
        List<String> hand = game.getPlayerHand();
        List<String> discardPile = game.getDiscardPile();
        int jokerId = game.getSelectedJokerId();

        int chips = calculateBaseChipsFromHand(hand);
        int mult = HandEvaluator.calculateBaseMultiplier(hand);

        switch (jokerId) {
            case 1: mult += countPairs(hand) * 3; break;
            case 2: chips += countFaceCards(discardPile) * 20; break;
            case 3: chips += countRanks(hand, "K") * 25; break;
            case 4: mult += countSameSuit(discardPile) * 2; chips += countSameSuit(discardPile) * 5; break;
            case 5: mult += countHeartsMovedToDiscard(hand, discardPile) * 2; break;
            case 6: mult += countRanks(hand, "Q"); break;
            case 7: chips += discardPile.size() * 7; break;
            case 8: if (hand.size() < 5) chips += 30; break;
            case 9: mult += countSuits(discardPile, '♥'); break;
            case 10: chips += countSuits(hand, '♠') * 25; break;
            case 11: mult += countHeartDiamondToBlackConversion(hand, discardPile) * 2; break;
            case 12: if (hasAllSuits(hand)) mult += 4; break;
            case 13: mult += countSuits(hand, '♥'); break;
            case 14: chips += countSuits(discardPile, '♥') * 15; break;
            case 15: int h = countSuits(hand, '♥'); chips -= h * 11; mult += h; break;
            case 16: chips += countSuits(hand, '♣') * 15; break;
            case 17: chips += countFaceCards(hand) * 10; break;
            case 18: int uniqueSuits = (int) discardPile.stream().map(c -> c.charAt(c.length() - 1)).distinct().count(); chips += 80 + uniqueSuits * 15 - discardPile.size() * 15; break;
        }

        return new int[]{chips, mult, chips * mult};
    }

    private static int calculateBaseChipsFromHand(List<String> hand) {
        int chips = 0;

        for (String card : hand) {
            String rank = card.substring(0, card.length() - 1);
            switch (rank) {
                case "A": chips += 11; break;
                case "T": chips += 10; break;
                case "J": chips += 11; break;
                case "Q": chips += 12; break;
                case "K": chips += 13; break;
                default:
                    try {
                        chips += Integer.parseInt(rank);
                    } catch (NumberFormatException ignored) {}
                    break;
            }
        }
        return chips;
    }

    

    private static String getJokerDescription(int jokerId) {
        for (Joker joker : ALL_JOKERS) {
            if (joker.getId() == jokerId) {
                return joker.getDescription();
            }
        }
        return "Unknown Joker";
    }

    private static int countRanks(List<String> cards, String rank) {
        return (int) cards.stream().filter(c -> c.startsWith(rank)).count();
    }

    private static int countFaceCards(List<String> cards) {
        return (int) cards.stream().filter(c -> c.matches("[JQK].")).count();
    }

    private static int countSuits(List<String> cards, char suit) {
        return (int) cards.stream().filter(c -> c.charAt(c.length() - 1) == suit).count();
    }

    private static int countPairs(List<String> cards) {
        java.util.Map<String, Integer> counts = new java.util.HashMap<>();
        for (String c : cards) {
            String rank = c.substring(0, c.length() - 1);
            counts.put(rank, counts.getOrDefault(rank, 0) + 1);
        }
        int pairs = 0;
        for (int count : counts.values()) {
            pairs += count / 2;
        }
        return pairs;
    }

    private static int countSameSuit(List<String> cards) {
        java.util.Map<Character, Integer> suits = new java.util.HashMap<>();
        for (String c : cards) {
            char suit = c.charAt(c.length() - 1);
            suits.put(suit, suits.getOrDefault(suit, 0) + 1);
        }
        return (int) suits.values().stream().filter(v -> v >= 2).count();
    }

    private static boolean hasAllSuits(List<String> cards) {
        java.util.Set<Character> suits = new java.util.HashSet<>();
        for (String c : cards) {
            suits.add(c.charAt(c.length() - 1));
        }
        return suits.containsAll(List.of('♠', '♥', '♦', '♣'));
    }

    private static int countHeartsMovedToDiscard(List<String> originalHand, List<String> discardPile) {
        return (int) discardPile.stream().filter(c -> c.charAt(c.length() - 1) == '♥').count();
    }

    private static int countHeartDiamondToBlackConversion(List<String> hand, List<String> discardPile) {
        long redOut = discardPile.stream().filter(c -> c.endsWith("♥") || c.endsWith("♦")).count();
        long blackIn = hand.stream().filter(c -> c.endsWith("♣") || c.endsWith("♠")).count();
        return (int) Math.min(redOut, blackIn);
    }

    private static BufferedImage generateJokersSelectionImage(BalatroGame game) {
        int width = 750;
        int height = 430;
        int borderThickness = 10;
        String playerName = game.getUserName();
        
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        var g = image.createGraphics();

        Paint gradient = GradientGenerator.generateGradientFromUsername(playerName, false, width, height);
        g.setPaint(gradient);
        g.fillRect(0, 0, width, height);

        gradient = new GradientPaint(0, 0, java.awt.Color.DARK_GRAY, width, height, java.awt.Color.BLACK);
        g.setPaint(gradient); 
        g.fillRect(borderThickness, borderThickness, width - 2*borderThickness, height - 2*borderThickness);

        ImageUtils.drawUserAvatar(g, game.getUserName(), 675, 15, 60, 60);

        g.translate(borderThickness, borderThickness);

        g.setColor(java.awt.Color.WHITE);
        g.setFont(new java.awt.Font("Arial", java.awt.Font.BOLD, 24));
        g.drawString("Choose your Joker: /balatro jocker <1-3>", 20, 40);

        List<Integer> available = game.getAvailableJokerIds();
        g.setFont(new java.awt.Font("Arial", java.awt.Font.PLAIN, 18));
        int y = 60;
        for (int i = 0; i < available.size(); i++) {
            Joker joker = getJokerById(available.get(i));
            BufferedImage jokerImg = null;
            try {
                jokerImg = ImageIO.read(new File(JOCKERS_DIR, joker.getImagePath()));
            } catch (Exception ignored) {}
            if (jokerImg != null) {
                g.drawImage(jokerImg, 20, y, 100, 100, null);
            }
            g.setColor(java.awt.Color.WHITE);
            g.drawString(String.format("%d) %s", i + 1, joker.getDescription()), 140, y + 40);
            y += 110;
        }

        g.dispose();
        return image;
    }

    private static BufferedImage generateHandImage(BalatroGame game) {
        return BalatroImageGenerator.generateBalatroImage(
            game.getUserName(),
            game.getPlayerHand(),
            BalatroImageGenerator.GamePhase.SHOW_HAND,
            "Joker selected: " + getJokerDescription(game.getSelectedJokerId()),
            UserRepository.getCurrentUserBalance(game.getUserName(), false),
            game.getBetAmount(),
            game
        );
    }

    private static BufferedImage generateGameOverImage(BalatroGame game, String result) {
        return BalatroImageGenerator.generateBalatroImage(
            game.getUserName(),
            game.getPlayerHand(),
            BalatroImageGenerator.GamePhase.GAME_END,
            "Joker selected: " + getJokerDescription(game.getSelectedJokerId()),
            UserRepository.getCurrentUserBalance(game.getUserName(), false),
            game.getBetAmount(),
            game
        );
    }

    private static Joker getJokerById(int id) {
        for (Joker joker : ALL_JOKERS) {
            if (joker.getId() == id) {
                return joker;
            }
        }
        return null;
    }

    public static void finalizeGame(String userName, BalatroGame game, CommandContext context) {
        if (game == null || !game.isGameInProgress()) {
            MessageService.sendMessage(userName + " you have no ongoing game.");
            return;
        }

        game.setGameInProgress(false);
        int[] result = calculateResult(game);
        int chips = result[0];
        int mult = result[1];
        int finalScore = result[2];

        int betAmount = game.getBetAmount();
        int winnings = 0;

        if (finalScore < 120) {
            winnings = 0;
        } else if (finalScore < 150) {
            winnings = betAmount / 2;
        } else if (finalScore < 200) {
            winnings = betAmount * 2;
        } else if (finalScore < 400) {
            winnings = betAmount * 3;
        } else if (finalScore < 600) {
            winnings = betAmount * 5;
        } else if (finalScore < 1000) {
            winnings = betAmount * 8;
        } else if (finalScore < 1400) {
            winnings = betAmount * 12;
        } else {
            winnings = betAmount * 20;
        }

        UserService.updateAndRetriveUserBalance(userName, winnings);

        String note = "Chips: " + chips + ", Mult: " + mult + ", Final Score: " + finalScore + ". You won: " + winnings + " coins. Game Details: "
        + game.getSelectedJokerId() + ", " + game.getAvailableJokerIds() + ", " + game.getDeck() + ", " + game.getDiscardPile() + ", " + game.getPlayerHand();
        GameHistoryRepository.addGameHistory(userName, "Balatro", context.getFullCommand(), betAmount, finalScore, "Result: " + note);

        String resultMessage = "Chips: " + chips + "  Mult: " + mult + "  Final Score: " + finalScore + "  You won: " + winnings + " coins.";

        ImageUtils.setClipboardImage(generateGameOverImage(game, resultMessage));
        MessageService.sendMessageFromClipboard(true);

        BalatroGameRepository.deleteGame(userName);
    }

    
}