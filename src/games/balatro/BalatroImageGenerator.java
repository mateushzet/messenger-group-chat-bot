package games.balatro;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.util.List;
import utils.GradientGenerator;
import utils.ImageUtils;

public class BalatroImageGenerator {

    private static final int CARD_WIDTH = 120;
    private static final int CARD_HEIGHT = 150;
    private static final int MARGIN = 40;
    private static final int HAND_Y = 200;
    private static final int IMAGE_HEIGHT = 480;

    public enum GamePhase {
        SHOW_HAND,
        GAME_END
    }

    public static BufferedImage generateBalatroImage(
            String userName,
            List<String> playerHand,
            GamePhase phase,
            String gameStatus,
            int playerBalance,
            int betAmount,
            BalatroGame game) {

        int imageWidth = 750;
        int borderThickness = 10;

        BufferedImage image = new BufferedImage(imageWidth, IMAGE_HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        Paint borderGradient = GradientGenerator.generateGradientFromUsername(userName, false, imageWidth, IMAGE_HEIGHT);
        g.setPaint(borderGradient);
        g.fillRect(0, 0, imageWidth, IMAGE_HEIGHT);

        GradientPaint innerGradient = new GradientPaint(0, 0, Color.DARK_GRAY, imageWidth, IMAGE_HEIGHT, Color.BLACK);
        g.setPaint(innerGradient);
        g.fillRect(borderThickness, borderThickness, imageWidth - 2 * borderThickness, IMAGE_HEIGHT - 2 * borderThickness);

        g.translate(borderThickness, borderThickness);

        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 22));
        g.drawString("Balatro", MARGIN, 40);

        ImageUtils.drawUserAvatar(g, userName, 650, 10, 70, 70);

        g.setFont(new Font("Arial", Font.BOLD, 16));
        g.drawString("Player: " + userName, MARGIN, 70);
        g.drawString("Balance: " + playerBalance + "  Bet: " + betAmount, MARGIN, 95);
        g.setFont(new Font("Arial", Font.BOLD, 16));
        g.drawString(gameStatus, MARGIN, 125);

        drawCards(g, playerHand, MARGIN, HAND_Y, "Hand:");
        int[] result = BalatroGameService.calculateResult(game);
        int chips = result[0];
        int mult = result[1];
        int finalScore = result[2];
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
        String resultMessage = "Chips: " + chips + "  Mult: " + mult + "  Final Score: " + finalScore + " Prize: " + winnings;

         switch (phase) {
            case SHOW_HAND:
                drawSummary(g, resultMessage, imageWidth - 2 * borderThickness, IMAGE_HEIGHT - 2 * borderThickness);
                break;

            case GAME_END:
                drawGameEndSummary(g, resultMessage, imageWidth - 2 * borderThickness, IMAGE_HEIGHT - 2 * borderThickness);
                break;
        }

        g.dispose();
        return image;
    }

    private static void drawGameEndSummary(Graphics2D g, String gameStatus, int width, int height) {
        g.setColor(Color.YELLOW);
        g.setFont(new Font("Arial", Font.BOLD, 30));
        String text = "Game Over!";
        int textWidth = g.getFontMetrics().stringWidth(text);
        g.drawString(text, (width - textWidth) / 2, 385);

        g.setFont(new Font("Arial", Font.PLAIN, 18));
        int statusWidth = g.getFontMetrics().stringWidth(gameStatus);
        g.drawString(gameStatus, (width - statusWidth) / 2, 415);
    }

        private static void drawSummary(Graphics2D g, String gameStatus, int width, int height) {
        g.setColor(Color.WHITE);

        g.setFont(new Font("Arial", Font.PLAIN, 18));
        int statusWidth = g.getFontMetrics().stringWidth(gameStatus);
        g.drawString(gameStatus, (width - statusWidth) / 2, 415);
    }

    private static void drawCards(Graphics2D g, List<String> cards, int startX, int y, String label) {
        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 16));
        g.drawString(label, startX + 25, y - 15);

        int x = startX;
        for (String card : cards) {
            drawCard(g, card, x, y, CARD_WIDTH, CARD_HEIGHT);
            x += CARD_WIDTH + 10;
        }
    }

    public static void fillGradient(Graphics2D g, int width, int height, Color startColor, Color endColor) {
        GradientPaint gp = new GradientPaint(
                0, 0, startColor,
                0, height, endColor
        );
        Paint oldPaint = g.getPaint();
        g.setPaint(gp);
        g.fillRect(0, 0, width, height);
        g.setPaint(oldPaint);
    }

    public static void drawCard(Graphics2D g, String card, int x, int y, int width, int height) {
        g.setColor(Color.WHITE);
        g.fillRoundRect(x, y, width, height, 15, 15);
        g.setColor(Color.BLACK);
        g.drawRoundRect(x, y, width, height, 15, 15);

        Color textColor = getCardTextColor(card);
        g.setColor(textColor);
        g.setFont(new Font("Arial", Font.BOLD, 20));

        String value = card.substring(0, card.length() - 1);
        if (value.equals("T")) {
            value = "10";
        }
        String suit = card.substring(card.length() - 1);

        g.drawString(suit, x + 5, y + 20);
        g.drawString(suit, x + width - 20, y + height - 5);
        g.drawString(value, x + (width / 2) - 10, y + (height / 2) + 5);
    }

    private static Color getCardTextColor(String card) {
        char suit = card.charAt(card.length() - 1);
        return (suit == '♦' || suit == '♥') ? Color.RED : Color.BLACK;
    }

    public static BufferedImage createHelpImage(String text) {
        int width = 600;
        int height = 900;

        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        g.setColor(Color.WHITE);
        g.fillRect(0, 0, width, height);

        g.setColor(Color.BLACK);
        g.setFont(new Font("Arial", Font.PLAIN, 14));

        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

        int x = 20;
        int y = 30;
        int lineHeight = 18;

        for (String line : text.split("\n")) {
            g.drawString(line.trim(), x, y);
            y += lineHeight;
        }

        g.dispose();
        return image;
    }
    
}