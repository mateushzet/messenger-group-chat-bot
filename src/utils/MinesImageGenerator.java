package utils;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.datatransfer.Clipboard;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.net.URL;
import java.util.List;

public class MinesImageGenerator {

    private static final int BOARD_SIZE = 5;
    private static final int TILE_SIZE = 40;
    private static final int MARGIN = 10;
    
    private static final String BOMB_IMAGE_URL = "https://cdn-icons-png.flaticon.com/128/595/595582.png";
    private static final Color GREEN_COLOR = new Color(50, 200, 50);
    private static final Color RED_COLOR = new Color(200, 50, 50);

    public static void generateMinesweeperImage(boolean[][] revealed, boolean[][] bombs, String username, List<String> status, String gameStatus, int totalBalance) {
        
        int width = (BOARD_SIZE * TILE_SIZE) + 2 * MARGIN;
        int height = (BOARD_SIZE * TILE_SIZE) + 13 * MARGIN;
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();
        
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        
        g.setColor(new Color(255, 255, 255));
        g.fillRect(0, 0, width, height);

        Color color1 = generateColorFromUsername(username, 1);
        Color color2 = generateColorFromUsername(username, 2);

        GradientPaint gradient = new GradientPaint(0, 0, color1, 220, 330, color2);

        g.setPaint(gradient);
        g.fillRect(0, 0, 220, 330);

        Color darkenedColor1 = darkenColor(color1, 0.7f);
        Color darkenedColor2 = darkenColor(color2, 0.7f);

        for (int row = 0; row < BOARD_SIZE; row++) {
            for (int col = 0; col < BOARD_SIZE; col++) {

                int x = MARGIN + col * TILE_SIZE;
                int y = MARGIN + row * TILE_SIZE;

                if (revealed[row][col]) {

                    if (bombs[row][col]) {
                        try {
                            g.setColor(RED_COLOR);
                            g.fillRect(x, y, TILE_SIZE, TILE_SIZE);

                            BufferedImage bombImage = ImageIO.read(new URL(BOMB_IMAGE_URL));
                            g.drawImage(bombImage, x, y, TILE_SIZE, TILE_SIZE, null);

                            g.setColor(Color.BLACK);
                            g.drawRect(x, y, TILE_SIZE, TILE_SIZE);
                        } catch (IOException e) {
                            g.setColor(Color.RED);
                            g.fillRect(x, y, TILE_SIZE, TILE_SIZE);
                        }
                    } else {
                        g.setColor(GREEN_COLOR);
                        g.fillRect(x, y, TILE_SIZE, TILE_SIZE);

                        g.setColor(Color.BLACK);
                        g.drawRect(x, y, TILE_SIZE, TILE_SIZE);
                    }
                } else {
                    GradientPaint darkGradient = new GradientPaint(x, y, darkenedColor1, x + TILE_SIZE, y + TILE_SIZE, darkenedColor2);
                    g.setPaint(darkGradient);
                    g.fillRect(x, y, TILE_SIZE, TILE_SIZE);
                    g.setColor(Color.BLACK);
                    g.drawRect(x, y, TILE_SIZE, TILE_SIZE);
                    
                    int fieldNumber = row * BOARD_SIZE + col + 1;
                    g.setColor(Color.BLACK);
                    g.setFont(new Font("Arial", Font.BOLD, 12));
                    String fieldText = String.valueOf(fieldNumber);
                    FontMetrics metrics = g.getFontMetrics();
                    int textX = x + (TILE_SIZE - metrics.stringWidth(fieldText)) / 2;
                    int textY = y + (TILE_SIZE + metrics.getHeight()) / 2 - 5;
                    g.drawString(fieldText, textX, textY);
                }
            }
        }   

        int statusY = height - 95;
        int statusHeight = 110;
        g.setColor(new Color(0, 0, 0, 128));
        g.fillRect(MARGIN, statusY - 20, width - 2 * MARGIN, statusHeight);
        
        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 16));
        for (int i = 0; i < status.size(); i++) {
            String line = status.get(i);
            g.drawString(line, MARGIN + 10, statusY + (i * 20));
        }

        if(gameStatus != null){

            g.setColor(new Color(0, 0, 0, 128));
            g.fillRect(0, 80, 330, 30);

            if(gameStatus.equals("Game over!")) g.setColor(RED_COLOR);
            else  g.setColor(GREEN_COLOR);
            g.setFont(new Font("Arial", Font.BOLD, 20));
            g.drawString(gameStatus, 30, 100);
            }

            g.setFont(new Font("Arial", Font.BOLD, 10));
            g.setColor(Color.WHITE);
            g.drawString("Total: " + totalBalance, 140, 310);

        g.dispose();
        setClipboardImage(image);
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

    private static Color generateColorFromUsername(String username, int seed) {
        int hash = (username + seed).hashCode();
        int colorComponent1 = (hash >>> 16) & 0xFF;
        int colorComponent2 = (hash >>> 8) & 0xFF;
        int colorComponent3 = (hash) & 0xFF;
    
        int red1 = (colorComponent1 + 128) % 256;
        int green1 = (colorComponent2 + 128) % 256;
        int blue1 = (colorComponent3 + 128) % 256;
    
        int red2 = (colorComponent1 + 180) % 256;
        int green2 = (colorComponent2 + 180) % 256;
        int blue2 = (colorComponent3 + 180) % 256;
    
        red1 = Math.min(red1 + 80, 255);
        green1 = Math.min(green1 + 80, 255);
        blue1 = Math.min(blue1 + 80, 255);
    
        red2 = Math.min(red2 + 80, 255);
        green2 = Math.min(green2 + 80, 255);
        blue2 = Math.min(blue2 + 80, 255);
    
        Color color1 = new Color(red1, green1, blue1);
        Color color2 = new Color(red2, green2, blue2);
    
        return seed == 1 ? color1 : color2;
    }

    private static Color darkenColor(Color color, float factor) {
        int r = (int) (color.getRed() * factor);
        int g = (int) (color.getGreen() * factor);
        int b = (int) (color.getBlue() * factor);
    
        r = Math.max(0, Math.min(255, r));
        g = Math.max(0, Math.min(255, g));
        b = Math.max(0, Math.min(255, b));
    
        return new Color(r, g, b);
    }

}
