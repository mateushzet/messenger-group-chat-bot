package utils;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.net.URL;
import java.util.Arrays;
import java.util.List;

public class BlackjackImageGenerator {

    private static final int CARD_WIDTH = 100;
    private static final int CARD_HEIGHT = 140;
    private static final int MARGIN = 20;
    private static final int DEALER_Y = 20;
    private static final int PLAYER_Y = 300;
    private static final int INFO_BOX_Y = 180;
    private static final int IMAGE_HEIGHT = 460;
    private static final String CARD_BACK_IMAGE_URL = "https://cdn.pixabay.com/photo/2012/05/07/18/53/card-game-48983_1280.png";


    public static void generateBlackjackImage(String userName, List<String> playerHand, List<String> dealerHand, String gameStatus, int playerBalance, int betAmount, boolean revealDealerCard, int playerScore, int dealerScore) {
        int maxCards = Math.max(playerHand.size(), dealerHand.size());
        int imageWidth = Math.max(MARGIN * 2 + maxCards * CARD_WIDTH, 380);
    
        BufferedImage image = new BufferedImage(imageWidth, IMAGE_HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
    
        Paint gradient = GradientGenerator.generateGradientFromUsername(userName, false, imageWidth, IMAGE_HEIGHT);
        g.setPaint(gradient);
        g.fillRect(0, 0, imageWidth, IMAGE_HEIGHT);
    
        int playerStartX = (imageWidth - playerHand.size() * CARD_WIDTH) / 2;
        for (int i = 0; i < playerHand.size(); i++) {
            drawCard(g, playerHand.get(i), playerStartX + i * CARD_WIDTH, PLAYER_Y);
        }
    
        int dealerStartX = (imageWidth - dealerHand.size() * CARD_WIDTH) / 2;
        for (int i = 0; i < dealerHand.size(); i++) {
            if (i == 0 && !revealDealerCard) {
                drawCardBack(g, dealerStartX + i * CARD_WIDTH, DEALER_Y);
            } else {
                drawCard(g, dealerHand.get(i), dealerStartX + i * CARD_WIDTH, DEALER_Y);
            }
        }
    
        drawGameInfo(g, gameStatus, playerBalance, betAmount, playerScore, dealerScore, revealDealerCard, imageWidth);
    
        g.dispose();
        ImageUtils.setClipboardImage(image);
    }

    private static void drawCard(Graphics2D g, String card, int x, int y) {
        g.setColor(Color.WHITE);
        g.fillRoundRect(x, y, CARD_WIDTH, CARD_HEIGHT, 15, 15);
        g.setColor(Color.BLACK);
        g.drawRoundRect(x, y, CARD_WIDTH, CARD_HEIGHT, 15, 15);
        
        Color textColor = getCardTextColor(card);
        g.setColor(textColor);
        g.setFont(new Font("Arial", Font.BOLD, 20));
        
        String value = card.substring(0, card.length() - 1);
        String suit = card.substring(card.length() - 1);
        
        g.drawString(suit, x + 5, y + 20);
        g.drawString(suit, x + CARD_WIDTH - 20, y + CARD_HEIGHT - 5);
        g.drawString(value, x + (CARD_WIDTH / 2) - 10, y + (CARD_HEIGHT / 2) + 5);
    }

    private static void drawCardBack(Graphics2D g, int x, int y) {
        try {
            BufferedImage cardBackImage = ImageIO.read(new URL(CARD_BACK_IMAGE_URL));
            g.drawImage(cardBackImage, x, y, CARD_WIDTH, CARD_HEIGHT, null);
        } catch (IOException e) {
            g.setColor(Color.BLUE);
            g.fillRect(x, y, CARD_WIDTH, CARD_HEIGHT);
            g.setColor(Color.BLACK);
            g.drawRect(x, y, CARD_WIDTH, CARD_HEIGHT);
        }
    }

    private static void drawGameInfo(Graphics2D g, String gameStatus, int playerBalance, int betAmount, int playerScore, int dealerScore, boolean revealDealerCard, int imageWidth) {
        g.setFont(new Font("Arial", Font.BOLD, 16));
        FontMetrics fm = g.getFontMetrics();
        
        String[] texts = {
            gameStatus,
            "Balance: " + playerBalance,
            "Bet: " + betAmount,
            "Player: " + playerScore,
            "Dealer: " + dealerScore
        };
        
        int maxWidth = Arrays.stream(texts)
                .mapToInt(fm::stringWidth)
                .max()
                .orElse(200);
        
        int infoBoxX = (imageWidth - maxWidth - 40) / 2;
        g.setColor(new Color(0, 0, 0, 150));
        g.fillRoundRect(infoBoxX, INFO_BOX_Y, maxWidth + 40, 110, 20, 20);
        g.setColor(Color.WHITE);
        
        for (int i = 0; i < texts.length; i++) {
            if (!texts[i].isEmpty()) {
                g.drawString(texts[i], infoBoxX + 20, INFO_BOX_Y + 20 + (i * 20));
            }
        }
    }

    private static Color getCardTextColor(String card) {
        char suit = card.charAt(card.length() - 1);
        return (suit == '♦' || suit == '♥') ? Color.RED : Color.BLACK;
    }

}
