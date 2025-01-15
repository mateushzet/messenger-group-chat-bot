package utils;

import java.awt.Color;
import java.awt.Font;
import java.awt.GradientPaint;
import java.awt.Graphics2D;
import java.awt.LinearGradientPaint;
import java.awt.Paint;
import java.awt.Rectangle;
import java.awt.TexturePaint;
import java.awt.Toolkit;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.geom.Point2D;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.net.URL;
import java.util.List;
import java.util.Map;

import javax.imageio.ImageIO;

import repository.UserSkinRepository;
import service.MessageService;

    public class GradientGenerator {
        
        public static final List<Map<String, Object>> skinIds = List.of(
            Map.of("id", "red_flame", "name", "Red Flame", "price", 10),
            Map.of("id", "green_forest", "name", "Green Forest", "price", 10),
            Map.of("id", "blue_ocean", "name", "Blue Ocean", "price", 10),
            Map.of("id", "sunny_yellow", "name", "Sunny Yellow", "price", 10),
            Map.of("id", "pink_blossom", "name", "Pink Blossom", "price", 10),

            Map.of("id", "purple_dream", "name", "Purple Dream", "price", 15),
            Map.of("id", "chocolate_swirl", "name", "Chocolate Swirl", "price", 15),
            Map.of("id", "golden_aura", "name", "Golden Aura", "price", 15),
            Map.of("id", "icy_blue", "name", "Icy Blue", "price", 15),

            Map.of("id", "crimson_sunset", "name", "Crimson Sunset", "price", 30),
            Map.of("id", "lavender_haze", "name", "Lavender Haze", "price", 30),
            Map.of("id", "fire", "name", "Fire Gradient", "price", 30),
            Map.of("id", "ocean_waves", "name", "Ocean Waves", "price", 30),
            Map.of("id", "retro_sunset", "name", "Retro Sunset", "price", 30),

            Map.of("id", "sunrise", "name", "Sunrise", "price", 50),
            Map.of("id", "neon_glow", "name", "Neon Glow", "price", 50),
            Map.of("id", "galaxy_dream", "name", "Galaxy Dream", "price", 50),
            Map.of("id", "electric_lime", "name", "Electric Lime", "price", 50),
            Map.of("id", "mystic_forest", "name", "Mystic Forest", "price", 50),
            Map.of("id", "cosmic_pink", "name", "Cosmic Pink", "price", 50),
            Map.of("id", "lush_meadow", "name", "Lush Meadow", "price", 50),

            Map.of("id", "rainbow", "name", "Rainbow", "price", 100),
            Map.of("id", "aurora_borealis", "name", "Aurora Borealis", "price", 100),

            Map.of("id", "neon_pulse", "name", "Neon Pulse", "price", 150),
            Map.of("id", "neon_rainbow", "name", "Neon Rainbow", "price", 150)
        );

    public static Paint generateGradientFromUsername(String username, boolean isDark, int width, int height) {

        String skinId = UserSkinRepository.getActiveSkinForUser(username);
        
        if (skinId != null && skinId != "default") {
            return getGradientForSkin(skinId, width, height, 0, 0);
        }
        
        int hash = (username).hashCode();
        int colorComponent1 = (hash >>> 16) & 0xFF;
        int colorComponent2 = (hash >>> 8) & 0xFF;
        int colorComponent3 = (hash) & 0xFF;
    
        int red1 = (colorComponent1 + 128) % 256;
        int green1 = (colorComponent2 + 128) % 256;
        int blue1 = (colorComponent3 + 128) % 256;
    
        int red2 = (colorComponent1 + 180) % 256;
        int green2 = (colorComponent2 + 180) % 256;
        int blue2 = (colorComponent3 + 180) % 256;
    
        red1 = Math.min(red1 + 80, 255);
        green1 = Math.min(green1 + 80, 255);
        blue1 = Math.min(blue1 + 80, 255);
    
        red2 = Math.min(red2 + 80, 255);
        green2 = Math.min(green2 + 80, 255);
        blue2 = Math.min(blue2 + 80, 255);
    
        Color color1 = new Color(red1, green1, blue1);
        Color color2 = new Color(red2, green2, blue2);

        if (isDark) {
            color1 = darkenGradient(color1, 0.9f);
            color2 = darkenGradient(color2, 0.9f);
        }
    
        GradientPaint gradient = new GradientPaint(0, 0, color1, width, height, color2);
        
        return gradient;
    }

    public static Paint generateGradientFromUsername(String username, boolean isDark, int width, int height, int x, int y) {

        String skinId = UserSkinRepository.getActiveSkinForUser(username);
        
        if (skinId != null && skinId != "default") {
            return getGradientForSkin(skinId, width, height, x, y);
        }
        
        int hash = (username).hashCode();
        int colorComponent1 = (hash >>> 16) & 0xFF;
        int colorComponent2 = (hash >>> 8) & 0xFF;
        int colorComponent3 = (hash) & 0xFF;
    
        int red1 = (colorComponent1 + 128) % 256;
        int green1 = (colorComponent2 + 128) % 256;
        int blue1 = (colorComponent3 + 128) % 256;
    
        int red2 = (colorComponent1 + 180) % 256;
        int green2 = (colorComponent2 + 180) % 256;
        int blue2 = (colorComponent3 + 180) % 256;
    
        red1 = Math.min(red1 + 80, 255);
        green1 = Math.min(green1 + 80, 255);
        blue1 = Math.min(blue1 + 80, 255);
    
        red2 = Math.min(red2 + 80, 255);
        green2 = Math.min(green2 + 80, 255);
        blue2 = Math.min(blue2 + 80, 255);
    
        Color color1 = new Color(red1, green1, blue1);
        Color color2 = new Color(red2, green2, blue2);

        if (isDark) {
            color1 = darkenGradient(color1, 0.9f);
            color2 = darkenGradient(color2, 0.9f);
        }
    
        GradientPaint gradient = new GradientPaint(x, y, color1, width, height, color2);
        
        return gradient;
    }

    private static Paint getGradientForSkin(String skinId, int width, int height, int x, int y) {
        switch (skinId) {
            case "red_flame":
                return new GradientPaint(x, y, new Color(255, 100, 100), x + width, y + height, new Color(255, 0, 0));
    
            case "green_forest":
                return new GradientPaint(x, y, new Color(100, 255, 100), x + width, y + height, new Color(0, 255, 0));
    
            case "blue_ocean":
                return new GradientPaint(x, y, new Color(100, 100, 255), x + width, y + height, new Color(0, 0, 255));
    
            case "sunny_yellow":
                return new GradientPaint(x, y, new Color(255, 255, 100), x + width, y + height, new Color(255, 255, 0));
    
            case "purple_dream":
                return new GradientPaint(x, y, new Color(200, 100, 255), x + width, y + height, new Color(100, 0, 255));
    
            case "fiery_orange":
                return new GradientPaint(x, y, new Color(255, 150, 50), x + width, y + height, new Color(255, 100, 0));
    
            case "pink_blossom":
                return new GradientPaint(x, y, new Color(255, 182, 193), x + width, y + height, new Color(255, 105, 180));
            
            case "crimson_sunset":
                return new GradientPaint(x, y, new Color(255, 50, 50), x + width / 2, y + height / 2, new Color(255, 255, 0));
                
            case "lavender_haze":
                return new GradientPaint(x, y, new Color(240, 220, 255), x + width / 2, y + height / 2, new Color(70, 50, 200));
            
            case "rainbow":
                return new LinearGradientPaint(
                        new Point2D.Float(x, y), new Point2D.Float(x + width, y + height),
                        new float[]{0.0f, 0.2f, 0.4f, 0.6f, 0.8f, 1.0f},
                        new Color[]{
                            new Color(255, 0, 0),
                            new Color(255, 165, 0),
                            new Color(255, 255, 0),
                            new Color(0, 255, 0),
                            new Color(0, 0, 255),
                            new Color(75, 0, 130)
                        }
                    );

            case "sunrise":
                return new LinearGradientPaint(
                    new Point2D.Float(x, y), new Point2D.Float(x + width, y + height),
                    new float[]{0.0f, 0.2f, 0.5f, 0.7f, 1.0f},
                    new Color[]{
                        new Color(255, 94, 77),
                        new Color(255, 140, 0),
                        new Color(255, 215, 64),
                        new Color(255, 239, 210),
                        new Color(135, 206, 250)
                    }
                );

            case "golden_aura":
                return new GradientPaint(x, y, new Color(255, 223, 0), x + width, y + height, new Color(255, 140, 0));
    
            case "mystic_forest":
                return new GradientPaint(x, y, new Color(34, 139, 34), x + width, y + height, new Color(75, 0, 130));
    
            case "icy_blue":
                return new GradientPaint(x, y, new Color(173, 216, 230), x + width, y + height, new Color(70, 130, 180));
    
            case "neon_glow":
                return new GradientPaint(x, y, new Color(0, 255, 0), x + width, y + height, new Color(255, 105, 180));
    
            case "autumn_leaves":
                return new GradientPaint(x, y, new Color(255, 165, 0), x + width, y + height, new Color(255, 69, 0));
    
            case "galaxy_dream":
                return new LinearGradientPaint(
                    new Point2D.Float(x, y), new Point2D.Float(x + width, y + height),
                    new float[]{0.0f, 0.5f, 1.0f},
                    new Color[]{
                        new Color(0, 0, 128),
                        new Color(75, 0, 130),
                        new Color(238, 130, 238)
                    }
                );
    
            case "electric_lime":
                return new GradientPaint(x, y, new Color(0, 255, 0), x + width, y + height, new Color(255, 255, 0));
    
            case "chocolate_swirl":
                return new GradientPaint(x, y, new Color(139, 69, 19), x + width, y + height, new Color(205, 133, 63));
    
            case "cosmic_pink":
                return new LinearGradientPaint(
                    new Point2D.Float(x, y), new Point2D.Float(x + width, y + height),
                    new float[]{0.0f, 0.5f, 1.0f},
                    new Color[]{
                        new Color(255, 20, 147),
                        new Color(138, 43, 226),
                        new Color(75, 0, 130)
                    }
                );
    
            case "lush_meadow":
                return new GradientPaint(x, y, new Color(34, 139, 34), x + width, y + height, new Color(255, 255, 0));
    
            case "galaxy":
                return new LinearGradientPaint(
                    new Point2D.Float(x, y), new Point2D.Float(x + width, y + height),
                    new float[]{0.0f, 0.5f, 1.0f},
                    new Color[]{
                        new Color(0, 0, 128),
                        new Color(75, 0, 130),
                        new Color(238, 130, 238)
                    }
                );

            case "aurora_borealis":
                return new LinearGradientPaint(
                    new Point2D.Float(x, y), new Point2D.Float(x + width, y + height),
                    new float[]{0.0f, 0.3f, 0.6f, 1.0f},
                    new Color[]{
                        new Color(0, 255, 255),
                        new Color(0, 255, 0),
                        new Color(75, 0, 130),
                        new Color(238, 130, 238)
                    }
                );

            case "fire":
                return new LinearGradientPaint(
                    new Point2D.Float(x, y), new Point2D.Float(x + width, y + height),
                    new float[]{0.0f, 0.3f, 0.6f, 1.0f},
                    new Color[]{
                        new Color(255, 69, 0),
                        new Color(255, 140, 0),
                        new Color(255, 255, 0),
                        new Color(255, 165, 0)
                    }
                );

            case "ocean_waves":
                return new LinearGradientPaint(
                    new Point2D.Float(x, y), new Point2D.Float(x + width, y + height),
                    new float[]{0.0f, 0.5f, 1.0f},
                    new Color[]{
                        new Color(0, 105, 148),
                        new Color(0, 204, 204),
                        new Color(102, 255, 204)
                    }
                );

            case "peach_blossom":
                return new LinearGradientPaint(
                    new Point2D.Float(x, y), new Point2D.Float(x + width, y + height),
                    new float[]{0.0f, 0.5f, 1.0f},
                    new Color[]{
                        new Color(255, 218, 185),
                        new Color(255, 182, 193),
                        new Color(255, 105, 180)
                    }
                );

            case "neon_pulse":
                return new LinearGradientPaint(
                    new Point2D.Float(x, y), new Point2D.Float(x + width, y + height),
                    new float[]{0.0f, 0.2f, 0.5f, 0.8f, 1.0f},
                    new Color[]{
                        new Color(0, 255, 0),
                        new Color(255, 0, 255),
                        new Color(0, 255, 255),
                        new Color(255, 255, 0),
                        new Color(255, 165, 0)
                    }
                );

            case "retro_sunset":
                return new LinearGradientPaint(
                    new Point2D.Float(x, y), new Point2D.Float(x + width, y + height),
                    new float[]{0.0f, 0.3f, 0.7f, 1.0f},
                    new Color[]{
                        new Color(255, 94, 77),
                        new Color(255, 140, 0),
                        new Color(255, 223, 0),
                        new Color(75, 0, 130)
                    }
                );

            case "candy_dream":
                return new LinearGradientPaint(
                    new Point2D.Float(x, y), new Point2D.Float(x + width, y + height),
                    new float[]{0.0f, 0.5f, 1.0f},
                    new Color[]{
                        new Color(255, 182, 193),
                        new Color(138, 43, 226),
                        new Color(75, 0, 130)
                    }
                );

            case "neon_rainbow":
                return new LinearGradientPaint(
                    new Point2D.Float(x, y), new Point2D.Float(x + width, y + height),
                    new float[]{0.0f, 0.16f, 0.32f, 0.48f, 0.64f, 0.80f, 1.0f},
                    new Color[]{
                        new Color(255, 0, 0),
                        new Color(255, 165, 0),
                        new Color(255, 255, 0),
                        new Color(0, 255, 0),
                        new Color(0, 0, 255),
                        new Color(75, 0, 130),
                        new Color(238, 130, 238)
                    }
                );

            default:
                return new GradientPaint(x, y, new Color(200, 200, 200), x + width, y + height, new Color(255, 255, 255));
        }
    }

    public static Paint generateImagePaint(String imageUrl, int width, int height, int x, int y) {
        try {
            URL url = new URL(imageUrl);
            BufferedImage image = ImageIO.read(url);

            Rectangle rect = new Rectangle(x, y, x + width, y + height);
            TexturePaint texturePaint = new TexturePaint(image, rect);

            return texturePaint;
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    public static Color darkenGradient(Color color, float factor) {
        int r = (int) (color.getRed() * factor);
        int g = (int) (color.getGreen() * factor);
        int b = (int) (color.getBlue() * factor);
    
        r = Math.max(0, Math.min(255, r));
        g = Math.max(0, Math.min(255, g));
        b = Math.max(0, Math.min(255, b));
    
        return new Color(r, g, b);
    }

    private static final int NUM_COLUMNS = 6;

    public static BufferedImage generateGradientImage(int width, int height) {
        int numGradients = skinIds.size();
        int numRows = (int) Math.ceil((double) numGradients / NUM_COLUMNS);
        int imageHeight = numRows * (height + 50);
        int imageWidth = NUM_COLUMNS * (width + 20);

        BufferedImage image = new BufferedImage(imageWidth, imageHeight, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g2d = image.createGraphics();

        g2d.setColor(Color.WHITE);
        g2d.fillRect(0, 0, imageWidth, imageHeight);

        int xOffset = 0;
        int yOffset = 0;
        for (int i = 0; i < numGradients; i++) {
            Map<String, Object> skin = skinIds.get(i);
            String skinId = (String) skin.get("id");
            int price = (int) skin.get("price");

            int column = i % NUM_COLUMNS;
            int row = i / NUM_COLUMNS;

            xOffset = column * (width + 20);
            yOffset = row * (height + 50);

            Paint gradient = getGradientForSkin(skinId, width, height, xOffset, yOffset);

            g2d.setPaint(gradient);
            g2d.fillRect(xOffset, yOffset, width, height);

            g2d.setColor(Color.BLACK);
            g2d.setFont(new Font("Arial", Font.PLAIN, 18));
            g2d.drawString(skinId, xOffset + 10, yOffset + height + 20);

            g2d.setFont(new Font("Arial", Font.PLAIN, 16));
            g2d.drawString("Price: $" + price, xOffset + 10, yOffset + height + 40);

        }

        g2d.dispose();
        return image;
    }

    public static void copyImageToClipboard(BufferedImage image) {
        ImageSelection imageSelection = new ImageSelection(image);
        Toolkit.getDefaultToolkit().getSystemClipboard().setContents(imageSelection, null);
    }

    static class ImageSelection implements Transferable {
        private final BufferedImage image;

        public ImageSelection(BufferedImage image) {
            this.image = image;
        }

        @Override
        public DataFlavor[] getTransferDataFlavors() {
            return new DataFlavor[]{DataFlavor.imageFlavor};
        }

        @Override
        public boolean isDataFlavorSupported(DataFlavor flavor) {
            return DataFlavor.imageFlavor.equals(flavor);
        }

        @Override
        public Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException {
            if (!DataFlavor.imageFlavor.equals(flavor)) {
                throw new UnsupportedFlavorException(flavor);
            }
            return image;
        }
    }

    public static void sendAvaiableSkinsImage(){
        try {
            BufferedImage image = generateGradientImage(150, 150);
            copyImageToClipboard(image);
            MessageService.sendMessageFromClipboard(false);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
