package utils;

import com.madgag.gif.fmsware.AnimatedGifEncoder;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class RewardGifGenerator {

    private static final int WIDTH = 210;
    private static final int HEIGHT = 100;

    private static final int BOX_X = 10;
    private static final int BOX_Y = 0;
    private static final int BOX_WIDTH = WIDTH - 20;
    private static final int BOX_HEIGHT = 60;

    private static final int BAR_HEIGHT = 15;
    private static final int BAR_Y = BOX_Y + 25;
    private static final int SEGMENTS = 9;

    private static final int FRAME_DELAY = 50;
    private static final int FINAL_FRAME_DURATION = 3000;
    private static final int MAX_FRAMES = 100;

    private static final Font HEADER_FONT = new Font("SansSerif", Font.BOLD, 11);
    private static final Font REWARD_FONT = new Font("SansSerif", Font.BOLD, 14);
    private static final Font BALANCE_FONT = new Font("SansSerif", Font.PLAIN, 10);

    private static final FontMetrics HEADER_METRICS;
    private static final FontMetrics REWARD_METRICS;
    private static final FontMetrics BALANCE_METRICS;

    private static final Map<String, Paint> GRADIENT_CACHE = new HashMap<>();
    private static final float[] PULSES = new float[MAX_FRAMES];

    static {
        BufferedImage dummy = new BufferedImage(1, 1, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = dummy.createGraphics();
        g.setFont(HEADER_FONT);
        HEADER_METRICS = g.getFontMetrics();
        g.setFont(REWARD_FONT);
        REWARD_METRICS = g.getFontMetrics();
        g.setFont(BALANCE_FONT);
        BALANCE_METRICS = g.getFontMetrics();
        g.dispose();

        for (int i = 0; i < MAX_FRAMES; i++) {
            double sinValue = Math.sin(2 * Math.PI * i / MAX_FRAMES);
            PULSES[i] = 0.7f + 0.3f * (float) ((sinValue + 1) / 2);
        }
    }

    public static void generateGif(int reward, String userName, int newBalance, int fakeRewardMax) {
        List<BufferedImage> frames = new ArrayList<>();
        List<Integer> delays = new ArrayList<>();

        Paint gradient = GRADIENT_CACHE.computeIfAbsent(userName,
                name -> GradientGenerator.generateGradientFromUsername(name, false, WIDTH, HEIGHT));

        String header = userName + " correct answer!";

        double targetProgress = ((double) reward) / (fakeRewardMax);
        targetProgress = Math.min(Math.max(targetProgress, 0), 1);

        double progressStep = 0.02;
        int animatedFrames = (int) Math.ceil(targetProgress / progressStep);
        animatedFrames = Math.min(animatedFrames, MAX_FRAMES - 1);

        for (int i = 0; i < animatedFrames; i++) {
            double progress = Math.min(i * progressStep, targetProgress);
            BufferedImage frame = createFrame(userName, reward, newBalance, false, gradient, header, progress, i);
            frames.add(frame);
            delays.add(FRAME_DELAY);
        }

        BufferedImage lastFrame = createFrame(userName, reward, newBalance, true, gradient, header, targetProgress, animatedFrames);
        
        int finalFramesCount = FINAL_FRAME_DURATION / FRAME_DELAY;
        for (int i = 0; i < finalFramesCount; i++) {
            frames.add(lastFrame);
            delays.add(FRAME_DELAY);
        }

        byte[] gifBytes = createGif(frames, delays);
        if (gifBytes != null) {
            ImageUtils.setClipboardGif(gifBytes);
        }
    }

    private static BufferedImage createFrame(String userName, int reward, int balance, boolean highlight,
                                             Paint gradient, String header,
                                             double progress, int pulseIndex) {
        BufferedImage frame = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = frame.createGraphics();

        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

        g.setPaint(gradient);
        g.fillRect(0, 0, WIDTH, HEIGHT);

        g.setColor(new Color(0, 0, 0, 140));
        g.fillRect(0, 20, WIDTH, BOX_HEIGHT - 20);

        drawHeader(g, header);
        drawProgressBar(g, progress, highlight, pulseIndex);
        drawRangeLabels(g);

        if (highlight) {
            drawRewardText(g, reward, balance);
        }

        g.dispose();
        return frame;
    }

    private static void drawHeader(Graphics2D g, String header) {
        g.setFont(HEADER_FONT);
        g.setColor(new Color(0, 0, 0, 100));
        drawCenteredString(g, header, HEADER_METRICS, BOX_Y + 17);

        g.setColor(Color.WHITE);
        drawCenteredString(g, header, HEADER_METRICS, BOX_Y + 15);
    }

    private static void drawProgressBar(Graphics2D g, double progress, boolean highlight, int pulseIndex) {
        int fillWidth = (int) (BOX_WIDTH * progress);

        g.setColor(new Color(50, 50, 50, 160));
        g.fillRoundRect(BOX_X, BAR_Y, BOX_WIDTH, BAR_HEIGHT, 10, 10);

        g.setColor(new Color(255, 255, 255, 40));
        for (int i = 1; i <= SEGMENTS; i++) {
            int x = BOX_X + (BOX_WIDTH * i / (SEGMENTS + 1));
            g.drawLine(x, BAR_Y + 2, x, BAR_Y + BAR_HEIGHT - 2);
        }

        Color gold = new Color(255, 215, 0);
        float pulse = highlight ? PULSES[pulseIndex % MAX_FRAMES] : 1.0f;
        Color fillColor = new Color(
                Math.min(255, (int) (gold.getRed() * pulse)),
                Math.min(255, (int) (gold.getGreen() * pulse)),
                Math.min(255, (int) (gold.getBlue() * pulse)),
                220
        );

        g.setColor(fillColor);
        g.fillRoundRect(BOX_X, BAR_Y, fillWidth, BAR_HEIGHT, 10, 10);

            int shineWidth = 30;
            int shineX = Math.max(fillWidth - 20, 10);
            GradientPaint shine = new GradientPaint(
                    shineX, BAR_Y, new Color(255, 223, 50, 130),
                    shineX + shineWidth, BAR_Y + BAR_HEIGHT, new Color(255, 223, 50, 0)
            );
            g.setPaint(shine);
            g.fillRoundRect(shineX, BAR_Y, Integer.min(shineWidth,fillWidth), BAR_HEIGHT, 10, 10);
    }

    private static void drawRangeLabels(Graphics2D g) {
        g.setFont(BALANCE_FONT);
        g.setColor(new Color(255, 255, 255, 180));
        FontMetrics fm = BALANCE_METRICS;

        String minStr = "0";
        String midStr = "50";
        String maxStr = "100";

        g.drawString(minStr, BOX_X + fm.stringWidth(minStr) / 2, BAR_Y + BAR_HEIGHT + 15);
        g.drawString(midStr, BOX_X + BOX_WIDTH / 2 - fm.stringWidth(midStr) / 2, BAR_Y + BAR_HEIGHT + 15);
        g.drawString(maxStr, BOX_X + BOX_WIDTH - fm.stringWidth(maxStr), BAR_Y + BAR_HEIGHT + 15);
    }

    private static void drawRewardText(Graphics2D g, int reward, int balance) {
        g.setFont(REWARD_FONT);
        g.setColor(new Color(255, 215, 0));
        drawCenteredString(g, "Reward: " + reward + " coins", REWARD_METRICS, BAR_Y + BAR_HEIGHT + 35);

        g.setFont(BALANCE_FONT);
        g.setColor(Color.WHITE);
        drawCenteredString(g, "New balance: " + balance, BALANCE_METRICS, BAR_Y + BAR_HEIGHT + 50);
    }

    private static void drawCenteredString(Graphics2D g, String text, FontMetrics metrics, int y) {
        int textWidth = metrics.stringWidth(text);
        int x = (WIDTH - textWidth) / 2;
        g.drawString(text, x, y);
    }

    private static byte[] createGif(List<BufferedImage> frames, List<Integer> delays) {
        try (ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            AnimatedGifEncoder encoder = new AnimatedGifEncoder();
            encoder.start(output);
            encoder.setRepeat(0);
            encoder.setQuality(10);
            for (int i = 0; i < frames.size(); i++) {
                encoder.setDelay(delays.get(i));
                encoder.addFrame(frames.get(i));
            }
            encoder.finish();
            return output.toByteArray();
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

}