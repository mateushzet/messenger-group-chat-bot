package controller;

import model.CommandContext;
import repository.UserRepository;
import service.MessageService;
import service.SkinsService;
import service.StatisticsService;
import service.UserService;
import utils.ConfigReader;
import utils.Logger;
import service.AskCommandService;
import service.AvatarsService;
import service.BitcoinService;
import service.CommandService;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

import games.Poker.PokerService;
import games.balatro.BalatroGameController;
import games.blackjack.BlackjackService;
import games.caseopening.CaseOpeningService;
import games.coinflip.CoinflipService;
import games.colors.ColorsService;
import games.crash.CrashService;
import games.dice.DiceGameService;
import games.horseRace.HorseRaceBettingService;
import games.jackpot.JackpotService;
import games.lotto.LottoService;
import games.match.MatchController;
import games.mines.MinesService;
import games.moneytree.MoneyTreeService;
import games.plinko.PlinkoService;
import games.roulette.RouletteService;
import games.slots.SlotsService;

public class CommandController {
    
    private static final Map<String, Consumer<CommandContext>> commands = new HashMap<>();
    private static final String botCommand = ConfigReader.getBotCommand();
    private static final String botAlternativeCommand = ConfigReader.getBotAlternativeCommand();
    private static final boolean requireGameAccess = ConfigReader.isGameAccessRequired();

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
        commands.put("buy", UserService::handleBuyCommand);
        commands.put("jackpot", JackpotService::handleJackpotCommand);
        commands.put("tree", MoneyTreeService::handleTreeCommand);
        commands.put("ask", AskCommandService::handleAskCommand);
        commands.put("weekly", CommandService::handleWeeklyCommand); 
        commands.put("poker", PokerService::handlePokerCommand); 
        commands.put("pk", PokerService::handlePokerCommand); 
        commands.put("gift", CommandService::handleGiftCommand);
        commands.put("bind", CommandService::handleBindCommand);
        commands.put("1", CommandService::handleBindCommand);
        commands.put("2", CommandService::handleBindCommand);
        commands.put("3", CommandService::handleBindCommand);
        commands.put("4", CommandService::handleBindCommand);
        commands.put("5", CommandService::handleBindCommand);
        commands.put("6", CommandService::handleBindCommand);
        commands.put("7", CommandService::handleBindCommand);
        commands.put("8", CommandService::handleBindCommand);
        commands.put("9", CommandService::handleBindCommand);
        commands.put("0", CommandService::handleBindCommand);
        commands.put("admin", CommandService::handleAdminCommand);
        commands.put("balatro", BalatroGameController::handleBalatroCommand);
        commands.put("bal", BalatroGameController::handleBalatroCommand);
        commands.put("b", BalatroGameController::handleBalatroCommand);
    }

    public static void processCommand(String userName, String message) {
        CommandContext context = parseCommand(message, userName);
        Consumer<CommandContext> commandHandler = commands.get(context.getCommand().toLowerCase());
    
        if (commandHandler != null) {
            if (requiresGameAccess(context.getCommand()) && requireGameAccess) {
                String gameName = getGameNameFromCommand(context.getCommand());
                if (!UserRepository.hasGameAccess(userName, gameName)) {
                    MessageService.sendMessage(userName + ", you do not have access to " + gameName + ". /buy " + gameName + " (50 coins)");
                    return;
                }
            }
    
            commandHandler.accept(context);
        } else {
            MessageService.sendMessage("Unknown command: " + context.getCommand());
            Logger.logInfo(userName + " used unknown command: " +  context.getCommand(), "CommandController.processCommand()");
        }
    }

    public static void processCommand(CommandContext context) {
        String userName = context.getUserName();
        Consumer<CommandContext> commandHandler = commands.get(context.getCommand().toLowerCase());
    
        if (commandHandler != null) {
            if (requiresGameAccess(context.getCommand()) && requireGameAccess) {
                String gameName = getGameNameFromCommand(context.getCommand());
                if (!UserRepository.hasGameAccess(userName, gameName)) {
                    MessageService.sendMessage(userName + ", you do not have access to " + gameName + ". /buy " + gameName + " (50 coins)");
                    return;
                }
            }
    
            commandHandler.accept(context);
        } else {
            MessageService.sendMessage("Unknown command: " + context.getCommand());
            Logger.logInfo(userName + " used unknown command: " +  context.getCommand(), "CommandController.processCommand()");
        }
    }

    private static boolean requiresGameAccess(String command) {
        List<String> gameCommands = List.of("slots", "s", "roulette", "r", "blackjack", "bj", "plinko", "p", "dice", "d", "crash", "case", "c", "colors", "m", "mines", "l", "lotto", "race");
        return gameCommands.contains(command);
    }
    
    private static String getGameNameFromCommand(String command) {
        Map<String, String> commandToGameMap = Map.ofEntries(
            Map.entry("slots", "slots"),
            Map.entry("s", "slots"),
            Map.entry("roulette", "roulette"),
            Map.entry("r", "roulette"),
            Map.entry("blackjack", "blackjack"),
            Map.entry("bj", "blackjack"),
            Map.entry("plinko", "plinko"),
            Map.entry("p", "plinko"),
            Map.entry("dice", "dice"),
            Map.entry("d", "dice"),
            Map.entry("crash", "crash"),
            Map.entry("case", "case"),
            Map.entry("c", "colors"),
            Map.entry("colors", "colors"),
            Map.entry("m", "mines"),
            Map.entry("mines", "mines"),
            Map.entry("l", "lotto"),
            Map.entry("lotto", "lotto"),
            Map.entry("race", "race")
        );
        return commandToGameMap.getOrDefault(command, command);
    }

    public static CommandContext parseCommand(String message, String userName) {
        String commandAndArgs;
            if (message.startsWith(botCommand) && message.length() > botCommand.length()) {
                commandAndArgs = message.substring(botCommand.length()).trim();
            } else if (message.startsWith(botAlternativeCommand) && message.length() > botAlternativeCommand.length()){
                commandAndArgs = message.substring(botAlternativeCommand.length()).trim();
            } else {
                commandAndArgs = "";
                Logger.logInfo(userName + " used empty command", "CommandController.processCommand()");
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

}
