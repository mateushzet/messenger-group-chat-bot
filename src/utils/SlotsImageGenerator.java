package utils;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.net.URL;
import java.util.Random;
import java.awt.datatransfer.Clipboard;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;

import javax.imageio.ImageIO;


public class SlotsImageGenerator {

    private static final String[] symbols = {
        "https://cdn-icons-png.flaticon.com/128/10646/10646576.png",
        "https://cdn-icons-png.flaticon.com/128/10646/10646518.png",
        "https://cdn-icons-png.flaticon.com/128/10646/10646435.png",
        "https://cdn-icons-png.flaticon.com/128/10646/10646584.png",
        "https://cdn-icons-png.flaticon.com/128/10646/10646477.png",
        "https://cdn-icons-png.flaticon.com/128/10646/10646487.png",
        "https://cdn-icons-png.flaticon.com/128/10646/10646590.png"
    };

    private static final Color RED_COLOR = new Color(200, 50, 50);
    private static final Color GREEN_COLOR = new Color(50, 200, 50);
    private static final Color DARK_GRAY = new Color(25, 25, 25);
    
    public static void generateSlotsResultImage(int[] result, String playerName, int amount, int totalBalance, int betAmount, int jackpotAmount) {
        String[] resultsImages = {symbols[result[0]], symbols[result[1]], symbols[result[2]]};
        
        int width = 300;
        int height = 330;
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();
    
        GradientPaint gradient = GradientGenerator.generateGradientFromUsername(playerName, false, width, height);
        
        int symbolWidth = width / 3;
        int symbolHeight = width / 3;
    
        g.setColor(new Color(230,230,230));
        g.fillRect(0, 0, 300, 300);

        String[] topRow = spinSlotsWithWildcard();
        for (int i = 0; i < 3; i++) {
            try {
                URL imageUrl = new URL(topRow[i]);
                Image symbolImage = ImageIO.read(imageUrl);
                g.drawImage(symbolImage, i * symbolWidth, 0 - (symbolHeight / 2), symbolWidth, symbolWidth, null);
    
                if (i < 2) {
                    g.setColor(Color.GRAY);
                    g.drawLine((i + 1) * symbolWidth, 0, (i + 1) * symbolWidth, height);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    
        for (int i = 0; i < resultsImages.length; i++) {
            try {
                URL imageUrl = new URL(resultsImages[i]);
                Image symbolImage = ImageIO.read(imageUrl);
                g.drawImage(symbolImage, i * symbolWidth, symbolWidth - (symbolHeight / 2), symbolWidth, symbolWidth, null);
    
                if (i < 2) {
                    g.setColor(Color.GRAY);
                    g.drawLine((i + 1) * symbolWidth, symbolWidth - (symbolHeight / 2), (i + 1) * symbolWidth, height);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    
        String[] bottomRow = spinSlotsWithWildcard();
        for (int i = 0; i < 3; i++) {
            try {
                URL imageUrl = new URL(bottomRow[i]);
                Image symbolImage = ImageIO.read(imageUrl);
                g.drawImage(symbolImage, i * symbolWidth, 2 * symbolWidth - (symbolHeight / 2), symbolWidth, symbolWidth, null);
    
                if (i < 2) {
                    g.setColor(Color.GRAY);
                    g.drawLine((i + 1) * symbolWidth, 2 * symbolWidth - (symbolHeight / 2), (i + 1) * symbolWidth, height);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        
        g.setColor(DARK_GRAY);
        g.setStroke(new BasicStroke(10));
        g.drawRect(0, 0, width - 1, height - 1 - (symbolHeight / 2) - 80);
    
        g.setColor(Color.DARK_GRAY);
        g.setFont(new Font("Arial", Font.BOLD, 24));
        g.fillRect(0, 202, 300, 130);

        g.setPaint(gradient);
        g.fillRect(0, 200, 300, 200);

        if (amount > 0) {
            g.setColor(GREEN_COLOR);
            g.drawString("WIN " + amount, 10, 230);
        } else {
            g.setColor(RED_COLOR);
            g.drawString("LOSE " + amount, 10, 230);
        }

        g.setColor(Color.WHITE);
        g.drawString(playerName, 10, 260);
        g.drawString("Total: " + totalBalance, 10, 290);
        g.drawString("Jackpot: " + jackpotAmount, 10, 320);

        g.setFont(new Font("Arial", Font.BOLD, 14));

        g.drawString("Bet: " + betAmount, 200, 320);
        
        g.dispose();
    
        setClipboardImage(image);;
    }

    private static String[] spinSlotsWithWildcard() {
        Random rand = new Random();
        String[] result = new String[3];

        for (int i = 0; i < 3; i++) {
            result[i] = symbols[rand.nextInt(symbols.length)];
        }
        return result;
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
