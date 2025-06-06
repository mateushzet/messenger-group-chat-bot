package service;

import java.util.List;

import repository.BindRepository;

public class BindService {

    public static String getUserCommand(String username, int bindId) {
        String command = BindRepository.getCommand(username, bindId);
        if (command == null) {
            MessageService.sendMessage(username + ", no command bound to ID " + bindId + ".");
        }
        return command;
    }

    public static void saveUserCommand(String username, int bindId, String command) {
        boolean success = BindRepository.saveBind(username, bindId, command);
        if (success) {
            MessageService.sendMessage(username + ", your bind was saved successfully!");
        } else {
            MessageService.sendMessage(username + ", failed to save your bind.");
        }
    }

    public static String listUserBinds(String username) {
        List<String> binds = BindRepository.getUserBinds(username);

        if (binds.isEmpty()) {
            return username + " has no binds saved.";
        }

        StringBuilder sb = new StringBuilder();
        sb.append("Binds for ").append(username).append(":\n");
        for (String bind : binds) {
            sb.append(bind).append("\n");
        }

        return sb.toString().trim();
    }   
}