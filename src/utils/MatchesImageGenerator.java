package utils;

import java.awt.*;
import java.awt.datatransfer.*;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.util.List;

public class MatchesImageGenerator {

    public static void generateMatchImage(List<String> matchTexts) {
        int imageWidth = 2000;
        int imageHeight = 150 + matchTexts.size() * 40;
        BufferedImage image = new BufferedImage(imageWidth, imageHeight, BufferedImage.TYPE_INT_RGB);
    
        Graphics2D g = image.createGraphics();
    
        g.setPaint(new GradientPaint(0, 0, Color.CYAN, 0, imageHeight, Color.BLUE));
        g.fillRect(0, 0, imageWidth, imageHeight);
    
        g.setFont(new Font("Arial", Font.BOLD, 24));
        g.setColor(Color.BLACK);
    
        g.drawString("Available Matches", 20, 50);
    
        int yPosition = 100;
        for (int i = 0; i < matchTexts.size(); i++) {
            String matchText = matchTexts.get(i);
    
            if (i % 2 == 0) {
                g.setColor(Color.WHITE);
            } else {
                g.setColor(Color.DARK_GRAY);
            }
    
            g.drawString(matchText, 20, yPosition);
    
            yPosition += 40;
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