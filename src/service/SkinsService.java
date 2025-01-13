package service;

import model.CommandContext;
import repository.UserRepository;
import repository.UserSkinRepository;

import java.util.List;
import java.util.Map;

public class SkinsService {

    private static final Map<String, Integer> SKIN_PRICES = Map.of(
        "red_flame", 10,
        "green_forest", 10,
        "blue_ocean", 10,
        "sunny_yellow", 10,
        "purple_dream", 10,
        "fiery_orange", 10,
        "pink_blossom", 10,
        "crimson_sunset", 50,
        "lavender_haze", 50
    );

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

        if (!isSkinAvailableInShop(skinId)) {
            MessageService.sendMessage("Skin " + skinId + " is not available in the shop.");
            return;
        }

        Integer skinPrice = SKIN_PRICES.get(skinId);
        if (skinPrice == null) {
            MessageService.sendMessage("Price for the skin is not defined.");
            return;
        }

        int userBalance = UserRepository.getUserBalance(userName, false);

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
            MessageService.sendMessage("You successfully bought the skin: " + skinId);
        } else {
            MessageService.sendMessage("Failed to buy skin. You might already own it or something went wrong.");
        }
    }

    private static void handleShopCommand(CommandContext context) {
        StringBuilder availableSkins = new StringBuilder("Available skins in the shop:\n");
        
        SKIN_PRICES.forEach((skin, price) -> {
            availableSkins.append(skin).append(" (").append(price).append(" coins) | ");
        });
        
        MessageService.sendMessage(availableSkins.toString().substring(0, availableSkins.length() - 3));
    }

    private static boolean isSkinAvailableInShop(String skinId) {
        return SKIN_PRICES.containsKey(skinId);
    }
}
