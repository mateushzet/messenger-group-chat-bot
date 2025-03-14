package games.colors;

import java.awt.*;
import java.awt.geom.AffineTransform;
import java.awt.geom.Arc2D;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.util.*;
import java.util.List;
import java.util.Queue;

import com.madgag.gif.fmsware.AnimatedGifEncoder;
import utils.GradientGenerator;
import utils.ImageUtils;

public class ColorsGifGenerator {

    private static final int WIDTH = 300;
    private static final int HEIGHT = 300;
    private static final int RADIUS = 125;
    private static final Color[] COLORS = {
        new Color(90, 90, 90),
        new Color(197, 52, 81),
        new Color(72, 179, 221),
        new Color(252, 194, 120)
    };
    private static int[] colorOrder = {3, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2};


    public static void generateColorsGif(int winAmount, String userName, int updatedBalance, int currentBalance, int shift, int betAmount, Queue<Integer> history) {

        BufferedImage colorWheel = generateColorWheel(colorOrder);

        List<BufferedImage> frames = new ArrayList<>();

        BufferedImage background = createBackground(userName);

        int initialShift = (shift - 30 + colorOrder.length) % colorOrder.length;

        for (int i = 0; i < 20; i++) {
            BufferedImage frame = generateFrame(i, background, colorWheel, initialShift, shift, colorOrder, userName, currentBalance, betAmount, winAmount, history, false);
            frames.add(frame);
        }

        BufferedImage resultFrame = generateFrame(0, background, colorWheel, shift, shift, colorOrder, userName, updatedBalance, betAmount, winAmount, history, true);
        for (int i = 0; i < 40; i++) {
            frames.add(resultFrame);
        }

        byte[] gifBytes = createGif(frames);
        ImageUtils.setClipboardGif(gifBytes);
    }

    private static BufferedImage generateFrame(int i, BufferedImage background, BufferedImage colorWheel, int initialShift, int shift, int[] colorOrder, String userName, int currentBalance, int betAmount, int winAmount, Queue<Integer> history, boolean showResult) {
        BufferedImage frame = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = frame.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        g.drawImage(background, 0, 0, null);

        double progress = (double) i / 30;
        double easeOut = 1 - Math.pow(1 - progress, 5);
        int arrayShift = (int) (initialShift + easeOut * (shift - initialShift + colorOrder.length)) % colorOrder.length;

        double angle = 360.0 * arrayShift / colorOrder.length + 92;

        drawRotatedColorWheel(g, colorWheel, angle);

        Paint gradient = GradientGenerator.generateGradientFromUsername(userName, false, WIDTH, HEIGHT);
        g.setPaint(gradient);
        g.fillOval(WIDTH / 2 - RADIUS + 15, HEIGHT / 2 - RADIUS + 7, 220, 220);

        drawArrow(g);

        drawText(g, userName, currentBalance, betAmount, winAmount, showResult, shift);

        drawHistory(g, history);

        g.dispose();
        return frame;
    }

    private static BufferedImage createBackground(String userName) {
        BufferedImage background = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = background.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        Paint gradient = GradientGenerator.generateGradientFromUsername(userName, false, WIDTH, HEIGHT);
        g.setPaint(gradient);
        g.fillRect(0, 0, WIDTH, HEIGHT);

        ImageUtils.drawUserAvatar(g, userName, 490, 10, 100, 100);

        g.dispose();
        return background;
    }

    private static BufferedImage generateColorWheel(int[] colorOrder) {
        BufferedImage wheel = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = wheel.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int centerX = WIDTH / 2;
        int centerY = HEIGHT / 2;
        double anglePerSegment = 360.0 / colorOrder.length;
        double gap = 0.7;
        double startAngle = 0;

        for (int colorIndex : colorOrder) {
            g.setColor(COLORS[colorIndex]);
            Arc2D.Double arc = new Arc2D.Double(
                centerX - RADIUS, centerY - RADIUS,
                RADIUS * 2, RADIUS * 2,
                startAngle, anglePerSegment - gap,
                Arc2D.PIE
            );
            g.fill(arc);
            startAngle += anglePerSegment;
        }

        g.dispose();
        return wheel;
    }

