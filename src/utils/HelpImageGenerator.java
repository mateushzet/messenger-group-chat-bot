package utils;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.Map;

import javax.imageio.ImageIO;

import model.GameHelp;

public class HelpImageGenerator {

    private static final String BASE_PATH = "src/resources/help_images/";

    public static void generateMainMenu(String username) {
        int width = 600;
        int height = 400;
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = image.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setPaint(GradientGenerator.generateGradientFromUsername(username, false, width, height));
        g.fillRect(0, 0, width, height);

        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 36));
        g.drawString("HELP MENU", 20, 60);

        Map<String, String> defaultCommands = Map.of(
            "games", "games",
            "rewards", "rewards",
            "settings", "settings"
        );

        int baseY = 130;
        int spacing = 100;
        int iconSize = 64;
        int rectX = 30;
        int rectWidth = width - 60;
        int rectHeight = iconSize + 30;

        g.setFont(new Font("Arial", Font.PLAIN, 36));

        int index = 0;
        for (String command : defaultCommands.keySet()) {
            String iconName = defaultCommands.get(command);
            int yPosition = baseY + index * spacing;
            int rectY = yPosition - iconSize + 10;

            g.setColor(new Color(0, 0, 0, 150));
            g.fillRoundRect(rectX, rectY, rectWidth, rectHeight, 20, 20);

            try {
                BufferedImage icon = loadImage(iconName);
                g.drawImage(icon, 40, yPosition - iconSize + 25, iconSize, iconSize, null);
            } catch (IOException e) {
                System.err.println("Missing icon for " + command + ": " + e.getMessage());
            }

            String text = "/help " + command;
            g.setColor(new Color(0, 0, 0, 150));
            g.drawString(text, 120 + 2, yPosition + 2);
            g.setColor(Color.WHITE);
            g.drawString(text, 120, yPosition);

            index++;
        }

        g.dispose();
        ImageUtils.setClipboardImage(image);
    }

    public static void generateGameList(String username) {
        List<String> games = HelpDataProvider.getGames();
        int width = 700;
        int rows = (games.size() + 1) / 2;
        int height = 120 + rows * 60;
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = image.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setPaint(GradientGenerator.generateGradientFromUsername(username, false, width, height));
        g.fillRect(0, 0, width, height);

        g.setFont(new Font("SansSerif", Font.BOLD, 32));
        g.setColor(Color.WHITE);
        g.drawString("🎮 Games", 20, 60);

        Font listFont = new Font("SansSerif", Font.PLAIN, 28);
        g.setFont(listFont);

        int baseX1 = 40;
        int baseX2 = width / 2 + 20;
        int baseY = 120;
        int spacingY = 60;
        int rectHeight = 40;
        int rectPadding = 10;
        int columnWidth = width / 2 - 60;
        int iconSize = 32;

        for (int i = 0; i < games.size(); i++) {
            String game = games.get(i);
            int row = i % rows;
            int col = i / rows;

            int xPosition = (col == 0) ? baseX1 : baseX2;
            int yPosition = baseY + row * spacingY;

            g.setColor(new Color(0, 0, 0, 100));
            g.fillRoundRect(xPosition - rectPadding, yPosition - rectHeight + 10, columnWidth, rectHeight, 15, 15);

            try {
                BufferedImage icon = loadImage(game);
                g.drawImage(icon, xPosition, yPosition - iconSize + 10, iconSize, iconSize, null);
            } catch (IOException ignored) {
            }

            int textX = xPosition + iconSize + 10;
            g.setColor(new Color(0, 0, 0, 150));
            g.drawString("/help " + game, textX + 2, yPosition + 2);
            g.setColor(Color.WHITE);
            g.drawString("/help " + game, textX, yPosition);
        }

        g.dispose();
        ImageUtils.setClipboardImage(image);
    }

    public static void generateGameHelp(String gameName, String username) {
        GameHelp gameHelp = HelpDataProvider.getGameHelp(gameName);
        BufferedImage exampleImage = gameHelp.getExampleImage();
        int width = 1000;
        int padding = 20;
        int startDescriptionY = 100;

        BufferedImage tempImage = new BufferedImage(1, 1, BufferedImage.TYPE_INT_RGB);
        Graphics2D gTemp = tempImage.createGraphics();
        gTemp.setFont(new Font("Arial", Font.PLAIN, 20));
        FontMetrics fm = gTemp.getFontMetrics();
        int lineHeight = fm.getHeight();
        gTemp.dispose();

        int maxTextWidth = width - 2 * padding;
        int descriptionLines = drawWrappedText(null, "Description: " + gameHelp.getDescription(), 0, 0, maxTextWidth, lineHeight);
        int commandLines = gameHelp.getCommands().size();
        int commandLineHeight = 30;
        int startCommandsY = startDescriptionY + descriptionLines * lineHeight + 20;
        int textHeight = startCommandsY + commandLines * commandLineHeight + padding;
        int height = Math.max(textHeight, exampleImage.getHeight() + 2 * padding);

        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = image.createGraphics();
        g.setPaint(GradientGenerator.generateGradientFromUsername(username, false, width, height));
        g.fillRect(0, 0, width, height);

        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 26));
        try {
            BufferedImage icon = loadImage(gameName);
            g.drawImage(icon, 20, 20, 32, 32, null);
        } catch (IOException e) {
            g.drawString(gameName, 20, 50);
        }

        g.drawString(gameName, 60, 50);
        g.setFont(new Font("Arial", Font.PLAIN, 20));
        drawWrappedText(g, "Description: " + gameHelp.getDescription(), padding, startDescriptionY, maxTextWidth, lineHeight);

        int y = startCommandsY;
        for (String cmd : gameHelp.getCommands()) {
            g.drawString(cmd, padding, y);
            y += commandLineHeight;
        }

        int imageX = width - exampleImage.getWidth() - padding;
        int imageY = height - exampleImage.getHeight() - padding;
        g.drawImage(exampleImage, imageX, imageY, null);

        g.dispose();
        ImageUtils.setClipboardImage(image);
    }

    public static void generateRewardsList(String username) {
        List<String> rewards = List.of("daily", "weekly", "hourly", "gift", "answer");

        Map<String, String> rewardDescriptions = Map.of(
            "daily", "Get your daily bonus reward",
            "weekly", "Claim weekly bonus rewards",
            "hourly", "Receive hourly rewards on a full hour",
            "gift", "Send a daily gift to other player",
            "answer", "Rewards for solving hourly random math questions"
        );

        int width = 600;
        int height = 200 + rewards.size() * 60;
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = image.createGraphics();

        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setPaint(GradientGenerator.generateGradientFromUsername(username, false, width, height));
        g.fillRect(0, 0, width, height);

        g.setFont(new Font("SansSerif", Font.BOLD, 32));
        g.setColor(Color.WHITE);
        g.drawString("🎁 Rewards", 20, 60);

        Font listFont = new Font("SansSerif", Font.PLAIN, 24);
        g.setFont(listFont);

        int baseX = 40;
        int baseY = 120;
        int spacingY = 80;
        int rectHeight = 60;
        int rectPadding = 10;
        int iconSize = 32;
        int rectWidth = width - 2 * baseX;

        for (int i = 0; i < rewards.size(); i++) {
            String reward = rewards.get(i);
            int yPosition = baseY + i * spacingY;

            g.setColor(new Color(0, 0, 0, 100));
            g.fillRoundRect(baseX - rectPadding, yPosition - rectHeight + 30, rectWidth, rectHeight, 15, 15);

            try {
                BufferedImage icon = loadImage(reward);
                g.drawImage(icon, baseX, yPosition - iconSize + 10, iconSize, iconSize, null);
            } catch (IOException ignored) {
            }

            int textX = baseX + iconSize + 10;
            String commandText = "/help " + reward;
            String description = rewardDescriptions.getOrDefault(reward, "");

            g.setColor(new Color(0, 0, 0, 150));
            g.drawString(commandText, textX + 2, yPosition + 2);
            g.setColor(Color.WHITE);
            g.drawString(commandText, textX, yPosition);

            g.setColor(new Color(255, 255, 255, 180));
            g.setFont(new Font("SansSerif", Font.PLAIN, 18));
            g.drawString(description, textX, yPosition + 20);
            g.setFont(listFont);
        }

        g.dispose();
        ImageUtils.setClipboardImage(image);
    }

    private static int drawWrappedText(Graphics2D g, String text, int x, int y, int maxWidth, int lineHeight) {
        if (g == null) {
            String[] words = text.split(" ");
            int lines = 1;
            int currentWidth = 0;
            for (String word : words) {
                int wordWidth = word.length() * 7;
                if (currentWidth + wordWidth > maxWidth) {
                    lines++;
                    currentWidth = wordWidth;
                } else {
                    currentWidth += wordWidth + 7;
                }
            }
            return lines;
        }

        String[] words = text.split(" ");
        StringBuilder line = new StringBuilder();
        int yOffset = y;

        for (String word : words) {
            String testLine = line + (line.length() == 0 ? "" : " ") + word;
            int lineWidth = g.getFontMetrics().stringWidth(testLine);
            if (lineWidth > maxWidth) {
                g.drawString(line.toString(), x, yOffset);
                line = new StringBuilder(word);
                yOffset += lineHeight;
            } else {
                if (line.length() > 0) line.append(" ");
                line.append(word);
            }
        }
        if (line.length() > 0) {
            g.drawString(line.toString(), x, yOffset);
        }

        return (yOffset - y) / lineHeight + 1;
    }

    public static BufferedImage loadImage(String name) throws IOException {
        String fileName = name.toLowerCase().replaceAll("\\s+", "_") + ".png";
        File file = new File(BASE_PATH + fileName);
        if (!file.exists()) {
            throw new IOException("Missing file: " + file.getAbsolutePath());
        }
        return ImageIO.read(file);
    }

}