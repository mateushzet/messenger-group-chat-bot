package utils;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;

public class CaseAvatarsImageProcessor {

    static private File outputFolder;

    private static final String[] CONDITIONS = {
            "Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"
    };
    private static final float[] BRIGHTNESS_SCALE_LEVELS = {1.2f, 1.0f, 0.9f, 0.75f, 0.5f};

    public static void main(String[] args) {
        File inputFolder = new File("src\\games\\caseopening\\skins");

        outputFolder = new File("src\\resources\\user_avatars");
        if (!outputFolder.exists()) {
            outputFolder.mkdirs();
        }

        if (!outputFolder.exists()) outputFolder.mkdirs();

        File[] files = inputFolder.listFiles((dir, name) -> name.toLowerCase().endsWith(".png"));
        if (files == null) {
            return;
        }

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
            BufferedImage processed = new BufferedImage(100, 100, BufferedImage.TYPE_INT_ARGB);
            Graphics2D g2d = processed.createGraphics();
    
            if (isST) {
                GradientPaint goldGradient = new GradientPaint(
                        0, 0, new Color(255, 215, 0),
                        0, 100, new Color(184, 134, 11)
                );
                g2d.setPaint(goldGradient);
            } else {
                g2d.setColor(Color.BLACK);
            }
            g2d.fillRect(0, 0, 100, 100);
    
            BufferedImage adjustedImage = applyBrightnessAdjustment(original, brightnessFactor);
    
            Image scaledImage = adjustedImage.getScaledInstance(100, 100, Image.SCALE_SMOOTH);
            g2d.drawImage(scaledImage, 0, 0, null);
            g2d.dispose();
    
            String newFileName = file.getName().replace(".png", "") + " " + condition + (isST ? " ST" : "") + ".png";

            
            File outputFile = new File(outputFolder, newFileName);
            ImageIO.write(processed, "png", outputFile);

            ImageIO.write(processed, "png", outputFile);
    
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
                
                Color newColor = new Color(r, g, b, color.getAlpha());
                result.setRGB(x, y, newColor.getRGB());
            }
        }
        return result;
    }
    
    private static int adjustBrightness(int colorValue, float factor) {
        int newValue = (int) (colorValue * factor);
        return Math.min(255, Math.max(0, newValue));
    }
}
