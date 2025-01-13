package utils;

import java.awt.Color;
import java.awt.GradientPaint;
import java.util.HashMap;
import java.util.Map;

import repository.UserSkinRepository;

public class GradientGenerator {

    private static final Map<String, String> userSkins = new HashMap<>();

    public static void assignSkinToUser(String username, String skinId) {
        userSkins.put(username, skinId);
    }

    public static GradientPaint generateGradientFromUsername(String username, boolean isDark, int width, int height) {

        String skinId = UserSkinRepository.getActiveSkinForUser(username);
        
        if (skinId != null && skinId != "default") {
            return getGradientForSkin(skinId, width, height);
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

    public static GradientPaint generateGradientFromUsername(String username, boolean isDark, int width, int height, int x, int y) {

        String skinId = UserSkinRepository.getActiveSkinForUser(username);
        
        if (skinId != null && skinId != "default") {
            return getGradientForSkin(skinId, width, height);
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

    private static GradientPaint getGradientForSkin(String skinId, int width, int height) {
        switch (skinId) {
            case "red_flame":
                return new GradientPaint(0, 0, new Color(255, 100, 100), width, height, new Color(255, 0, 0));
    
            case "green_forest":
                return new GradientPaint(0, 0, new Color(100, 255, 100), width, height, new Color(0, 255, 0));
    
            case "blue_ocean":
                return new GradientPaint(0, 0, new Color(100, 100, 255), width, height, new Color(0, 0, 255));
    
            case "sunny_yellow":
                return new GradientPaint(0, 0, new Color(255, 255, 100), width, height, new Color(255, 255, 0));
    
            case "purple_dream":
                return new GradientPaint(0, 0, new Color(200, 100, 255), width, height, new Color(100, 0, 255));
    
            case "fiery_orange":
                return new GradientPaint(0, 0, new Color(255, 150, 50), width, height, new Color(255, 100, 0));
    
            case "pink_blossom":
                return new GradientPaint(0, 0, new Color(255, 182, 193), width, height, new Color(255, 105, 180));
    
            default:
                return new GradientPaint(0, 0, new Color(200, 200, 200), width, height, new Color(255, 255, 255));
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
}
