package utils;

import java.awt.*;
import java.awt.geom.RoundRectangle2D;
import java.awt.image.BufferedImage;
import java.util.Random;

public class MathQuestionImageGenerator {

    private static final int WIDTH = 350;
    private static final int HEIGHT = 200;
    private static final Font HEADER_FONT = new Font("Arial", Font.BOLD, 22);
    private static final Font QUESTION_FONT = new Font("Arial", Font.BOLD, 28);
    private static final Font HINT_FONT = new Font("Arial", Font.PLAIN, 16);
    private static final int CORNER_RADIUS = 20;
    private static final Random random = new Random();
    private static boolean isRandomPrizeEnabled = ConfigReader.isMathQuestionRandomPrizeEnabled();
    private static int randomPrizeMin = ConfigReader.getMathQuestionRandomPrizeMinCap();
    private static int randomPrizeMax = ConfigReader.getMathQuestionRandomPrizeMaxCap();
    private static int mathQuestionPrize = ConfigReader.getMathQuestionPrize();

    public static void generateMathQuestionImage(String question) {
        BufferedImage image = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = image.createGraphics();

        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        Color backgroundColor = getRandomPastelColor();
        g.setColor(backgroundColor);
        g.fillRect(0, 0, WIDTH, HEIGHT);

        g.setColor(Color.WHITE);
        g.setFont(HEADER_FONT);
        FontMetrics headerMetrics = g.getFontMetrics();
        String headerText = "Math question";
        int headerX = (WIDTH - headerMetrics.stringWidth(headerText)) / 2;
        int headerY = 40;
        g.drawString(headerText, headerX, headerY);

        Color mathBackgroundColor = brightenColor(backgroundColor, 0.2f);
        int mathBackgroundY = 70;
        int mathBackgroundHeight = 60;
        g.setColor(mathBackgroundColor);
        g.fill(new RoundRectangle2D.Double(20, mathBackgroundY, WIDTH - 40, mathBackgroundHeight, CORNER_RADIUS, CORNER_RADIUS));

        g.setColor(Color.BLACK);
        g.setFont(QUESTION_FONT);
        FontMetrics questionMetrics = g.getFontMetrics();
        int questionX = (WIDTH - questionMetrics.stringWidth(question)) / 2;
        int questionY = mathBackgroundY + (mathBackgroundHeight / 2) + (questionMetrics.getAscent() / 2);
        g.drawString(question, questionX, questionY);

        g.setColor(Color.DARK_GRAY);
        g.setFont(HINT_FONT);
        FontMetrics rewardMetrics = g.getFontMetrics();
        String rewardText;
        if (isRandomPrizeEnabled) {
            rewardText = "Reward: " + randomPrizeMin + "-" + randomPrizeMax + " coins";
        } else {
            rewardText = "Reward: " + mathQuestionPrize + " coins";
        }
        int rewardX = (WIDTH - rewardMetrics.stringWidth(rewardText)) / 2;
        int rewardY = questionY + 45;
        g.drawString(rewardText, rewardX, rewardY);

        FontMetrics hintMetrics = g.getFontMetrics();
        String hintText = "Use /answer <number> to respond";
        int hintX = (WIDTH - hintMetrics.stringWidth(hintText)) / 2;
        int hintY = HEIGHT - 17;
        g.drawString(hintText, hintX, hintY);

        g.dispose();
        ImageUtils.setClipboardImage(image);
    }

    private static Color getRandomPastelColor() {
        int r = 150 + random.nextInt(106);
        int g = 150 + random.nextInt(106);
        int b = 150 + random.nextInt(106);
        return new Color(r, g, b);
    }

    private static Color brightenColor(Color color, float factor) {
        int r = Math.min(255, (int) (color.getRed() + 255 * factor));
        int g = Math.min(255, (int) (color.getGreen() + 255 * factor));
        int b = Math.min(255, (int) (color.getBlue() + 255 * factor));
        return new Color(r, g, b);
    }
}