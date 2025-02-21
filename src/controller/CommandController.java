package controller;

import model.CommandContext;
import service.MessageService;
import service.SkinsService;
import service.StatisticsService;
import utils.ConfigReader;
import utils.Logger;
import service.AvatarsService;
import service.BitcoinService;
import service.CommandService;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

import games.blackjack.BlackjackService;
import games.caseopening.CaseOpeningService;
import games.coinflip.CoinflipService;
import games.colors.ColorsService;
import games.crash.CrashService;
import games.dice.DiceGameService;
import games.horseRace.HorseRaceBettingService;
import games.lotto.LottoService;
import games.mines.MinesService;
import games.plinko.PlinkoService;
import games.roulette.RouletteService;
import games.slots.SlotsService;

public class CommandController {
    
    private static final Map<String, Consumer<CommandContext>> commands = new HashMap<>();
    private static final String botCommand = ConfigReader.getBotCommand();
    private static final String botAlternativeCommand = ConfigReader.getBotAlternativeCommand();

    static {
        commands.put("time", CommandService::handleTimeCommand);
        commands.put("money", CommandService::handleMoneyCommand);
        commands.put("roulette", RouletteService::handleRouletteCommand);
        commands.put("r", RouletteService::handleRouletteCommand);
        commands.put("kill", CommandService::handleKillCommand);
        commands.put("stop", CommandService::handleStopCommand);
        commands.put("start", CommandService::handleStartCommand);
        commands.put("status", CommandService::handleStatusCommand);
        commands.put("say", CommandService::handleSayCommand);
        commands.put("answer", CommandService::handleAnswerCommand);
        commands.put("a", CommandService::handleAnswerCommand);
        commands.put("transfer", CommandService::handleTransferCommand);
        commands.put("t", CommandService::handleTransferCommand);
        commands.put("rank", CommandService::handleRankCommand);
        commands.put("help", CommandService::handleHelpCommand);
        commands.put("slots", SlotsService::handleSlotsCommand);
        commands.put("s", SlotsService::handleSlotsCommand);
        commands.put("buy", CommandController::handleBuyCommand);        
        commands.put("daily", CommandService::handleDailyCommand); 
        commands.put("hourly", CommandService::handleHourlyCommand); 
        commands.put("h", CommandService::handleHourlyCommand); 
        commands.put("coinflip", CoinflipService::handleCoinflipCommand);
        commands.put("colors", ColorsService::handleColorsCommand);
        commands.put("c", ColorsService::handleColorsCommand);
        commands.put("mines", MinesService::handleMinesCommand);
        commands.put("m", MinesService::handleMinesCommand);
        commands.put("skins", SkinsService::handleSkinsCommand);
        commands.put("lotto", LottoService::handleLottoCommand);
        commands.put("l", LottoService::handleLottoCommand);
        commands.put("race", HorseRaceBettingService::handleRaceCommand);
        commands.put("sports", MatchController::handleSportsBettingCommand);
        commands.put("blackjack", BlackjackService::handleBlackjackCommand);
        commands.put("bj", BlackjackService::handleBlackjackCommand);
        commands.put("plinko", PlinkoService::handlePlinkoCommand);
        commands.put("p", PlinkoService::handlePlinkoCommand);
        commands.put("stats", StatisticsService::handleStatsCommand);
        commands.put("dice", DiceGameService::handleDiceCommand);
        commands.put("d", DiceGameService::handleDiceCommand); 
        commands.put("crash", CrashService::handleCrashCommand);
        commands.put("case", CaseOpeningService::handleCaseCommand);
        commands.put("avatar", AvatarsService::handleAvatarsCommand);
        commands.put("btc", BitcoinService::handleBitcoinCommand);
        
    }

    public static void processCommand(String userName, String message) {
        CommandContext context = parseCommand(message, userName);
        Consumer<CommandContext> commandHandler = commands.get(context.getCommand().toLowerCase());
        
        if (commandHandler != null) {
            commandHandler.accept(context);
        } else {
            MessageService.sendMessage("Unknown command: %s", context.getCommand());
            Logger.logInfo("%s used unknown command: %s", "CommandController.processCommand()", userName, context.getCommand());
        }
    }

    private static CommandContext parseCommand(String message, String userName) {
        String commandAndArgs;
            if (message.startsWith(botCommand) && message.length() > botCommand.length()) {
                commandAndArgs = message.substring(botCommand.length()).trim();
            } else if (message.startsWith(botAlternativeCommand) && message.length() > botAlternativeCommand.length()){
                commandAndArgs = message.substring(botAlternativeCommand.length()).trim();
            } else {
                commandAndArgs = "";
                Logger.logInfo("%s used empty command", "CommandController.processCommand()", userName);
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
