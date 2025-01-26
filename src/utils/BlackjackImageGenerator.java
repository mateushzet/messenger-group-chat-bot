package utils;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.datatransfer.*;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.net.URL;
import java.util.List;

public class BlackjackImageGenerator {

    private static final int CARD_WIDTH = 100;
    private static final int CARD_HEIGHT = 140;
    private static final int MARGIN = 20;
    
    private static final String CARD_BACK_IMAGE_URL = "https://cdn.pixabay.com/photo/2012/05/07/18/53/card-game-48983_1280.png";
    private static final Color PLAYER_COLOR = new Color(50, 200, 50);
    private static final Color DEALER_COLOR = new Color(200, 50, 50);
    
    public static void generateBlackjackImage(String userName, List<String> playerHand, List<String> dealerHand, String gameStatus, int playerBalance, int betAmount, boolean revealDealerCard, int playerScore, int dealerScore) {
        int width = Math.max(playerHand.size(), dealerHand.size()) * CARD_WIDTH + 2 * MARGIN;
        int height = 2 * CARD_HEIGHT + 3 * MARGIN + 100;
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();
    
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        
        g.setColor(new Color(0, 0, 0));
        g.fillRect(0, 0, width, height);
    
        Paint gradient = GradientGenerator.generateGradientFromUsername(userName, false, 220, 330);
        g.setPaint(gradient);
        g.fillRect(0, 0, width, height);
    
        int playerX = MARGIN;
        int playerY = height - CARD_HEIGHT - MARGIN;
        for (int i = 0; i < playerHand.size(); i++) {
            String card = playerHand.get(i);
            g.setColor(PLAYER_COLOR);
            g.fillRect(playerX + i * CARD_WIDTH, playerY, CARD_WIDTH, CARD_HEIGHT);
            drawCard(g, card, playerX + i * CARD_WIDTH, playerY);
        }
    
        int dealerX = MARGIN;
        int dealerY = MARGIN;
        for (int i = 0; i < dealerHand.size(); i++) {
            String card = dealerHand.get(i);
            g.setColor(DEALER_COLOR);
            g.fillRect(dealerX + i * CARD_WIDTH, dealerY, CARD_WIDTH, CARD_HEIGHT);
            if (i == 0 && !revealDealerCard) {
                drawCardBack(g, dealerX + i * CARD_WIDTH, dealerY);
            } else {
                drawCard(g, card, dealerX + i * CARD_WIDTH, dealerY);
            }
        }
    
        g.setColor(Color.BLACK);
        g.setFont(new Font("Arial", Font.PLAIN, 14));
        if (gameStatus != null) {
            g.drawString(gameStatus, MARGIN, height/2 - 2*MARGIN);
        }
    
        g.setFont(new Font("Arial", Font.PLAIN, 14));
        g.drawString("Balance: " + playerBalance, MARGIN, height/2 - MARGIN);
        
        g.setFont(new Font("Arial", Font.PLAIN, 14));
        g.drawString("Bet: " + betAmount, MARGIN, height/2);
    
        g.setFont(new Font("Arial", Font.PLAIN, 16));
        g.drawString("Player: " + playerScore, MARGIN, height/2 + MARGIN);
        if (revealDealerCard) {
            g.drawString("Dealer: " + dealerScore, MARGIN, height/2 + 2*MARGIN);
        }
    
        g.dispose();
        setClipboardImage(image);
    }

    private static void drawCard(Graphics2D g, String card, int x, int y) {
        g.setColor(Color.WHITE);
        g.fillRect(x, y, CARD_WIDTH, CARD_HEIGHT);
        g.setColor(Color.BLACK);
        g.drawRect(x, y, CARD_WIDTH, CARD_HEIGHT);
    
        Color textColor = getCardTextColor(card); 

        g.setFont(new Font("Arial", Font.BOLD, 20));
        FontMetrics metrics = g.getFontMetrics();
    

        String cardValue = card.substring(0, card.length() - 1); 
        char suit = card.charAt(card.length() - 1);
    
        int textX = x + (CARD_WIDTH - metrics.stringWidth(cardValue)) / 2;
        int textY = y + (CARD_HEIGHT + metrics.getHeight()) / 2 - 5;
    
        g.setColor(textColor);
        g.drawString(cardValue, textX, textY);
    

        g.setFont(new Font("Arial", Font.PLAIN, 14));
        String symbol = String.valueOf(suit);
    
        g.drawString(symbol, x + 5, y + 15);
        
        g.drawString(symbol, x + CARD_WIDTH - 20, y + CARD_HEIGHT - 5);
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
    
    private static Color getCardTextColor(String card) {
        char suit = card.charAt(card.length() - 1);
        if (suit == '♦' || suit == '♥') {
            return Color.RED;
        } else {
            return Color.BLACK;
        }
    }

    public static void setClipboardImage(final BufferedImage image) {
        TransferableImage transferable = new TransferableImage(image);
        Clipboard clipboard = Toolkit.getDefaultToolkit().getSystemClipboard();
        clipboard.setContents(transferable, null);
    }

    private static class TransferableImage implements Transferable {
        private final BufferedImage image;

        public TransferableImage(BufferedImage image) {
            this.image = image;
        }

        @Override
        public DataFlavor[] getTransferDataFlavors() {
            return new DataFlavor[]{DataFlavor.imageFlavor};
        }

        @Override
        public boolean isDataFlavorSupported(DataFlavor flavor) {
            return DataFlavor.imageFlavor.equals(flavor);
        }

        @Override
        public Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException, IOException {
            if (!isDataFlavorSupported(flavor)) {
                throw new UnsupportedFlavorException(flavor);
            }
            return image;
        }
    }
}
