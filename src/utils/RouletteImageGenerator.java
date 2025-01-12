package utils;

import java.util.Queue;
import java.util.LinkedList;
import java.io.IOException;
import java.awt.*;
import java.awt.datatransfer.Clipboard;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.geom.Arc2D;
import java.awt.geom.Ellipse2D;
import java.awt.image.BufferedImage;




public class RouletteImageGenerator  {

    private static final Color DARK_GRAY = new Color(25, 25, 25);
    private static final Color WIN_COLOR = new Color(50, 200, 50);
    private static final Color LOSE_COLOR = new Color(200, 50, 50);
    private static final Color TEXT_COLOR = new Color(200, 200, 200);
    private static final Color HISTORY_COLOR_NULL = new Color(100, 100, 100);
    private static final Color GREEN_COLOR = new Color(50, 200, 50);
    private static final Color BLACK_COLOR = new Color(60, 60, 60);
    private static final Color RED_COLOR = new Color(200, 50, 50);
    private static final Color HIGHLIGHT_COLOR = new Color(255, 215, 0);

public static void generateImage(int result, int winnings, int balance, String username, int betAmount ,Queue<Integer> rouletteHistory) {

    BufferedImage image = new BufferedImage(600, 646, BufferedImage.TYPE_INT_RGB);
    Graphics2D g = image.createGraphics();


   Color color1 = generateColorFromUsername(username, 1);
   Color color2 = generateColorFromUsername(username, 2);

   GradientPaint gradient = new GradientPaint(0, 0, color1, 600, 600, color2);

   g.setPaint(gradient);
   g.fillRect(0, 0, 600, 600);

    int centerX = 300, centerY = 300, radius = 250;
    drawRouletteWheel(g, centerX, centerY, radius, result);

    g.setFont(new Font("Arial", Font.BOLD, 50));

    g.setColor(winnings <= 0 ? LOSE_COLOR : WIN_COLOR);
    String winLoseText = winnings <= 0 ? "LOSE " + winnings : "WIN " + winnings;
    g.drawString(winLoseText, 15, 50);
    
    g.setFont(new Font("Arial", Font.BOLD, 30));

    g.setColor(TEXT_COLOR);
    String betAmountText = "Bet: " + betAmount;
    g.drawString(betAmountText, 400, 30);

    g.setFont(new Font("Arial", Font.BOLD, 50));

    String balanceText = "Total: " + balance;
    g.setColor(TEXT_COLOR);
    g.drawString(balanceText, 10, 590);

    g.setColor(TEXT_COLOR);
    g.setFont(new Font("Arial", Font.PLAIN, 32));
    g.drawString(username, 330, 590);

    drawHistory(g, rouletteHistory);

    g.dispose();

    setClipboardImage(image);
    System.out.println("Image saved to clipboard.");
}

private static void drawRouletteWheel(Graphics2D g, int centerX, int centerY, int radius, int result) {
    int segments = 13;
    double anglePerSegment = 360.0 / segments;

    g.setFont(new Font("Arial", Font.BOLD, 48));

    for (int i = 0; i < segments; i++) {
        if (i == 0) {
            g.setColor(GREEN_COLOR);
        } else if (i % 2 == 0) {
            g.setColor(BLACK_COLOR);
        } else {
            g.setColor(RED_COLOR);
        }

        Arc2D.Double arc = new Arc2D.Double(
            centerX - radius, centerY - radius, 
            radius * 2, radius * 2, 
            i * anglePerSegment, anglePerSegment, 
            Arc2D.PIE
        );
        g.fill(arc);

        g.setColor(Color.WHITE);
        double theta = Math.toRadians(i * anglePerSegment + anglePerSegment / 2);
        int textX = centerX + (int) (Math.cos(theta) * (radius - 50));
        int textY = centerY - (int) (Math.sin(theta) * (radius - 50));
        g.drawString(String.valueOf(i), textX - 12, textY + 8);
    }

    g.setStroke(new BasicStroke(6));
    g.setColor(HIGHLIGHT_COLOR);
    double highlightStartAngle = result * anglePerSegment;
    Arc2D.Double highlight = new Arc2D.Double(
        centerX - radius, centerY - radius, 
        radius * 2, radius * 2, 
        highlightStartAngle, anglePerSegment, 
        Arc2D.PIE
    );
    g.draw(highlight);

    g.setColor(DARK_GRAY);
    g.setStroke(new BasicStroke(15));
    g.drawOval(centerX - radius, centerY - radius, radius * 2, radius * 2);

    double theta = Math.toRadians(result * anglePerSegment + anglePerSegment / 2);
    int ballX = centerX + (int) (Math.cos(theta) * (radius - 130));
    int ballY = centerY - (int) (Math.sin(theta) * (radius - 130));
    g.setColor(Color.WHITE);
    g.fill(new Ellipse2D.Double(ballX - 25, ballY - 25, 50, 50));
}

private static void drawHistory(Graphics2D g, Queue<Integer> rouletteHistory) {
    int maxHistorySize = 13;
    int squareSize = 45;
    int padding = 2;
    int historyStartX = 600 - (maxHistorySize * (squareSize + padding));
    int historyStartY = 600;


    LinkedList<Integer> paddedHistory = new LinkedList<>(rouletteHistory);
    while (paddedHistory.size() < maxHistorySize) {
        paddedHistory.addFirst(null);
    }


    g.setColor(Color.WHITE);
    g.fillRect(historyStartX - 5, historyStartY - 1, maxHistorySize * (squareSize + padding), squareSize + 10);


    int index = 0;
    for (Integer number : paddedHistory) {
        int x = historyStartX + index * (squareSize + padding);


        Color color;
        if (number == null) {
            color = HISTORY_COLOR_NULL;
        } else if (number == 0) {
            color = GREEN_COLOR;
        } else if (number % 2 == 0) {
            color = BLACK_COLOR;
        } else {
            color = RED_COLOR;
        }

        g.setColor(color);
        g.fillRect(x, historyStartY, squareSize, squareSize);
        
        if (index == maxHistorySize - 1) {
            g.setColor(Color.YELLOW);
            g.setStroke(new BasicStroke(4));
            g.drawRect(x - 1, historyStartY - 1, squareSize + 2, squareSize + 2);
        }

        if (number != null) {
            g.setColor(Color.WHITE);
            String text = String.valueOf(number);
            int textWidth = g.getFontMetrics().stringWidth(text);
            int textX = x + (squareSize - textWidth) / 2;
            int textY = historyStartY + (squareSize + g.getFontMetrics().getAscent()) / 2 - 5;
            g.drawString(text, textX, textY);
        }

        index++;
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

private static Color generateColorFromUsername(String username, int seed) {

    int hash = (username + seed).hashCode();
    int colorComponent1 = (hash >>> 16) & 0xFF;
    int colorComponent2 = (hash >>> 8) & 0xFF;
    int colorComponent3 = (hash) & 0xFF;

    int red1 = (colorComponent1 * 2) % 256;
    int green1 = (colorComponent2 * 2) % 256;
    int blue1 = (colorComponent3 * 2) % 256;

    int red2 = (colorComponent1 + 50) % 256;
    int green2 = (colorComponent2 + 100) % 256;
    int blue2 = (colorComponent3 + 150) % 256;

    red1 = red1 / 2;
    green1 = green1 / 2;
    blue1 = blue1 / 2;

    red2 = red2 / 2;
    green2 = green2 / 2;
    blue2 = blue2 / 2;

    Color color1 = new Color(red1, green1, blue1);
    Color color2 = new Color(red2, green2, blue2);

    return seed == 1 ? color1 : color2;
}

}
