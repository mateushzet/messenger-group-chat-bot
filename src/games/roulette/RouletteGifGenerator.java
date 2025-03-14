package games.roulette;

import java.util.Queue;
import java.util.Random;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

import com.madgag.gif.fmsware.AnimatedGifEncoder;

import utils.GradientGenerator;
import utils.ImageUtils;

import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import java.awt.*;
import java.awt.geom.Arc2D;
import java.awt.geom.Ellipse2D;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;

public class RouletteGifGenerator {

    private static final Color DARK_GRAY = new Color(25, 25, 25);
    private static final Color WIN_COLOR = new Color(50, 200, 50);
    private static final Color LOSE_COLOR = new Color(200, 50, 50);
    private static final Color TEXT_COLOR = Color.WHITE;
    private static final Color HISTORY_COLOR_NULL = new Color(100, 100, 100);
    private static final Color GREEN_COLOR = new Color(50, 200, 50);
    private static final Color BLACK_COLOR = new Color(60, 60, 60);
    private static final Color RED_COLOR = new Color(200, 50, 50);
    private static final Color HIGHLIGHT_COLOR = new Color(255, 215, 0);

    public static void generateGif(int result, int winnings, int balance, String username, int betAmount, Queue<Integer> rouletteHistory) {
        List<BufferedImage> frames = new ArrayList<>();
        List<Integer> delays = new ArrayList<>();

        int totalFrames = 100;
        int spinFrames = 80;

        int fullRotations = 3;

        BufferedImage background = createBackground(username);

        ExecutorService executor = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());
        List<Future<BufferedImage>> futures = new ArrayList<>();

        List<Boolean> isSpinFrame = new ArrayList<>();

        for (int i = 0; i < totalFrames; i++) {
            int finalI = i;
            isSpinFrame.add(finalI < spinFrames);
            futures.add(executor.submit(() -> generateFrame(finalI, background, result, winnings, balance, username, betAmount, rouletteHistory, spinFrames, fullRotations)));
        }

