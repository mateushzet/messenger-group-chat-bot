package games.slots;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.net.URL;
import java.util.Random;
import javax.imageio.ImageIO;

import utils.GradientGenerator;
import utils.ImageUtils;


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
    private static final int IMAGE_HEIGHT = 330;
    private static final int IMAGE_WIDTH = 300;
    private static final int PADDING = 30;
    

    public static void generateSlotsResultImage(int[] result, String playerName, int amount, int totalBalance, int betAmount, int jackpotAmount) {
        String[] resultsImages = {symbols[result[0]], symbols[result[1]], symbols[result[2]]};
        
        BufferedImage image = new BufferedImage(IMAGE_HEIGHT, IMAGE_HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();
    
        Paint gradient = GradientGenerator.generateGradientFromUsername(playerName, false, IMAGE_WIDTH, IMAGE_HEIGHT);
        
        int symbolWidth = IMAGE_WIDTH / 3;
        int symbolHeight = IMAGE_WIDTH / 3;
    
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
                    g.drawLine((i + 1) * symbolWidth, 0, (i + 1) * symbolWidth, IMAGE_HEIGHT);
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
                    g.drawLine((i + 1) * symbolWidth, symbolWidth - (symbolHeight / 2), (i + 1) * symbolWidth, IMAGE_HEIGHT);
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
                    g.drawLine((i + 1) * symbolWidth, 2 * symbolWidth - (symbolHeight / 2), (i + 1) * symbolWidth, IMAGE_HEIGHT);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        
        g.setPaint(gradient);
        g.fillRect(0, 200, 300, 200);

        drawInfoPanel(g, playerName, amount, totalBalance, betAmount, jackpotAmount);

        g.dispose();
    
        ImageUtils.setClipboardImage(image);;
    }

    private static void drawInfoPanel(Graphics2D g, String playerName, int amount, int totalBalance, int betAmount, int jackpotAmount) {
        int panelY = IMAGE_HEIGHT - 150;
        g.setColor(new Color(0, 0, 0, 150));
        g.fillRoundRect(PADDING, panelY + 20, IMAGE_WIDTH - 2 * PADDING, 140, 20, 20);

        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 24));

        FontMetrics metrics = g.getFontMetrics();
        String winLoseText = amount > 0 ? "WIN " + amount : "LOSE " + amount;
        int textWidth = metrics.stringWidth(winLoseText);
        int x = (IMAGE_WIDTH - textWidth) / 2;

        if (amount > 0) {
            g.setColor(GREEN_COLOR);
        } else {
            g.setColor(RED_COLOR);
        }
        g.drawString(winLoseText, x, panelY + 45);

        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.PLAIN, 18));
        g.drawString(playerName, PADDING + 10, panelY + 70);
        g.drawString("Total: " + totalBalance, PADDING + 10, panelY + 100);
        g.drawString("Jackpot: " + jackpotAmount, PADDING + 10, panelY + 130);

        g.setFont(new Font("Arial", Font.BOLD, 16));
        g.drawString("Bet: " + betAmount, IMAGE_WIDTH - PADDING - 100, panelY + 130);
    }


    private static String[] spinSlotsWithWildcard() {
        Random rand = new Random();
        String[] result = new String[3];

        for (int i = 0; i < 3; i++) {
            result[i] = symbols[rand.nextInt(symbols.length)];
        }
        return result;
    }

}