    private static void drawRotatedColorWheel(Graphics2D g, BufferedImage colorWheel, double angle) {
        AffineTransform transform = new AffineTransform();
        transform.translate(WIDTH / 2, HEIGHT / 2);
        transform.rotate(Math.toRadians(angle));
        transform.translate(-WIDTH / 2, -HEIGHT / 2);
        g.drawImage(colorWheel, transform, null);
    }

    private static void drawArrow(Graphics2D g) {
        int arrowX = WIDTH / 2 + 2;
        int arrowY = HEIGHT - 60;
        int arrowWidth = 13;
        int arrowHeight = 25;

        int[] xPoints = {arrowX, arrowX - arrowWidth / 2, arrowX + arrowWidth / 2};
        int[] yPoints = {arrowY + arrowHeight, arrowY, arrowY};

        g.setColor(Color.WHITE);
        g.fillPolygon(xPoints, yPoints, 3);
    }

    private static void drawText(Graphics2D g, String userName, int currentBalance, int betAmount, int winAmount, boolean showResult, int shift) {
        g.setFont(new Font("Arial", Font.BOLD, 20));
        g.setColor(Color.WHITE);

        int centerX = WIDTH / 2;
        int centerY = HEIGHT / 2;
        FontMetrics metrics = g.getFontMetrics();

        if (showResult) {
            g.setColor(getColorFromIndex(colorOrder[shift]));
            String winText = winAmount > 0 ? "WIN " : "LOSE ";
            winText += winAmount;
            int textX = centerX - metrics.stringWidth(winText) / 2;
            g.drawString(winText, textX, centerY - 50);
            g.setColor(Color.WHITE);
        }

        String userText = userName;
        String balanceText = "Total: " + currentBalance;
        String betText = "Bet: " + betAmount;

        int textY = centerY - 20;
        int textX = centerX - metrics.stringWidth(userText) / 2;
        g.drawString(userText, textX, textY);

        textY += 30;
        textX = centerX - metrics.stringWidth(balanceText) / 2;
        g.drawString(balanceText, textX, textY);

        textY += 30;
        textX = centerX - metrics.stringWidth(betText) / 2;
        g.drawString(betText, textX, textY);
    }

    private static void drawHistory(Graphics2D g, Queue<Integer> history) {
        int margin = 20;
        int historyHeight = 50;
        int historyWidth = WIDTH - 2 * margin;
        int barWidth = historyWidth / 15;
        int spaceBetweenBars = 2;
    
        int x = 0;
        Integer[] reversedHistory = history.toArray(new Integer[0]);
    
        int startIndex = Math.max(0, reversedHistory.length - 16);
        for (int i = startIndex; i < reversedHistory.length; i++) {
            int colorIndex = reversedHistory[i];
            g.setColor(getColorFromIndex(colorIndex));
            g.fillRect(x, HEIGHT - historyHeight + 2 * margin, barWidth - spaceBetweenBars, historyHeight - 2 * margin - 5);
            x += (barWidth + spaceBetweenBars);
        }
    
        for (int i = 0; i < 16 - (reversedHistory.length - startIndex); i++) {
            g.setColor(Color.BLACK);
            g.fillRect(x, HEIGHT - historyHeight + 2 * margin, barWidth, historyHeight - 2 * margin - 5);
            x += (barWidth + spaceBetweenBars);
        }
    }

    private static Color getColorFromIndex(int colorIndex) {
        switch (colorIndex) {
            case 0: return new Color(90, 90, 90);
            case 1: return new Color(197, 52, 81);
            case 2: return new Color(72, 179, 221);
            case 3: return new Color(252, 194, 120);
            default: return Color.BLACK;
        }
    }

    private static byte[] createGif(List<BufferedImage> frames) {
        try (ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream()) {
            AnimatedGifEncoder encoder = new AnimatedGifEncoder();
            encoder.start(byteArrayOutputStream);
            encoder.setRepeat(0);
            encoder.setQuality(10);
            encoder.setDelay(100);

            for (BufferedImage frame : frames) {
                encoder.addFrame(frame);
            }

            encoder.finish();
            return byteArrayOutputStream.toByteArray();
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    public static int[] rotateArray(int[] array, int shift) {
        int length = array.length;
        int[] rotated = new int[length];
        for (int i = 0; i < length; i++) {
            rotated[(i + shift) % length] = array[i];
        }
        return rotated;
    }

}