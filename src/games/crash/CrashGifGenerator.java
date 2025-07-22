package games.crash;

import com.madgag.gif.fmsware.AnimatedGifEncoder;

import utils.ImageUtils;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.util.ArrayList;
import java.util.List;

public class CrashGifGenerator {
    private static final int WIDTH = 800;
    private static final int HEIGHT = 600;
    private static final Color BACKGROUND_COLOR = new Color(30, 30, 30);
    private static final Color LINE_COLOR = Color.GREEN;
    private static final Color TEXT_COLOR = Color.WHITE;
    private static final int MAX_FRAMES = 100;
    private static final double MAX_MULTIPLIER = 100.0;
    private static final int END_FRAME_DURATION = 20;
    
    public static double playAndGenerateGif(String username, int betAmount, int totalBalance, double playerCashout, double crashMultiplier) {
        List<BufferedImage> frames = new ArrayList<>();

        double[] multipliers = new double[MAX_FRAMES];
        for (int i = 0; i < MAX_FRAMES; i++) {
            double t = i / (double) (MAX_FRAMES - 1);
            multipliers[i] = Math.pow(MAX_MULTIPLIER, t);
            if (multipliers[i] >= playerCashout || multipliers[i] >= crashMultiplier) {
                crashMultiplier = Math.min(multipliers[i], crashMultiplier);
                break;
            }
        }

        double displayMultiplier = 0;

        for (int i = 0; ; i++) {
            displayMultiplier = Math.min(multipliers[i], Math.min(crashMultiplier, playerCashout));
            frames.add(generateCrashFrame(i, displayMultiplier, username, betAmount, totalBalance, multipliers));
            if (multipliers[i] >= crashMultiplier || multipliers[i] >= playerCashout) {
                boolean isCashout = displayMultiplier >= playerCashout;
                boolean isCrash = displayMultiplier >= crashMultiplier && !isCashout;
                for (int j = 0; j < END_FRAME_DURATION; j++) {
                    frames.add(generateCrashFrame(i, displayMultiplier, username, betAmount, totalBalance, multipliers, isCrash, isCashout));
                }
                break;
            }
            
        }

        byte[] gifBytes = createGif(frames);
        ImageUtils.setClipboardGif(gifBytes);

        return displayMultiplier;
    }

    private static BufferedImage generateCrashFrame(int frameIndex, double multiplier, String username, int betAmount, int totalBalance, double[] multipliers) {
        return generateCrashFrame(frameIndex, multiplier, username, betAmount, totalBalance, multipliers, false, false);
    }

    private static BufferedImage generateCrashFrame(int frameIndex, double multiplier, String username, int betAmount, int totalBalance, double[] multipliers, boolean isCrashPoint, boolean isCashout) {
        BufferedImage image = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        g.setColor(BACKGROUND_COLOR);
        g.fillRect(0, 0, WIDTH, HEIGHT);

        g.setColor(LINE_COLOR);
        g.setStroke(new BasicStroke(3));

        int prevX = 0;
        int prevY = HEIGHT;

        for (int i = 1; i <= frameIndex; i++) {
            int x = (int) ((i / (float) MAX_FRAMES) * WIDTH);
            int y = HEIGHT - (int) ((Math.log(multipliers[i]) / Math.log(MAX_MULTIPLIER)) * HEIGHT * 0.9);
            g.drawLine(prevX, prevY, x, y);
            prevX = x;
            prevY = y;
        }

        g.setColor(TEXT_COLOR);
        g.setFont(new Font("Arial", Font.BOLD, 30));
        g.drawString("Multiplier: " + String.format("%.2f x", multiplier), 25, 50);
        g.drawString("Username: " + username, 25, 100);
        if (isCashout) g.setColor(Color.GREEN);
        else g.setColor(Color.RED);
        if(isCrashPoint&&!isCashout) g.drawString("Balance: " + (totalBalance - betAmount), 25, 150);
        else g.drawString("Balance: " + (totalBalance + (int)(betAmount*multiplier) - betAmount), 25, 150);
        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 30));
        g.drawString("Bet: " + betAmount, 25, 200);

        if (isCashout) {
            g.setFont(new Font("Arial", Font.BOLD, 50));
            g.setColor(Color.GREEN);
            g.drawString("CASHOUT!", WIDTH / 2 - 100, HEIGHT / 2);
        } else if (isCrashPoint) {
            g.setFont(new Font("Arial", Font.BOLD, 50));
            g.setColor(Color.RED);
            g.drawString("CRASH!", WIDTH / 2 - 100, HEIGHT / 2);
        }

        g.dispose();
        return image;
    }

    private static byte[] createGif(List<BufferedImage> frames) {
        try {
            ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
            AnimatedGifEncoder encoder = new AnimatedGifEncoder();
            encoder.start(byteArrayOutputStream);
            encoder.setDelay(100);
            encoder.setRepeat(0);
            
            for (BufferedImage frame : frames) {
                encoder.addFrame(frame);
            }
            encoder.finish();
            return byteArrayOutputStream.toByteArray();
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

}
