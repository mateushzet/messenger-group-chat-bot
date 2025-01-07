package utils;

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

public static void generateImage(int result, int winnings, int balance, String username) {

    BufferedImage image = new BufferedImage(600, 600, BufferedImage.TYPE_INT_RGB);
    Graphics2D g = image.createGraphics();

    g.setColor(Color.DARK_GRAY);
    g.fillRect(0, 0, 600, 600);

    int centerX = 300, centerY = 300, radius = 250;
    drawRouletteWheel(g, centerX, centerY, radius, result);

    g.setFont(new Font("Arial", Font.BOLD, 55));

    g.setColor(winnings <= 0 ? Color.RED : Color.GREEN);
    String winLoseText = winnings <= 0 ? "LOSE " + winnings : "WIN " + winnings;
    g.drawString(winLoseText, 15, 50);

    g.setFont(new Font("Arial", Font.BOLD, 50));

    String balanceText = "Total: " + balance;
    g.setColor(Color.LIGHT_GRAY);
    g.drawString(balanceText, 10, 590);

    g.setColor(Color.LIGHT_GRAY);
    g.setFont(new Font("Arial", Font.PLAIN, 32));
    g.drawString(username, 330, 590);

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
            g.setColor(Color.GREEN);
        } else if (i % 2 == 0) {
            g.setColor(Color.BLACK);
        } else {
            g.setColor(Color.RED);
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
    g.setColor(Color.YELLOW);
    double highlightStartAngle = result * anglePerSegment;
    Arc2D.Double highlight = new Arc2D.Double(
        centerX - radius, centerY - radius, 
        radius * 2, radius * 2, 
        highlightStartAngle, anglePerSegment, 
        Arc2D.PIE
    );
    g.draw(highlight);

    double theta = Math.toRadians(result * anglePerSegment + anglePerSegment / 2);
    int ballX = centerX + (int) (Math.cos(theta) * (radius - 130));
    int ballY = centerY - (int) (Math.sin(theta) * (radius - 130));
    g.setColor(Color.WHITE);
    g.fill(new Ellipse2D.Double(ballX - 25, ballY - 25, 50, 50));
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
