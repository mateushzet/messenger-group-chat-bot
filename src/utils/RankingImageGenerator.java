package utils;

import java.awt.*;
import java.awt.datatransfer.*;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.util.List;
import java.util.Map;

public class RankingImageGenerator {

    public static void generateRankingImage(List<Map.Entry<String, Integer>> sortedUsers, String reguesterName) {
        int imageWidth = 600;
        int imageHeight = 100 + sortedUsers.size() * 50;
        BufferedImage image = new BufferedImage(imageWidth, imageHeight, BufferedImage.TYPE_INT_RGB);

        Graphics2D g = image.createGraphics();

        Color color1 = generateColorFromUsername(reguesterName, 1);
        Color color2 = generateColorFromUsername(reguesterName, 2);
    
        GradientPaint gradient = new GradientPaint(0, 0, color1, 600, 646, color2);

        g.setPaint(gradient);
        g.fillRect(0, 0, imageWidth, imageHeight);

        g.setFont(new Font("Arial", Font.BOLD, 32));
        g.setColor(Color.BLACK);
        g.drawString("User Ranking", 20, 50);

        int yPosition = 100;
        for (int i = 0; i < sortedUsers.size(); i++) {
            Map.Entry<String, Integer> entry = sortedUsers.get(i);
            String username = entry.getKey();
            int balance = entry.getValue();

            if (i == 0) {
                g.setColor(new Color(218, 165, 32));
            } else if (i == 1) {
                g.setColor(new Color(169, 169, 169));
            } else if (i == 2) {
                g.setColor(new Color(139, 69, 19));
            } else {
                g.setColor(new Color(64, 64, 64));
            }

            // Rysowanie tekstu: miejsce, nazwa użytkownika i saldo
            g.drawString((i + 1) + ". " + username + " - " + balance + " coins", 20, yPosition);

            yPosition += 50;
        }

        g.dispose();
        saveImageToClipboard(image);
    }

    public static void saveImageToClipboard(BufferedImage image) {
        TransferableImage transferable = new TransferableImage(image);
        Clipboard clipboard = Toolkit.getDefaultToolkit().getSystemClipboard();
        clipboard.setContents(transferable, null);
        System.out.println("Image saved to clipboard.");
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

    private static Color generateColorFromUsername(String username, int seed) {
        int hash = (username + seed).hashCode();
        int colorComponent1 = (hash >>> 16) & 0xFF;
        int colorComponent2 = (hash >>> 8) & 0xFF;
        int colorComponent3 = (hash) & 0xFF;
    
        int red1 = Math.min((colorComponent1 * 2) % 256 + 100, 255);
        int green1 = Math.min((colorComponent2 * 2) % 256 + 100, 255);
        int blue1 = Math.min((colorComponent3 * 2) % 256 + 100, 255);
    
        int red2 = Math.min((colorComponent1 + 50) % 256 + 100, 255);
        int green2 = Math.min((colorComponent2 + 100) % 256 + 100, 255);
        int blue2 = Math.min((colorComponent3 + 150) % 256 + 100, 255);
    
        Color color1 = new Color(red1, green1, blue1);
        Color color2 = new Color(red2, green2, blue2);
    
        return seed == 1 ? color1 : color2;
    }

}