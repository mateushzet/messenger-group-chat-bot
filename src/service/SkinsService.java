package service;

import model.CommandContext;
import repository.UserRepository;
import repository.UserSkinRepository;
import utils.GradientGenerator;
import utils.ImageUtils;
import utils.ImageUtils;

import java.util.ArrayList;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.awt.*;
import java.awt.image.BufferedImage;

public class SkinsService {

    public static void handleSkinsCommand(CommandContext context) {
        String userName = context.getUserName();
        String firstArg = context.getFirstArgument();
        String secondArg = context.getSecondArgument();
        
        if (firstArg == null) {
            MessageService.sendMessage("Available commands: set, list, buy, shop");
            return;
        }

        switch (firstArg.toLowerCase()) {
            case "set":
                handleSetCommand(context, userName, secondArg);
                break;

            case "list":
                handleListCommand(userName);
                handleListCommand(userName);
                break;

            case "buy":
                handleBuyCommand(context, userName, secondArg);
                break;

            case "shop":
                handleShopCommand(context);
                break;

            default:
                MessageService.sendMessage("Unknown command. Available commands: set, list, buy, shop");
                break;
        }
    }

    public static void handleSetCommand(CommandContext context, String userName, String skinId) {
        if (skinId == null) {
            MessageService.sendMessage("Usage: skins set <skin_id>");
            return;
        }
    
        boolean success = UserSkinRepository.updateActiveSkinForUser(userName, skinId);
        if (success) {
            MessageService.sendMessage("Skin set successfully to: " + skinId);
        } else {
            MessageService.sendMessage("Failed to set skin. Please ensure you own the skin.");
        }
    }

    private static void handleListCommand(String userName) {
    private static void handleListCommand(String userName) {
        List<String> userSkins = UserSkinRepository.getAllSkinsForUser(userName);
        if (userSkins.isEmpty()) {
            MessageService.sendMessage("You don't own any skins.");
        } else {
            BufferedImage previewImage = generateUserSkinsPreviewImage(userName, userSkins);
            ImageUtils.setClipboardImage(previewImage);
            MessageService.sendMessageFromClipboard(true);
        }
    }

    private static BufferedImage generateUserSkinsPreviewImage(String userName, List<String> skinNames) {
        final int boxSize = 150;
        final int padding = 20;
        final int textHeight = 40;

        int total = skinNames.size();
        int columns = (int) Math.ceil(Math.sqrt(total));
        int rows = (int) Math.ceil((double) total / columns);

        int width = columns * (boxSize + padding) + padding;
        int height = rows * (boxSize + textHeight + padding) + padding;

        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        try {
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

            g.setColor(Color.DARK_GRAY);
            g.fillRect(0, 0, width, height);

            g.setFont(new Font("Arial", Font.BOLD, 14));
            FontMetrics fm = g.getFontMetrics();

            for (int i = 0; i < total; i++) {
                String skinName = skinNames.get(i);
                int col = i % columns;
                int row = i / columns;

                int x = padding + col * (boxSize + padding);
                int y = padding + row * (boxSize + textHeight + padding);

                Paint skinGradient = GradientGenerator.generateGradientFromSkinId(skinName, userName, boxSize, boxSize, x, y);
                g.setPaint(skinGradient);
                g.fillRoundRect(x, y, boxSize, boxSize, 15, 15);

                g.setColor(new Color(0, 0, 0, 100));
                g.fillRoundRect(x, y + boxSize, boxSize, textHeight, 15, 15);

                List<String> lines = splitTextToFit(skinName, fm, boxSize - 10);

                g.setColor(Color.WHITE);
                int textY = y + boxSize + fm.getAscent() + 5;
                for (String line : lines) {
                    int textWidth = fm.stringWidth(line);
                    int textX = x + (boxSize - textWidth) / 2;
                    g.drawString(line, textX, textY);
                    textY += fm.getHeight();
                }
            }
        } finally {
            g.dispose();
        }

        return image;
            BufferedImage previewImage = generateUserSkinsPreviewImage(userName, userSkins);
            ImageUtils.setClipboardImage(previewImage);
            MessageService.sendMessageFromClipboard(true);
        }
    }

