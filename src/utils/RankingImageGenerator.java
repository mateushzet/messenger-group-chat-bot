package utils;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.util.List;
import java.util.Map;

public class RankingImageGenerator {

    public static void generateRankingImage(List<Map.Entry<String, Integer>> sortedUsers, String reguesterName) {
        int imageWidth = 600;
        int imageHeight = 100 + sortedUsers.size() * 50;
        BufferedImage image = new BufferedImage(imageWidth, imageHeight, BufferedImage.TYPE_INT_RGB);

        Graphics2D g = image.createGraphics();

        Paint gradient = GradientGenerator.generateGradientFromUsername(reguesterName, false, imageWidth, imageHeight);
        
        g.setPaint(gradient);
        g.fillRect(0, 0, imageWidth, imageHeight);

        g.setFont(new Font("Arial", Font.BOLD, 32));
        g.setColor(Color.BLACK);
        g.drawString("User Ranking", 20, 50);

        int yPosition = 100;
        for (int i = 0; i < sortedUsers.size(); i++) {
            Map.Entry<String, Integer> entry = sortedUsers.get(i);
            String username = entry.getKey();
            int balance = entry.getValue();

            Color transparentBlack = new Color(0, 0, 0, 127);
            g.setColor(transparentBlack);
            g.fillRect(10, yPosition - 35, imageWidth - 20, 40);

            if (i == 0) {
                g.setColor(new Color(218, 165, 32));
            } else if (i == 1) {
                g.setColor(new Color(169, 169, 169));
            } else if (i == 2) {
                g.setColor(new Color(180, 100, 60));
            } else {
                g.setColor(Color.WHITE); 
            }

            g.drawString((i + 1) + ". " + username + " - " + balance + " coins", 20, yPosition);

            yPosition += 50;
        }

        g.dispose();
        ImageUtils.setClipboardImage(image);
    }

}