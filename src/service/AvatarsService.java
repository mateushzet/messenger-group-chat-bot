package service;

import model.CommandContext;
import repository.UserAvatarRepository;
import java.util.List;

public class AvatarsService {

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
                handleListCommand(context, userName);
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

    private static void handleListCommand(CommandContext context, String userName) {
        List<String> userAvatars = UserAvatarRepository.getAllAvatarsForUser(userName);
        if (userAvatars.isEmpty()) {
            MessageService.sendMessage("You don't own any avatars.");
        } else {
            MessageService.sendMessage("Your avatars: " + String.join(", ", userAvatars));
        }
    }

}
