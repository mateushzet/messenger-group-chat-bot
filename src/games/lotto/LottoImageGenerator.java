package games.lotto;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.text.DecimalFormat;

import utils.GradientGenerator;
import utils.ImageUtils;

public class LottoImageGenerator {

    private static final Color TEXT_COLOR = new Color(255, 255, 255);
    private static final Color WIN_COLOR = new Color(50, 200, 50);
    private static final Color LOSE_COLOR = new Color(200, 50, 50);
    private static final Color BALL_COLOR = new Color(255, 200, 50);
    private static final Color BLACK_BACKGROUND = new Color(0, 0, 0, 180);

    public static void drawLottoResults(int[] drawnNumbers, int[] playerNumbers, int winAmount, int betAmount, int totalBalance, String playerName, int prizePool) {
        int width = 340;
        int height = 450;

        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        Paint gradient = GradientGenerator.generateGradientFromUsername(playerName, false, 340, 400);
        g.setPaint(gradient);
        g.fillRect(0, 0, width, height);

        ImageUtils.drawUserAvatar(g, playerName, 260, 0, 80, 80);

        DecimalFormat formatter = new DecimalFormat("#,###");
        String formattedPrizePool = formatter.format(prizePool);

        g.setColor(BLACK_BACKGROUND);
        g.fillRect(0, 0, width, 80);

        g.setColor(BLACK_BACKGROUND);
        g.fillRect(0, 350, 340, 100);

        g.setColor(TEXT_COLOR);
        g.setFont(new Font("Arial", Font.BOLD, 20));
        g.drawString("Lotto prize pool: " + formattedPrizePool, 15, 22);
        g.setFont(new Font("Arial", Font.PLAIN, 18));
        g.drawString("Player: " + playerName, 15, 47);
        g.drawString("Total Balance: " + totalBalance, 15, 72);

        drawLotteryDrum(g, drawnNumbers, 150, 200);
        drawWinningTube(g, drawnNumbers, 275, 100);
        drawPlayerNumbers(g, drawnNumbers, playerNumbers, 150, 355);

        g.setFont(new Font("Arial", Font.BOLD, 19));
        if (winAmount > 0) {
            g.setColor(WIN_COLOR);
            g.drawString("You won: " + winAmount, 20, 372);
        } else {
            g.setColor(LOSE_COLOR);
            g.drawString("You lost: " + winAmount, 20, 372);
        }

        g.setColor(Color.WHITE);
        g.drawString("Bet amount: " + betAmount, 20, 398);

        g.dispose();

        ImageUtils.setClipboardImage(image);
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
            g.fillRoundRect(20 + i * 52, y + 50, 40, 40, 10, 10);
            g.setColor(Color.WHITE);
            g.setFont(new Font("Arial", Font.BOLD, 16));
            g.drawString(String.valueOf(playerNumbers[i]), 20 + i * 52 + 12, y + 75);
        }
    }

    private static void drawWinningTube(Graphics2D g, int[] drawnNumbers, int x, int y) {
        g.setColor(new Color(100, 100, 100, 200));
        g.fillRect(x + 10, y - 20, 60, 270);

        for (int i = 0; i < drawnNumbers.length; i++) {
            g.setColor(BALL_COLOR);
            g.fillOval(x + 15, y + i * 43 - 15, 40, 40);
            g.setColor(Color.BLACK);
            g.setFont(new Font("Arial", Font.BOLD, 14));
            g.drawString(String.valueOf(drawnNumbers[i]), x + 25, y + 5 + i * 43);
        }
    }

    private static void drawLotteryDrum(Graphics2D g, int[] numbers, int centerX, int centerY) {
        int radius = 120;
        int ballRadius = 15;

        g.setColor(new Color(100, 100, 100, 200));
        g.fillOval(centerX - radius - 7, centerY - radius + 15, radius * 2, radius * 2);

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

            ballX -= 7;
            ballY += 15;

            g.setColor(BALL_COLOR);
            g.fillOval(ballX, ballY, ballRadius * 2, ballRadius * 2);
            g.setColor(Color.BLACK);
            g.setFont(new Font("Arial", Font.BOLD, 14));
            g.drawString(String.valueOf(i), ballX + 7, ballY + 20);
        }
    }

}
