package utils;

import java.awt.Color;
import java.util.HashMap;
import java.util.Map;

public class ColorGenerator {

    private static final Map<String, String> userSkins = new HashMap<>();

    public static void assignSkinToUser(String username, String skinId) {
        userSkins.put(username, skinId);
    }

    public static Color generateColorFromUsername(String username, int seed, boolean isDark) {

        String skinId = userSkins.get(username);
        if (skinId != null) {
            return getColorForSkin(skinId);
        }
        
        int hash = (username + seed).hashCode();
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
        
        if(isDark) return seed == 1 ? darkenColor(color1, 0.9f) : darkenColor(color2, 0.9f);
        else return seed == 1 ? color1 : color2;
    }

    private static Color getColorForSkin(String skinId) {
        switch (skinId) {
            case "skin1":
                return new Color(255, 0, 0);
            case "skin2":
                return new Color(0, 255, 0);
            case "skin3":
                return new Color(0, 0, 255);
            default:
                return new Color(255, 255, 255);
        }
    }

    public static Color darkenColor(Color color, float factor) {
        int r = (int) (color.getRed() * factor);
        int g = (int) (color.getGreen() * factor);
        int b = (int) (color.getBlue() * factor);
    
        r = Math.max(0, Math.min(255, r));
        g = Math.max(0, Math.min(255, g));
        b = Math.max(0, Math.min(255, b));
    
        return new Color(r, g, b);
    }
}