        for (int i = 0; i < futures.size(); i++) {
            try {
                frames.add(futures.get(i).get());
                delays.add(isSpinFrame.get(i) ? 40 : 100);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        executor.shutdown();

        Random random = new Random();
        int framesToCut = random.nextInt(16);
        if (framesToCut > 0) {
            frames = frames.subList(framesToCut, frames.size());
            delays = delays.subList(framesToCut, delays.size());
        }
    
        byte[] gifBytes = createGif(frames, delays);
        ImageUtils.setClipboardGif(gifBytes);
    }
    private static BufferedImage generateFrame(int i, BufferedImage background, int result, int winnings, int balance, String username, int betAmount, Queue<Integer> rouletteHistory, int spinFrames, int fullRotations) {
        BufferedImage frame = new BufferedImage(300, 300, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = frame.createGraphics();
        boolean lastFrames = false;
        g.drawImage(background, 0, 0, null);

        int simulatedResult;
        if (i < spinFrames) {
            double progress = (double) i / spinFrames;
            double easedProgress = easeOut(progress);
            simulatedResult = (int) (result + fullRotations * 13 * (1 - easedProgress));
        } else {
            simulatedResult = result;
            lastFrames = true;
        }
        drawRouletteWheel(g, 150, 158, 115, simulatedResult, i >= spinFrames);

        drawTextAndHistory(g, winnings, balance, username, betAmount, rouletteHistory, lastFrames);

        g.dispose();
        return frame;
    }

    private static BufferedImage createBackground(String username) {
        BufferedImage background = new BufferedImage(300, 300, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = background.createGraphics();

        Paint gradient = GradientGenerator.generateGradientFromUsername(username, false, 300, 300);
        g.setPaint(gradient);
        g.fillRect(0, 0, 300, 300);

        ImageUtils.drawUserAvatar(g, username, 230, 10, 60, 60);

        g.dispose();
        return background;
    }

    private static double easeOut(double progress) {
        return 1 - Math.pow(1 - progress/2, 5);
    }

    private static void drawRouletteWheel(Graphics2D g, int centerX, int centerY, int radius, int result, boolean showHighlight) {
        int segments = 13;
        double anglePerSegment = 360.0 / segments;

        g.setFont(new Font("Arial", Font.BOLD, 24));

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
            int textX = centerX + (int) (Math.cos(theta) * (radius - 25));
            int textY = centerY - (int) (Math.sin(theta) * (radius - 25));
            g.drawString(String.valueOf(i), textX - 6, textY + 4);
        }

        if (showHighlight) {
            g.setStroke(new BasicStroke(3));
            g.setColor(HIGHLIGHT_COLOR);
            double highlightStartAngle = result * anglePerSegment;
            Arc2D.Double highlight = new Arc2D.Double(
                centerX - radius, centerY - radius, 
                radius * 2, radius * 2, 
                highlightStartAngle, anglePerSegment, 
                Arc2D.PIE
            );
            g.draw(highlight);
        }

        g.setColor(DARK_GRAY);
        g.setStroke(new BasicStroke(8));
        g.drawOval(centerX - radius, centerY - radius, radius * 2, radius * 2);

        double theta = Math.toRadians(result * anglePerSegment + anglePerSegment / 2);
        int ballX = centerX + (int) (Math.cos(theta) * (radius - 55));
        int ballY = centerY - (int) (Math.sin(theta) * (radius - 55));
        g.setColor(Color.WHITE);
        g.fill(new Ellipse2D.Double(ballX - 12, ballY - 12, 25, 25));
    }

    private static void drawTextAndHistory(Graphics2D g, int winnings, int balance, String username, int betAmount, Queue<Integer> rouletteHistory, boolean lastFrames) {
        g.setColor(new Color(0, 0, 0, 150)); 
        g.fillRect(0, 0, 300, 40);

        g.setFont(new Font("Arial", Font.BOLD, 15));

        if(lastFrames){
            g.setColor(winnings <= 0 ? LOSE_COLOR : WIN_COLOR);
            String winLoseText = winnings <= 0 ? "LOSE " + winnings : "WIN " + winnings;
            g.drawString(winLoseText, 10, 20);
        }
        String betAmountText = "Bet: " + betAmount;
        int betTextWidth = g.getFontMetrics().stringWidth(betAmountText);
        g.setColor(TEXT_COLOR);
        g.drawString(betAmountText, 300 - betTextWidth - 10, 20);

        g.setFont(new Font("Arial", Font.BOLD, 15));
        String balanceText;
        if(lastFrames) balanceText = "Total: " + balance;
        else balanceText = "Total: " + (balance - winnings);
        g.setColor(TEXT_COLOR);
        g.drawString(balanceText, 10, 35);

        g.setFont(new Font("Arial", Font.PLAIN, 16));
        int usernameWidth = g.getFontMetrics().stringWidth(username);
        g.setColor(TEXT_COLOR);
        g.drawString(username, 300 - usernameWidth - 10, 35);

        drawHistory(g, rouletteHistory);
    }

    private static void drawHistory(Graphics2D g, Queue<Integer> rouletteHistory) {
        int maxHistorySize = 14;
        int squareSize = 21;
        int padding = 2;
        int historyStartX = 1;
        int historyStartY = 280;

        LinkedList<Integer> paddedHistory = new LinkedList<>(rouletteHistory);
        while (paddedHistory.size() < maxHistorySize) {
            paddedHistory.addFirst(null);
        }

        g.setColor(Color.WHITE);
        g.fillRect(historyStartX - 3, historyStartY - 1, maxHistorySize * (squareSize + padding), squareSize + 5);

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

            if (number != null) {
                g.setColor(Color.WHITE);
                String text = String.valueOf(number);
                int textWidth = g.getFontMetrics().stringWidth(text);
                int textX = x + (squareSize - textWidth) / 2;
                int textY = historyStartY + (squareSize + g.getFontMetrics().getAscent()) / 2 - 3;
                g.drawString(text, textX, textY);
            }

            index++;
        }
    }

    private static byte[] createGif(List<BufferedImage> frames, List<Integer> delays) {
        try (ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream()) {
            AnimatedGifEncoder encoder = new AnimatedGifEncoder();
            encoder.start(byteArrayOutputStream);
            encoder.setRepeat(0);
            encoder.setQuality(5);

            for (int i = 0; i < frames.size(); i++) {
                encoder.setDelay(delays.get(i));
                encoder.addFrame(frames.get(i));
            }

            encoder.finish();
            return byteArrayOutputStream.toByteArray();
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }
}