    private static BufferedImage generateUserSkinsPreviewImage(String userName, List<String> skinNames) {
        final int boxSize = 150;
        final int padding = 20;
        final int textHeight = 40;

        int total = skinNames.size();
        int columns = (int) Math.ceil(Math.sqrt(total));
        int rows = (int) Math.ceil((double) total / columns);

        int width = columns * (boxSize + padding) + padding;
        int height = rows * (boxSize + textHeight + padding) + padding;

        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        try {
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

            g.setColor(Color.DARK_GRAY);
            g.fillRect(0, 0, width, height);

            g.setFont(new Font("Arial", Font.BOLD, 14));
            FontMetrics fm = g.getFontMetrics();

            for (int i = 0; i < total; i++) {
                String skinName = skinNames.get(i);
                int col = i % columns;
                int row = i / columns;

                int x = padding + col * (boxSize + padding);
                int y = padding + row * (boxSize + textHeight + padding);

                Paint skinGradient = GradientGenerator.generateGradientFromSkinId(skinName, userName, boxSize, boxSize, x, y);
                g.setPaint(skinGradient);
                g.fillRoundRect(x, y, boxSize, boxSize, 15, 15);

                g.setColor(new Color(0, 0, 0, 100));
                g.fillRoundRect(x, y + boxSize, boxSize, textHeight, 15, 15);

                List<String> lines = splitTextToFit(skinName, fm, boxSize - 10);

                g.setColor(Color.WHITE);
                int textY = y + boxSize + fm.getAscent() + 5;
                for (String line : lines) {
                    int textWidth = fm.stringWidth(line);
                    int textX = x + (boxSize - textWidth) / 2;
                    g.drawString(line, textX, textY);
                    textY += fm.getHeight();
                }
            }
        } finally {
            g.dispose();
        }

        return image;
    }

    private static void handleBuyCommand(CommandContext context, String userName, String skinId) {
        if (skinId == null) {
            MessageService.sendMessage("Usage: skins buy <skin_id>");
            return;
        }
    
        Map<String, Object> skin = findSkinById(skinId);
        if (skin == null) {
            MessageService.sendMessage("Skin " + skinId + " is not available in the shop.");
            return;
        }
    
        int skinPrice = (int) skin.get("price");
        int userBalance = UserRepository.getCurrentUserBalance(userName, false);
    
        if (userBalance < skinPrice) {
            MessageService.sendMessage("You don't have enough coins to buy this skin.");
            return;
        }
    
        boolean balanceUpdated = UserRepository.updateUserBalance(userName, (userBalance - skinPrice));
        if (!balanceUpdated) {
            MessageService.sendMessage("Failed to update user balance.");
            return;
        }
    
        boolean success = UserSkinRepository.assignSkinToUser(userName, skinId);
        if (success) {
            MessageService.sendMessage("You successfully bought the skin: " + skin.get("name"));
        } else {
            MessageService.sendMessage("Failed to buy skin. You might already own it or something went wrong.");
        }
    }
    
    private static Map<String, Object> findSkinById(String skinId) {
        for (Map<String, Object> skin : GradientGenerator.skinIds) {
            if (skin.get("id").equals(skinId)) {
                return skin;
            }
        }
        return null;
    }

    private static void handleShopCommand(CommandContext context) {
        GradientGenerator.sendAvaiableSkinsImage();
    }

        private static List<String> splitTextToFit(String text, FontMetrics fm, int maxWidth) {
        List<String> result = new ArrayList<>();
        if (fm.stringWidth(text) <= maxWidth) {
            result.add(text);
            return result;
        }

        int mid = text.length() / 2;
        int splitIndex = mid;

        for (int offset = 0; offset < mid; offset++) {
            int left = mid - offset;
            int right = mid + offset;
            if (left > 0 && (text.charAt(left) == '_' || text.charAt(left) == ' ')) {
                splitIndex = left;
                break;
            }
            if (right < text.length() && (text.charAt(right) == '_' || text.charAt(right) == ' ')) {
                splitIndex = right;
                break;
            }
        }

        String first = text.substring(0, splitIndex).trim();
        String second = text.substring(splitIndex).trim();

        if (fm.stringWidth(first) > maxWidth) first = truncateToFit(first, fm, maxWidth);
        if (fm.stringWidth(second) > maxWidth) second = truncateToFit(second, fm, maxWidth);

        result.add(first);
        result.add(second);
        return result;
    }

    private static String truncateToFit(String text, FontMetrics fm, int maxWidth) {
        while (fm.stringWidth(text + "...") > maxWidth && text.length() > 1) {
            text = text.substring(0, text.length() - 1);
        }
        return text + "...";
    }
}
