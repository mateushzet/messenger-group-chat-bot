package utils;

import java.awt.*;
import java.awt.image.BufferedImage;

public class DailyRewardImageGenerator {

    public static BufferedImage generateDailyRewardImage(String username, int currentDay, int[] rewardAmounts, boolean alreadyClaimed) {
        final int width = 800;
        final int height = 300;
        final int boxWidth = 90, boxHeight = 100, boxSpacing = 20;
        final int startX = (width - (7 * boxWidth + 6 * boxSpacing)) / 2;
        final int startY = 150;

        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        try {
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

            Paint gradient = GradientGenerator.generateGradientFromUsername(username, false, width, height);
            g.setPaint(gradient);
            g.fillRect(0, 0, width, height);

            g.setColor(new Color(0, 0, 0, 100));
            g.fillRoundRect(10, 30, width - 20, height - 40, 30, 30);

            g.setColor(Color.WHITE);
            g.setFont(new Font("Arial", Font.BOLD, 24));
            String userText = username;
            int userWidth = g.getFontMetrics().stringWidth(userText);
            g.drawString(userText, (width - userWidth) / 2, 70);

            String message = alreadyClaimed
                ? "You've already claimed your reward. Come back tomorrow!"
                : "You received $" + rewardAmounts[currentDay] + " today!";
            g.setFont(new Font("Arial", Font.PLAIN, 20));
            int msgWidth = g.getFontMetrics().stringWidth(message);
            g.drawString(message, (width - msgWidth) / 2, 110);

            for (int i = 0; i < 7; i++) {
                int x = startX + i * (boxWidth + boxSpacing);
                int y = startY;

                if (i < currentDay) {
                    g.setColor(new Color(0, 150, 0, 180));
                } else {
                    g.setColor(new Color(100, 100, 100, 120));
                }
                g.fillRoundRect(x, y, boxWidth, boxHeight, 20, 20);

                if (!alreadyClaimed && i == currentDay) {
                    g.setColor(new Color(255, 215, 0));
                    g.setStroke(new BasicStroke(4));
                } else {
                    g.setColor(Color.WHITE);
                    g.setStroke(new BasicStroke(2));
                }
                g.drawRoundRect(x, y, boxWidth, boxHeight, 20, 20);



                g.setFont(new Font("Arial", Font.BOLD, 16));
                String dayText = "Day " + (i + 1);
                int dayW = g.getFontMetrics().stringWidth(dayText);
                g.setColor(Color.WHITE);
                g.drawString(dayText, x + (boxWidth - dayW) / 2, y + 30);

                g.setFont(new Font("Arial", Font.PLAIN, 14));
                String amt = "$" + rewardAmounts[i];
                int amtW = g.getFontMetrics().stringWidth(amt);
                g.drawString(amt, x + (boxWidth - amtW) / 2, y + 60);
            }

        } finally {
            g.dispose();
        }

        return image;
    }

}