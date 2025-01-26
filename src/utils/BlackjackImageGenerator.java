package utils;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.datatransfer.*;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.net.URL;
import java.util.List;

public class BlackjackImageGenerator {

    private static final int CARD_WIDTH = 90;
    private static final int CARD_HEIGHT = 140;
    private static final int MARGIN = 20;
    
    private static final String CARD_BACK_IMAGE_URL = "https://cdn.pixabay.com/photo/2012/05/07/18/53/card-game-48983_1280.png";
    private static final Color PLAYER_COLOR = new Color(50, 200, 50);
    private static final Color DEALER_COLOR = new Color(200, 50, 50);
    
    public static void generateBlackjackImage(String userName, List<String> playerHand, List<String> dealerHand, String gameStatus, int playerBalance) {
        int width = Math.max(playerHand.size(), dealerHand.size()) * CARD_WIDTH + 2 * MARGIN;
        int height = 2 * CARD_HEIGHT + 3 * MARGIN;
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        
        g.setColor(new Color(0, 0, 0));
        g.fillRect(0, 0, width, height);

        // Background gradient based on username (you can modify this further)
        Paint gradient = GradientGenerator.generateGradientFromUsername(userName, false, 220, 330);
        g.setPaint(gradient);
        g.fillRect(0, 0, width, height);

        // Player cards
        int playerX = MARGIN;
        int playerY = height - CARD_HEIGHT - MARGIN;
        for (int i = 0; i < playerHand.size(); i++) {
            String card = playerHand.get(i);
            g.setColor(PLAYER_COLOR);
            g.fillRect(playerX + i * CARD_WIDTH, playerY, CARD_WIDTH, CARD_HEIGHT);
            drawCard(g, card, playerX + i * CARD_WIDTH, playerY);
        }

        // Dealer cards (showing one card face down)
        int dealerX = MARGIN;
        int dealerY = MARGIN;
        for (int i = 0; i < dealerHand.size(); i++) {
            String card = dealerHand.get(i);
            g.setColor(DEALER_COLOR);
            g.fillRect(dealerX + i * CARD_WIDTH, dealerY, CARD_WIDTH, CARD_HEIGHT);
            if (i == 0) {
                drawCardBack(g, dealerX + i * CARD_WIDTH, dealerY); // Draw back of the first card
            } else {
                drawCard(g, card, dealerX + i * CARD_WIDTH, dealerY); // Draw face-up card
            }
        }

        // Game status and balance
        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 18));
        if (gameStatus != null) {
            g.drawString(gameStatus, MARGIN, height - 2 * MARGIN);
        }
        
        g.setFont(new Font("Arial", Font.PLAIN, 14));
        g.drawString("Balance: $" + playerBalance, MARGIN, height - MARGIN);

        g.dispose();
        setClipboardImage(image);
    }

    private static void drawCard(Graphics2D g, String card, int x, int y) {
        // Draw the card (simplified for the example)
        g.setColor(Color.WHITE);
        g.fillRect(x, y, CARD_WIDTH, CARD_HEIGHT);
        g.setColor(Color.BLACK);
        g.drawRect(x, y, CARD_WIDTH, CARD_HEIGHT);

        // Draw the card value (simplified)
        g.setFont(new Font("Arial", Font.BOLD, 20));
        FontMetrics metrics = g.getFontMetrics();
        String cardValue = card;  // Use actual card value (e.g., 10, Jack, Queen, etc.)
        int textX = x + (CARD_WIDTH - metrics.stringWidth(cardValue)) / 2;
        int textY = y + (CARD_HEIGHT + metrics.getHeight()) / 2 - 5;
        g.drawString(cardValue, textX, textY);
    }

    private static void drawCardBack(Graphics2D g, int x, int y) {
        try {
            BufferedImage cardBackImage = ImageIO.read(new URL(CARD_BACK_IMAGE_URL));
            g.drawImage(cardBackImage, x, y, CARD_WIDTH, CARD_HEIGHT, null);
        } catch (IOException e) {
            g.setColor(Color.BLUE);
            g.fillRect(x, y, CARD_WIDTH, CARD_HEIGHT); // Fallback if image fails to load
            g.setColor(Color.BLACK);
            g.drawRect(x, y, CARD_WIDTH, CARD_HEIGHT);
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
