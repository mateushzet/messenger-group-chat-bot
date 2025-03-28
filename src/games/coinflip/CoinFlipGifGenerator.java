package games.coinflip;

import com.madgag.gif.fmsware.AnimatedGifEncoder;

import repository.UserRepository;
import utils.GradientGenerator;
import utils.ImageUtils;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.geom.AffineTransform;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;

public class CoinFlipGifGenerator {
    private static final int WIDTH = 400;
    private static final int HEIGHT = 400;
    private static final int FRAME_COUNT = 100;
    private static final int COIN_SIZE = 200;
    private static final Color TEXT_COLOR = Color.WHITE;
    private static final Font TEXT_FONT = new Font("Arial", Font.BOLD, 18);

    public static void generateCoinFlipGif(String player1, String player2, String winner, String message) throws IOException {
        String avatar1Url = UserRepository.getUserAvatar(player1);
        String avatar2Url = UserRepository.getUserAvatar(player2);

        BufferedImage avatar1 = loadImageFromUrl(avatar1Url);
        BufferedImage avatar2 = loadImageFromUrl(avatar2Url);

        List<BufferedImage> frames = generateFrames(player1, avatar1, avatar2, winner.equals(player1) ? avatar1 : avatar2, message);

        byte[] gifBytes = createGif(frames);
            if (gifBytes != null) {
                ImageUtils.setClipboardGif(gifBytes);
            }
    }

    private static BufferedImage loadImageFromUrl(String imageUrl) throws IOException {
        URL url = new URL(imageUrl);
        return ImageIO.read(url);
    }

    private static List<BufferedImage> generateFrames(String player1, BufferedImage avatar1, BufferedImage avatar2, BufferedImage winnerAvatar, String message) {
        List<BufferedImage> frames = new ArrayList<>();

        for (int i = 0; i < FRAME_COUNT; i++) {
            BufferedImage frame = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_ARGB);
            Graphics2D g = frame.createGraphics();

            Paint gradient = GradientGenerator.generateGradientFromUsername(player1, false, WIDTH, HEIGHT);
            g.setPaint(gradient);
            g.fillRect(0, 0, WIDTH, HEIGHT);

            double progress = (double) i / FRAME_COUNT;
            double angle = 360 * 4 * progress;
            double scale = Math.abs(Math.sin(Math.toRadians(angle))) * 0.3 + 0.7;

            if (progress > 0.8) {
                angle = angle * (1 - (progress - 0.8) * 5);
                scale = 1.0;
            }

            double scaleY = Math.abs(Math.sin(Math.toRadians(angle)));

            int x = (WIDTH - COIN_SIZE) / 2;
            int y = (HEIGHT - COIN_SIZE) / 2;

            AffineTransform transform = new AffineTransform();
            transform.translate(x + COIN_SIZE / 2, y + COIN_SIZE / 2);
            transform.rotate(Math.toRadians(angle));
            transform.scale(1.0, scaleY);
            transform.translate(-COIN_SIZE / 2, -COIN_SIZE / 2);

        g.setTransform(transform);

            if (angle % 360 < 180) {
                drawAvatar(g, avatar1, 0, 0, COIN_SIZE, COIN_SIZE);
            } else {
                drawAvatar(g, avatar2, 0, 0, COIN_SIZE, COIN_SIZE);
            }

            g.dispose();
            frames.add(frame);
        }

        BufferedImage finalFrame = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = finalFrame.createGraphics();

        Paint gradient = GradientGenerator.generateGradientFromUsername(player1, true, WIDTH, HEIGHT);
        g.setPaint(gradient);
        g.fillRect(0, 0, WIDTH, HEIGHT);

        int x = (WIDTH - COIN_SIZE) / 2;
        int y = (HEIGHT - COIN_SIZE) / 2;
        drawAvatar(g, winnerAvatar, x, y, COIN_SIZE, COIN_SIZE);

        g.setColor(TEXT_COLOR);
        g.setFont(TEXT_FONT);
        FontMetrics metrics = g.getFontMetrics();
        int textX = (WIDTH - metrics.stringWidth(message)) / 2;
        int textY = HEIGHT - 50;
        g.drawString(message, textX, textY);

        g.dispose();

        for (int i = 0; i < 20; i++) {
            frames.add(finalFrame);
        }

        return frames;
    }

    private static void drawAvatar(Graphics2D g, BufferedImage avatar, int x, int y, int width, int height) {
        BufferedImage resizedAvatar = resizeImage(avatar, width, height);
    
        BufferedImage roundedAvatar = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g2d = roundedAvatar.createGraphics();
    
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
    
        int cornerRadius = 180;
        g2d.setColor(Color.WHITE);
        g2d.fillRoundRect(0, 0, width, height, cornerRadius, cornerRadius);
    
        g2d.setComposite(AlphaComposite.SrcIn);
        g2d.drawImage(resizedAvatar, 0, 0, null);
        g2d.dispose();
    
        g.drawImage(roundedAvatar, x, y, null);
    }

    private static BufferedImage resizeImage(BufferedImage originalImage, int targetWidth, int targetHeight) {
        BufferedImage resizedImage = new BufferedImage(targetWidth, targetHeight, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = resizedImage.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
        g.drawImage(originalImage, 0, 0, targetWidth, targetHeight, null);
        g.dispose();
        return resizedImage;
    }

    private static byte[] createGif(List<BufferedImage> frames) {
        try (ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream()) {
            AnimatedGifEncoder encoder = new AnimatedGifEncoder();
            encoder.start(byteArrayOutputStream);
            encoder.setDelay(50);
            encoder.setRepeat(0);
            encoder.setQuality(10);

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

}