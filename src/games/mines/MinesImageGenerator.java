package games.mines;

import javax.imageio.ImageIO;

import utils.GradientGenerator;
import utils.ImageUtils;

import java.awt.*;
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

        Paint gradient = GradientGenerator.generateGradientFromUsername(username, false, 220, 330);

        g.setPaint(gradient);
        g.fillRect(0, 0, 220, 330);

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
                } else if (bombs[row][col] && gameStatus != null) {
                    try {
                        g.setColor(Color.GRAY);
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
                    Paint darkGradient = GradientGenerator.generateGradientFromUsername(username, true, x + TILE_SIZE, y + TILE_SIZE, x, y);
                    
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

        ImageUtils.drawUserAvatar(g, username, 150, 240, 40, 40);

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

            FontMetrics gameStatusMetrics = g.getFontMetrics();
            int gameStatusX = (width - gameStatusMetrics.stringWidth(gameStatus)) / 2;
            int gameStatusY = 100;
            g.drawString(gameStatus, gameStatusX, gameStatusY);
        }

            g.setFont(new Font("Arial", Font.BOLD, 10));
            g.setColor(Color.WHITE);
            g.drawString("Total: " + totalBalance, 140, 310);

        g.dispose();
        ImageUtils.setClipboardImage(image);
    }

}