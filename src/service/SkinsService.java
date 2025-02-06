package service;

import model.CommandContext;
import repository.UserRepository;
import repository.UserSkinRepository;
import utils.GradientGenerator;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class SkinsService {

    private static final Map<String, Integer> SKIN_PRICES = new HashMap<>();
    static {
        SKIN_PRICES.put("red_flame", 10);
        SKIN_PRICES.put("green_forest", 10);
        SKIN_PRICES.put("blue_ocean", 10);
        SKIN_PRICES.put("sunny_yellow", 10);
        SKIN_PRICES.put("purple_dream", 10);
        SKIN_PRICES.put("fiery_orange", 10);
        SKIN_PRICES.put("pink_blossom", 10);
        SKIN_PRICES.put("crimson_sunset", 50);
        SKIN_PRICES.put("lavender_haze", 50);
        SKIN_PRICES.put("rainbow", 100);
        SKIN_PRICES.put("sunrise", 100);
    }

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
                handleListCommand(context, userName);
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

    private static void handleListCommand(CommandContext context, String userName) {
        List<String> userSkins = UserSkinRepository.getAllSkinsForUser(userName);
        if (userSkins.isEmpty()) {
            MessageService.sendMessage("You don't own any skins.");
        } else {
            MessageService.sendMessage("Your skins: " + String.join(", ", userSkins));
        }
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

}
