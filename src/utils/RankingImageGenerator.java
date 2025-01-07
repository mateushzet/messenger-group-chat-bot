package utils;

import java.awt.*;
import java.awt.datatransfer.*;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.util.List;
import java.util.Map;

public class RankingImageGenerator {

    public static void generateRankingImage(List<Map.Entry<String, Integer>> sortedUsers) {
        int imageWidth = 600;
        int imageHeight = 100 + sortedUsers.size() * 50;
        BufferedImage image = new BufferedImage(imageWidth, imageHeight, BufferedImage.TYPE_INT_RGB);

        Graphics2D g = image.createGraphics();
        g.setColor(Color.WHITE);
        g.fillRect(0, 0, imageWidth, imageHeight);

        g.setFont(new Font("Arial", Font.BOLD, 32));
        g.setColor(Color.BLACK);
        g.drawString("User Ranking", 20, 50);

        int yPosition = 100;
        for (int i = 0; i < sortedUsers.size(); i++) {
            Map.Entry<String, Integer> entry = sortedUsers.get(i);
            String username = entry.getKey();
            int balance = entry.getValue();

            // Kolor tekstu dla pierwszej trójki
            if (i == 0) {
                g.setColor(new Color(255, 215, 0)); // Złoty dla 1. miejsca
            } else if (i == 1) {
                g.setColor(new Color(192, 192, 192)); // Srebrny dla 2. miejsca
            } else if (i == 2) {
                g.setColor(new Color(205, 127, 50)); // Brązowy dla 3. miejsca
            } else {
                g.setColor(Color.BLACK); // Czarny dla reszty
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
}