package utils;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.nio.file.Paths;

public class CaseAvatarsImageProcessor {

    private static final String[] CONDITIONS = {
            "Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"
    };
    private static final float[] BRIGHTNESS_SCALE_LEVELS = {1.2f, 1.0f, 0.9f, 0.75f, 0.5f};
    private static final int IMAGE_SIZE = 100;
    
    private static File outputFolder;

    public static void main(String[] args) {
        File inputFolder = new File(buildPath("src","games","caseopening","skins"));
        outputFolder = new File(buildPath("src","resources","user_avatars"));

        if (!outputFolder.exists()) {
            outputFolder.mkdirs();
        }

        File[] files = inputFolder.listFiles((dir, name) -> name.toLowerCase().endsWith(".png"));
        if (files == null) return;

        for (File file : files) {
            for (int i = 0; i < CONDITIONS.length; i++) {
                processImage(file, CONDITIONS[i], BRIGHTNESS_SCALE_LEVELS[i], false);
                processImage(file, CONDITIONS[i], BRIGHTNESS_SCALE_LEVELS[i], true);
            }
        }
    }

    private static void processImage(File file, String condition, float brightnessFactor, boolean isST) {
        try {
            BufferedImage original = ImageIO.read(file);

            BufferedImage scaledImage = new BufferedImage(IMAGE_SIZE, IMAGE_SIZE, BufferedImage.TYPE_INT_ARGB);
            Graphics2D g2d = scaledImage.createGraphics();
            g2d.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
            g2d.drawImage(original, 0, 0, IMAGE_SIZE, IMAGE_SIZE, null);
            g2d.dispose();

            BufferedImage adjustedImage = applyBrightnessAdjustment(scaledImage, brightnessFactor);

            BufferedImage finalImage = new BufferedImage(IMAGE_SIZE, IMAGE_SIZE, BufferedImage.TYPE_INT_ARGB);
            g2d = finalImage.createGraphics();

            if (isST) {
                GradientPaint goldGradient = new GradientPaint(
                        0, 0, new Color(255, 215, 0),
                        0, IMAGE_SIZE, new Color(184, 134, 11)
                );
                g2d.setPaint(goldGradient);
                g2d.fillRect(0, 0, IMAGE_SIZE, IMAGE_SIZE);
            }

            g2d.drawImage(adjustedImage, 0, 0, null);
            g2d.dispose();

            // Zapis pliku
            String newFileName = file.getName().replace(".png", "") + " " + condition + (isST ? " ST" : "") + ".png";
            ImageIO.write(finalImage, "png", new File(outputFolder, newFileName));

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static BufferedImage applyBrightnessAdjustment(BufferedImage image, float brightnessFactor) {
        BufferedImage result = new BufferedImage(image.getWidth(), image.getHeight(), BufferedImage.TYPE_INT_ARGB);

        for (int y = 0; y < image.getHeight(); y++) {
            for (int x = 0; x < image.getWidth(); x++) {
                int argb = image.getRGB(x, y);
                Color color = new Color(argb, true);

                int r = adjustBrightness(color.getRed(), brightnessFactor);
                int g = adjustBrightness(color.getGreen(), brightnessFactor);
                int b = adjustBrightness(color.getBlue(), brightnessFactor);

                result.setRGB(x, y, new Color(r, g, b, color.getAlpha()).getRGB());
            }
        }
        return result;
    }

    private static int adjustBrightness(int colorValue, float factor) {
        return Math.min(255, Math.max(0, (int) (colorValue * factor)));
    }

    public static String buildPath(String... parts) {
        return Paths.get("", parts).toString();
    }

}
