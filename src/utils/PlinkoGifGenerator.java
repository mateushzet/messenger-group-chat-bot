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
    private static final int WIDTH = 800;
    private static final int HEIGHT = 940;
    private static final int PEG_RADIUS = 5;
    private static final int BALL_RADIUS = 8;
    private static final int ROWS = 16;
    private static final int COLUMNS = 17;
    private static final int SLOT_WIDTH = 40;
    private static final Color BALL_COLOR = new Color(255, 200, 50);
    private static Color PEG_COLOR = Color.WHITE;
    private static double[] MULTIPLIERS;
    private static String username = "";
    private static int betAmount = 0;
    private static int totalBalance = 0;
    private static Paint gradient;

    public static Double playAndGenerateGif(String usernamePassed, int betAmountPassed, int totalBalancePassed, String risk) {
        int ballX = WIDTH / 2;
        int ballY = 50;
        int steps = ROWS;
        gradient = GradientGenerator.generateGradientFromUsername(usernamePassed, false, 300, 120);

        switch (risk) {
            case "low", "l":
                MULTIPLIERS = new double[]{20., 4.0, 1.6, 1.3, 1.2, 1.1, 1.0, 0.5, 1.0, 1.1, 1.2, 1.3, 1.6, 4.0, 20.};
                break;
            
            case "medium", "m":
                MULTIPLIERS = new double[]{60., 12., 5.6, 3.2, 1.6, 1.1, 0.7, 0.2, 0.7, 1.1, 1.6, 3.2, 5.6, 12., 60.};
                break;

            case "high", "h":
                MULTIPLIERS = new double[]{420.0, 50.0, 14.0, 5.3, 2.1, 0.5, 0.2, 0.0, 0.2, 0.5, 2.1, 5.3, 14.0, 50.0, 420};
                break;

            default:
                MULTIPLIERS = new double[]{20., 4.0, 1.6, 1.3, 1.2, 1.1, 1.0, 0.5, 1.0, 1.1, 1.2, 1.3, 1.6, 4.0, 20.};
                break;
        }

        Random rand = new Random();
        List<BufferedImage> frames = new ArrayList<>();
        
        username = usernamePassed;
        betAmount = betAmountPassed;
        totalBalance = totalBalancePassed;

        for (int i = 0; i < steps; i++) {
            ballY += 50;
            ballX += rand.nextBoolean() ? SLOT_WIDTH / 2 : -SLOT_WIDTH / 2;
            if(i == steps - 1) {
                BufferedImage frame = generatePlinkoImage(ballX, ballY, true, risk);
                frames.add(frame);
                frames.add(frame);
                frames.add(frame);
                frames.add(frame);
                frames.add(frame);
                frames.add(frame);
                frames.add(frame);
            } else frames.add(generatePlinkoImage(ballX, ballY, false, risk));
        }

        int finalSlot = Math.min(Math.max((ballX - (WIDTH / 2 - (COLUMNS * SLOT_WIDTH / 2))) / SLOT_WIDTH, 0), COLUMNS - 1);

        double finalMultiplier = MULTIPLIERS[finalSlot - 1];

        byte[] gifBytes = createGif(frames, finalMultiplier, risk);

        copyToClipboard(gifBytes);

        return finalMultiplier;
    }

    private static BufferedImage generatePlinkoImage(int ballX, int ballY, boolean lastStep, String risk) {
        BufferedImage image = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        g.setColor(new Color(20, 20, 40));
        g.fillRect(0, 0, WIDTH, HEIGHT);

        g.setStroke(new BasicStroke(7));
        g.setPaint(gradient);
        g.drawRect(5, 5, WIDTH - 10, HEIGHT - 10);

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

            Color backgroundColor = getMultiplierBackgroundColor(i, risk);
            g.setColor(backgroundColor);
            g.fillRect(x - 3 , y - 20, 40, 30);

            String multiplierText = formatMultiplier(MULTIPLIERS[i]) + "x";

            g.setColor(Color.BLACK);
            g.setFont(new Font("Arial", Font.BOLD, 14));
            g.drawString(multiplierText, x+5, y);
        }

        if (lastStep) {
            int finalSlot = Math.min(Math.max((ballX - (WIDTH / 2 - (COLUMNS * SLOT_WIDTH / 2))) / SLOT_WIDTH, 0), COLUMNS - 1);
            double finalMultiplierValue = MULTIPLIERS[finalSlot - 1];

            g.setFont(new Font("Arial", Font.BOLD, 90));
            g.setColor(Color.YELLOW);

            String multiplierText = finalMultiplierValue + "x";
            FontMetrics metrics = g.getFontMetrics();
            int textWidth = metrics.stringWidth(multiplierText);
            int textX = (WIDTH - textWidth) / 2;
            int textY = HEIGHT / 3 + 70;
            g.drawString(multiplierText, textX, textY);

            String wonText = "WON: " + ((int) (finalMultiplierValue * betAmount));
            textWidth = metrics.stringWidth(wonText);
            textX = (WIDTH - textWidth) / 2;
            int wonTextY = HEIGHT / 3 + 170;
            g.drawString(wonText, textX, wonTextY);
        }

        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 36));
        g.drawString(username, 25, 55);
        g.drawString("Balance: " + totalBalance, 25, 105);
        g.drawString("Bet: " + betAmount, 25, 155);
 
        g.dispose();
        return image;
    }

    private static byte[] createGif(List<BufferedImage> frames, double finalMultiplier, String risk) {
        try {
            ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
            AnimatedGifEncoder encoder = new AnimatedGifEncoder();
            encoder.start(byteArrayOutputStream);
            encoder.setDelay(180);
            encoder.setRepeat(0);
            
            for (BufferedImage frame : frames) {
                encoder.addFrame(frame);
            }
            
            BufferedImage finalFrame = generatePlinkoImage(frames.get(frames.size() - 1).getWidth() / 2, 
                                                           frames.get(frames.size() - 1).getHeight() - 50, 
                                                           false, risk);
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

    private static Color getMultiplierBackgroundColor(int index, String risk) {
        int centerIndex = (COLUMNS - 2) / 2;
        int distanceFromCenter = Math.abs(index - centerIndex);
        float ratio = distanceFromCenter / (float) centerIndex;
        
        Color startColor = Color.WHITE;
        Color endColor;
    
        switch (risk) {
            case "low", "l":
                endColor = new Color(0, 200, 0);
                break;
            case "medium", "m":
                endColor = new Color(200, 200, 0);
                break;
            case "high", "h":
                endColor = new Color(200, 0, 0);
                break;
            default:
                endColor = Color.GRAY;
                break;
        }
    
        int r = (int) (startColor.getRed() * (1 - ratio) + endColor.getRed() * ratio);
        int g = (int) (startColor.getGreen() * (1 - ratio) + endColor.getGreen() * ratio);
        int b = (int) (startColor.getBlue() * (1 - ratio) + endColor.getBlue() * ratio);
    
        return new Color(r, g, b);
    }    

    private static String formatMultiplier(double multiplier) {
        if(multiplier >=10){
            if (multiplier == (int) multiplier) {
                return String.format("%d", (int) multiplier);
            } else {
                return String.format("%.1f", multiplier);
            }
        } else return String.valueOf(multiplier);
    }

}
