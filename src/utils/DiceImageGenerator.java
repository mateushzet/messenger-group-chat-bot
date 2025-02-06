package utils;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.text.DecimalFormat;

public class DiceImageGenerator {

    private static final Color TEXT_COLOR = new Color(255, 255, 255);
    private static final Color WIN_COLOR = new Color(50, 200, 50);
    private static final Color LOSE_COLOR = new Color(200, 50, 50);
    private static final Color BALL_COLOR = new Color(255, 200, 50);
    private static final Color BLACK_BACKGROUND = new Color(0, 0, 0, 180);

    public static void drawDiceResults(int[] diceValues, int betAmount, int totalBalance, String playerName, double multiplier, boolean showReward) {
        int width = 500;
        int height = 630;

        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        Paint gradient = GradientGenerator.generateGradientFromUsername(playerName, false, width, height);
        g.setPaint(gradient);
        g.fillRect(0, 0, width, height);

        DecimalFormat formatter = new DecimalFormat("#,###");
        String formattedBalance = formatter.format(totalBalance);

        g.setColor(BLACK_BACKGROUND);
        g.fillRect(0, 0, width, 80);

        g.setColor(TEXT_COLOR);
        g.setFont(new Font("Arial", Font.BOLD, 20));
        g.drawString(playerName, 15, 22);
        g.setFont(new Font("Arial", Font.PLAIN, 18));
        g.drawString("Total Balance: " + formattedBalance, 15, 47);
        g.drawString("Bet amount: " + betAmount, 15, 72);

        drawDice(g, diceValues, 45, 150);

        String multiplierText = "Multiplier: x" + multiplier;
        FontMetrics metrics = g.getFontMetrics();
        int textWidth = metrics.stringWidth(multiplierText);
        int textHeight = metrics.getHeight();
        
        int xPosition = (width - textWidth) / 2;
        int yPosition = 120;

        g.setColor(new Color(0, 0, 0, 180));
        g.fillRect(xPosition - 5, yPosition - textHeight, textWidth + 40, textHeight + 10);

        g.setFont(new Font("Arial", Font.BOLD, 19));
        g.setColor(multiplier > 1 ? WIN_COLOR : LOSE_COLOR);
        g.drawString(multiplierText, xPosition, yPosition);



        if(showReward){
        String rewardText = "" + (int)(multiplier * betAmount);
        textWidth = metrics.stringWidth(rewardText);
        xPosition = (220 - textWidth) / 2 + 277;
        yPosition = 420;

        g.setColor(new Color(0, 0, 0, 180));
        g.fillRect(xPosition - 35, yPosition - textHeight - 30, textWidth + 105, 2 * textHeight + 20);
        g.setColor(multiplier > 1 ? WIN_COLOR : LOSE_COLOR);
        g.setFont(new Font("Arial", Font.BOLD, 24));
        g.drawString("REWARD", 350, 390);
        g.drawString(rewardText, xPosition, yPosition);

        g.setFont(new Font("Arial", Font.PLAIN, 14));
        g.setColor(TEXT_COLOR);
        }

        drawMultiplierInfo(g);

        g.dispose();

        ImageUtils.setClipboardImage(image);
    }

    private static void drawDice(Graphics2D g, int[] diceValues, int startX, int startY) {
        int diceSize = 60;
        int margin = 10;

        for (int i = 0; i < diceValues.length; i++) {
            int x = startX + i * (diceSize + margin);
            drawDiceFace(g, x, startY, diceValues[i], diceSize, 11);
            g.drawString(String.valueOf(i + 1), x + 25, startY + diceSize + 25);
        }
    }

    private static void drawDiceFace(Graphics2D g, int x, int y, int value, int size, int dotSize) {
        g.setColor(Color.WHITE);
        g.fillRoundRect(x, y, size, size, 15, 15);
        g.setColor(Color.BLACK);
        g.drawRoundRect(x, y, size, size, 15, 15);

        int[][] positions = {
            {},
            {2, 2},
            {0, 0, 4, 4},
            {0, 0, 2, 2, 4, 4},
            {0, 0, 0, 4, 4, 0, 4, 4},
            {0, 0, 0, 4, 2, 2, 4, 0, 4, 4},
            {0, 0, 0, 2, 0, 4, 4, 0, 4, 2, 4, 4}
        };

        int offset = size / 7;
        for (int i = 0; i < positions[value].length; i += 2) {
            int dx = x + offset + positions[value][i] * offset;
            int dy = y + offset + positions[value][i + 1] * offset;
            g.fillOval(dx, dy, dotSize, dotSize);
        }

    }

    private static void drawMultiplierInfo(Graphics2D g) {

        g.setColor(new Color(0, 0, 0, 180));
        g.fillRect(10, 290, 270, 355);

        int startX = 20;
        int startY = 300;
        int diceSize = 25;
        int margin = 10;

        Object[][] combinations = {
            {new int[]{1, 1, 1}, 0.1},
            {new int[]{1, 1, 2, 2, 2}, 0.2},
            {new int[]{1, 1, 1, 1}, 1.5},
            {new int[]{1, 1, 1, 2, 2, 2}, 1.5},
            {new int[]{1, 1, 2, 2, 3, 3}, 2.},
            {new int[]{1, 1, 1, 1, 1}, 3.},
            {new int[]{1, 2, 3, 4, 5, 6}, 5.},
            {new int[]{1, 1, 1, 1, 1, 1}, 5.}
        };



        for (Object[] combination : combinations) {
            int[] pattern = (int[]) combination[0];
            double multiplier = (double) combination[1];

            drawDiceFace(g, startX, startY, pattern[0], diceSize, 5);
            int offsetX = diceSize + margin;

            for (int i = 1; i < pattern.length; i++) {
                drawDiceFace(g, startX + i * offsetX, startY, pattern[i], diceSize, 5);
            }

            g.setFont(new Font("Arial", Font.PLAIN, 14));
            g.setColor(TEXT_COLOR);
            g.drawString("x" + multiplier, startX + pattern.length * offsetX + 5, startY + diceSize / 2);
            startY += 40;
        }

    }

}