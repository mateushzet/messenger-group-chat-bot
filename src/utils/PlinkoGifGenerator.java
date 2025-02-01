package utils;

import com.madgag.gif.fmsware.AnimatedGifEncoder;

import java.awt.*;
import java.awt.datatransfer.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class PlinkoGifGenerator {
    private static final int WIDTH = 600;
    private static final int HEIGHT = 840;
    private static final int PEG_RADIUS = 5;
    private static final int BALL_RADIUS = 8;
    private static final int ROWS = 14;
    private static final int COLUMNS = 15;
    private static final int SLOT_WIDTH = 40;
    private static final Color BALL_COLOR = new Color(255, 200, 50);
    private static final Color PEG_COLOR = Color.WHITE;
    private static final double[] MULTIPLIERS = {33., 11., 4., 2., 1.1, 0.6, 0.3, 0.6, 1.1, 2.0, 4.0, 11.0, 33.0};
    private static String username = "";
    private static int betAmount = 0;
    private static int totalBalance = 0;


    public static Double playAndGenerateGif(String usernamePassed, int betAmountPassed, int totalBalancePassed) {
        int ballX = WIDTH / 2;
        int ballY = 50;
        int steps = ROWS;
        Random rand = new Random();
        List<BufferedImage> frames = new ArrayList<>();

        username = usernamePassed;
        betAmount = betAmountPassed;
        totalBalance = totalBalancePassed;

        for (int i = 0; i < steps; i++) {
            ballY += 50;
            ballX += rand.nextBoolean() ? SLOT_WIDTH / 2 : -SLOT_WIDTH / 2;
            if(i == steps - 1) {
                frames.add(generatePlinkoImage(ballX, ballY, i, ""));
                frames.add(generatePlinkoImage(ballX, ballY, i, ""));
            }
            frames.add(generatePlinkoImage(ballX, ballY, i, ""));
        }

        int finalSlot = Math.min(Math.max((ballX - (WIDTH / 2 - (COLUMNS * SLOT_WIDTH / 2))) / SLOT_WIDTH, 0), COLUMNS - 1);

        double finalMultiplier = MULTIPLIERS[finalSlot - 1];

        byte[] gifBytes = createGif(frames, finalMultiplier);

        copyToClipboard(gifBytes);

        return finalMultiplier;
    }

    private static BufferedImage generatePlinkoImage(int ballX, int ballY, int currentStep, String finalMultiplier) {
        BufferedImage image = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        g.setColor(new Color(20, 20, 40));
        g.fillRect(0, 0, WIDTH, HEIGHT);

        g.setColor(PEG_COLOR);
        for (int row = 0; row < ROWS; row++) {
            for (int col = 0; col <= row; col++) {
                int x = WIDTH / 2 - (row * SLOT_WIDTH / 2) + col * SLOT_WIDTH;
                int y = 100 + row * 50;
                g.fillOval(x - PEG_RADIUS, y - PEG_RADIUS, PEG_RADIUS * 2, PEG_RADIUS * 2);
            }
        }

        g.setColor(BALL_COLOR);
        g.fillOval(ballX - BALL_RADIUS, ballY - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2);

        g.setColor(Color.WHITE);
        for (int i = 0; i < COLUMNS - 2; i++) {
            int x = WIDTH / 2 - (ROWS * SLOT_WIDTH / 2) + i * SLOT_WIDTH + 25;
            int y = HEIGHT - 50;

            Color backgroundColor = getMultiplierBackgroundColor(i);
            g.setColor(backgroundColor);
            g.fillRect(x - 3 , y - 20, 40, 30);

            g.setColor(Color.BLACK);
            g.drawString(formatMultiplier(MULTIPLIERS[i]) + "x", x + SLOT_WIDTH / 4, y);
        }

        if (currentStep == ROWS - 1) {
            int finalSlot = Math.min(Math.max((ballX - (WIDTH / 2 - (COLUMNS * SLOT_WIDTH / 2))) / SLOT_WIDTH, 0), COLUMNS - 1);
            double finalMultiplierValue = MULTIPLIERS[finalSlot - 1];

            g.setFont(new Font("Arial", Font.BOLD, 30));
            g.setColor(Color.YELLOW);
            g.drawString(finalMultiplierValue + "x", WIDTH / 2 - 50, HEIGHT / 2);
        }

        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 25));
        g.drawString("Username: " + username, 10, 50);
        g.drawString("Balance: " + totalBalance, 10, 90);
        g.drawString("Bet: " + betAmount, 10, 130);


        g.dispose();
        return image;
    }

    private static byte[] createGif(List<BufferedImage> frames, double finalMultiplier) {
        try {
            ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
            AnimatedGifEncoder encoder = new AnimatedGifEncoder();
            encoder.start(byteArrayOutputStream);
            encoder.setDelay(300);
            encoder.setRepeat(0);
            
            for (BufferedImage frame : frames) {
                encoder.addFrame(frame);
            }
            
            BufferedImage finalFrame = generatePlinkoImage(frames.get(frames.size() - 1).getWidth() / 2, 
                                                           frames.get(frames.size() - 1).getHeight() - 50, 
                                                           ROWS - 1, String.valueOf(finalMultiplier));
            encoder.addFrame(finalFrame);
            encoder.finish();

            return byteArrayOutputStream.toByteArray();

        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    private static void copyToClipboard(byte[] gifBytes) {
        try {
            Transferable transferable = new Transferable() {
                @Override
                public DataFlavor[] getTransferDataFlavors() {
                    return new DataFlavor[]{DataFlavor.javaFileListFlavor};
                }

                @Override
                public boolean isDataFlavorSupported(DataFlavor flavor) {
                    return DataFlavor.javaFileListFlavor.equals(flavor);
                }

                @Override
                public Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException {
                    try {
                        File tempFile = File.createTempFile("plinko", ".gif");
                        try (FileOutputStream fos = new FileOutputStream(tempFile)) {
                            fos.write(gifBytes);
                        }
                        return java.util.Collections.singletonList(tempFile);
                    } catch (Exception e) {
                        e.printStackTrace();
                        return null;
                    }
                }
            };

            Clipboard clipboard = Toolkit.getDefaultToolkit().getSystemClipboard();
            clipboard.setContents(transferable, null);

            System.out.println("GIF skopiowano do schowka.");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static Color getMultiplierBackgroundColor(int index) {
        int distanceFromCenter = Math.abs(index - ((COLUMNS - 2) / 2));
        int colorIntensity = Math.min(255, 255 - (distanceFromCenter * 30));

        return new Color(colorIntensity, colorIntensity, 255);
    }

    private static String formatMultiplier(double multiplier) {
        if (multiplier == (int) multiplier) {
            return String.format("%d", (int) multiplier);
        } else {
            return String.format("%.1f", multiplier);
        }
    }

}
