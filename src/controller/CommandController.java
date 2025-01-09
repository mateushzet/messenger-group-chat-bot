package controller;

import model.CommandContext;
import service.MessageService;
import service.SlotsService;
import service.roulette.RouletteService;
import utils.ConfigReader;
import utils.LoggerUtil;
import service.ColorsService;
import service.CommandService;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

public class CommandController {
    
    private static final Map<String, Consumer<CommandContext>> commands = new HashMap<>();
    private static final String botCommand = ConfigReader.getBotCommand();

    static {
        commands.put("time", CommandService::handleTimeCommand);
        commands.put("money", CommandService::handleMoneyCommand);
        commands.put("roulette", RouletteService::handleRouletteCommand);
        commands.put("kill", CommandService::handleKillCommand);
        commands.put("stop", CommandService::handleStopCommand);
        commands.put("start", CommandService::handleStartCommand);
        commands.put("status", CommandService::handleStatusCommand);
        commands.put("say", CommandService::handleSayCommand);
        commands.put("answer", CommandService::handleAnswerCommand);
        commands.put("transfer", CommandService::handleTransferCommand);
        commands.put("rank", CommandService::handleRankCommand);
        commands.put("help", CommandService::handleHelpCommand);
        commands.put("slots", SlotsService::handleSlotsCommand);
        commands.put("buy", CommandController::handleBuyCommand);        
        commands.put("daily", CommandService::handleDailyCommand); 
        commands.put("hourly", CommandService::handleHourlyCommand); 
        commands.put("coinflip", CommandService::handleCoinflipCommand);
        commands.put("colors", ColorsService::handleColorsCommand);
    }

    public static void processCommand(String userName, String message) {
        CommandContext context = parseCommand(message, userName);
        Consumer<CommandContext> commandHandler = commands.get(context.getCommand().toLowerCase());
        
        if (commandHandler != null) {
            commandHandler.accept(context);
        } else {
            MessageService.sendMessage("Unknown command: %s", context.getCommand());
            LoggerUtil.logWarning("Unknown command: %s", context.getCommand());
        }
    }

    private static CommandContext parseCommand(String message, String userName) {
        String commandAndArgs;
            if (message.startsWith(botCommand) && message.length() > botCommand.length()) {
                commandAndArgs = message.substring(botCommand.length()+1).trim();
            } else {
                commandAndArgs = "";
                LoggerUtil.logWarning("Missing command");
            }

        String[] parts = commandAndArgs.split(" ", 2);
        String command = parts[0].trim();
        List<String> arguments = new ArrayList<>();

        if (parts.length > 1) {
            String argumentsString = parts[1].trim();
            String[] args = argumentsString.split(" ");
            for (String arg : args) {
                arguments.add(arg);
            }
        }

        return new CommandContext(command, arguments, userName);
    }

    private static void handleBuyCommand(CommandContext context){
        if(context.getFirstArgument().equals("slots")){
            SlotsService.handleBuySlotsCommand(context);
        } else {
            ColorsService.handleBuyColorsCommand(context);
        }

    }

}
