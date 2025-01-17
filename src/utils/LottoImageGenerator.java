package utils;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.awt.datatransfer.Clipboard;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.io.IOException;
import java.text.DecimalFormat;

public class LottoImageGenerator {

    private static final Color TEXT_COLOR = new Color(50, 50, 50);
    private static final Color WIN_COLOR = new Color(50, 200, 50);
    private static final Color LOSE_COLOR = new Color(200, 50, 50);
    private static final Color BALL_COLOR = new Color(255, 200, 50);

    public static void main(String[] args) {
        int[] drawnNumbers = {5, 13, 22, 31, 44, 50};
        int[] playerNumbers = {5, 10, 15, 31, 44, 50};
        int winAmount = 5000;
        int totalBalance = 15000;
        String playerName = "John Doe";

        LottoImageGenerator.drawLottoResults(drawnNumbers, playerNumbers, winAmount, 50, totalBalance, playerName, 20000000);

        System.out.println("Lotto image generated and copied to clipboard!");
    }

    public static void drawLottoResults(int[] drawnNumbers, int[] playerNumbers, int winAmount, int betAmount, int totalBalance, String playerName, int prizePool) {
        int width = 340;
        int height = 400;

        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        Paint gradient = GradientGenerator.generateGradientFromUsername(playerName, false, 340, 400);
        g.setPaint(gradient);
        g.fillRect(0, 0, width, height);

        DecimalFormat formatter = new DecimalFormat("#,###");
        String formattedPrizePool = formatter.format(prizePool);

        g.setColor(TEXT_COLOR);
        g.setFont(new Font("Arial", Font.BOLD, 24));
        g.drawString("Lotto prize pool: " + formattedPrizePool, 15, 25);
        g.setFont(new Font("Arial", Font.PLAIN, 20));
        g.drawString("Player: " + playerName, 15, 50);
        g.drawString("Total Balance: " + totalBalance, 15, 75);


        drawLotteryDrum(g, drawnNumbers, 150, 200);

        drawWinningTube(g, drawnNumbers, 275, 100);

        drawPlayerNumbers(g, drawnNumbers, playerNumbers, 150, 355);

        g.setFont(new Font("Arial", Font.BOLD, 20));
        if (winAmount > 0) {
            g.setColor(WIN_COLOR);
            g.drawString("You won: " + winAmount, 20, 325);
        } else {
            g.setColor(LOSE_COLOR);
            g.drawString("You lost: " + winAmount, 20, 325);
        }

        g.setColor(Color.darkGray);
        g.drawString("Bet amount: " + betAmount, 20, 345);

        g.dispose();

        setClipboardImage(image);
    }

    private static void drawPlayerNumbers(Graphics2D g, int[] drawnNumbers, int[] playerNumbers, int x, int y) {
        for (int i = 0; i < playerNumbers.length; i++) {
            boolean isHit = false;
            for (int drawnNumber : drawnNumbers) {
                if (playerNumbers[i] == drawnNumber) {
                    isHit = true;
                    break;
                }
            }
            g.setColor(isHit ? WIN_COLOR : LOSE_COLOR);
            g.fillRoundRect( 20 + i * 45, y, 40, 40, 10, 10);
            g.setColor(Color.WHITE);
            g.setFont(new Font("Arial", Font.BOLD, 16));
            g.drawString(String.valueOf(playerNumbers[i]), 20 + i * 45 + 12, y + 25);
        }
    }

    private static void drawWinningTube(Graphics2D g, int[] drawnNumbers, int x, int y) {
        
        g.setColor(new Color(100, 100, 100, 200));
        g.fillRect(x-10, y-30, 60, 270);

        for (int i = 0; i < drawnNumbers.length; i++) {
            g.setColor(BALL_COLOR);
            g.fillOval(x, y + i * 43 - 23, 40, 40);
            g.setColor(Color.BLACK);
            g.setFont(new Font("Arial", Font.BOLD, 14));
            g.drawString(String.valueOf(drawnNumbers[i]), x + 8, y + i * 43);
        }
    }

    private static void drawLotteryDrum(Graphics2D g, int[] numbers, int centerX, int centerY) {
        int radius = 105;
        int ballRadius = 15;

        g.setColor(new Color(100, 100, 100, 200));
        g.fillOval(centerX - radius, centerY - radius, radius * 2, radius * 2);

        for (int i = 1; i <= 49; i++) {
            boolean isDrawn = false;
            for (int drawnNumber : numbers) {
                if (i == drawnNumber) {
                    isDrawn = true;
                    break;
                }
            }

            if (isDrawn) {
                continue;
            }

            double angle = Math.random() * 2 * Math.PI;
            double distance = Math.random() * (radius - ballRadius);
            int ballX = centerX + (int) (Math.cos(angle) * distance) - ballRadius;
            int ballY = centerY + (int) (Math.sin(angle) * distance) - ballRadius;

            g.setColor(BALL_COLOR);
            g.fillOval(ballX, ballY, ballRadius * 2, ballRadius * 2);
            g.setColor(Color.BLACK);
            g.setFont(new Font("Arial", Font.BOLD, 14));
            g.drawString(String.valueOf(i), ballX + 7, ballY + 20);
        }
    }

    private static void setClipboardImage(final BufferedImage image) {
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