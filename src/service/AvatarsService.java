package service;

import model.CommandContext;
import repository.UserAvatarRepository;
import utils.ImageUtils;
import utils.Logger;

import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

import javax.imageio.ImageIO;

import java.awt.*;

public class AvatarsService {

    private static final File USER_AVATAR_DIR = Paths.get("src", "resources", "user_avatars").toFile();

    public static void handleAvatarsCommand(CommandContext context) {
        String userName = context.getUserName();
        String firstArg = context.getFirstArgument();
        String secondArg = context.getArgumentsJoined();
        
        System.out.println(secondArg);

        if (firstArg == null) {
            MessageService.sendMessage("Available commands: set, list");
            return;
        }

        switch (firstArg.toLowerCase()) {
            case "set":
                handleSetCommand(context, userName, secondArg);
                break;

            case "list":
                handleListCommand(userName);
                break;

            default:
                MessageService.sendMessage("Unknown command. Available commands: set, list");
                break;
        }
    }

    public static void handleSetCommand(CommandContext context, String userName, String avatarId) {
        if (avatarId == null) {
            MessageService.sendMessage("Usage: avatar set <avatar_id>");
            return;
        }
    
        boolean success = UserAvatarRepository.updateActiveAvatarForUser(userName, avatarId);
        if (success) {
            MessageService.sendMessage("Avatar set successfully to: " + avatarId);
        } else {
            MessageService.sendMessage("Failed to set avatar. Please ensure you own the avatar.");
        }
    }

    private static void handleListCommand(String userName) {
        List<String> userAvatars = UserAvatarRepository.getAllAvatarsForUser(userName);
        if (userAvatars.isEmpty()) {
            MessageService.sendMessage("You don't own any avatars.");
        } else {
            BufferedImage preview = generateUserAvatarsPreviewImage(userAvatars);
            ImageUtils.setClipboardImage(preview);
            MessageService.sendMessageFromClipboard(true);
        }
    }

    private static BufferedImage generateUserAvatarsPreviewImage(List<String> avatarNames) {
        final int avatarWidth = 150;
        final int avatarHeight = 100;
        final int padding = 30;
        final int textHeight = 40;

        int total = avatarNames.size();
        int columns = (int) Math.ceil(Math.sqrt(total));
        int rows = (int) Math.ceil(total / (double) columns);

        int width = columns * (avatarWidth + padding) + padding;
        int height = rows * (avatarHeight + textHeight + padding) + padding;

        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        g.setColor(Color.DARK_GRAY);
        g.fillRect(0, 0, width, height);

        g.setColor(Color.WHITE);
        g.setFont(new Font("Arial", Font.BOLD, 14));
        FontMetrics fm = g.getFontMetrics();

        for (int i = 0; i < avatarNames.size(); i++) {
            String avatarName = avatarNames.get(i);
            int col = i % columns;
            int row = i / columns;

            int x = padding + col * (avatarWidth + padding);
            int y = padding + row * (avatarHeight + textHeight + padding);

            try {
                File avatarFile = new File(USER_AVATAR_DIR, avatarName + ".png");
                if (!avatarFile.exists()) continue;

                BufferedImage avatar = ImageIO.read(avatarFile);
                Image scaled = avatar.getScaledInstance(avatarHeight, avatarHeight, Image.SCALE_SMOOTH);
                g.drawImage(scaled, x + (avatarWidth - avatarHeight) / 2, y, null);

                List<String> lines = splitTextToFit(avatarName, fm, avatarWidth);
                int textY = y + avatarHeight + fm.getAscent();
                for (String line : lines) {
                    int textWidth = fm.stringWidth(line);
                    int textX = x + (avatarWidth - textWidth) / 2;
                    g.drawString(line, textX, textY);
                    textY += fm.getHeight();
                }

            } catch (IOException e) {
                Logger.logError("Couldn't load avatar: " + avatarName, "generateUserAvatarsPreviewImage", e);
            }
        }

        g.dispose();
        return image;
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
