package service;

import repository.UserRepository;

import java.awt.Toolkit;
import java.awt.datatransfer.Clipboard;
import java.awt.datatransfer.StringSelection;
import java.time.Duration;
import java.util.List;

import utils.ConfigReader;
import utils.LoggerUtil;

import org.openqa.selenium.By;
import org.openqa.selenium.Keys;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import app.App;
import factory.WebDriverFactory;
import model.CommandContext;

public class CommandService {
    
    private static WebDriver driver = WebDriverFactory.getDriver();
    private static String messageInputBoxCssSelector = ConfigReader.getMessageInputBoxCssSelector();

    public static void handleMoneyCommand(CommandContext context) {
        String userName = context.getUserName();
        int balance = UserRepository.getUserBalance(userName, true);
        MessageService.sendMessage("%s, current balance: %d", userName ,balance);
        LoggerUtil.logInfo("%s, current balance: %d",userName, balance);
    }

    public static void handleTimeCommand(CommandContext context) {
        MessageService.sendMessage("Current time: " + java.time.LocalTime.now());
    }

    public static void handleKillCommand(CommandContext context) {
        MessageService.sendMessage("Shutting down the bot");
        LoggerUtil.logInfo("Shutting down the bot at the request of %s", context.getUserName());
        System.exit(0);
    }

    public static void handleStopCommand(CommandContext context) {
        MessageService.sendMessage("Status: stopped");
        App.running = 0;
    }

    public static void handleStartCommand(CommandContext context) {
        MessageService.sendMessage("Status: running");
        App.running = 1;
    }

    public static void handleStatusCommand(CommandContext context) {
        String status = (App.running == 1) ? "running" : "stopped";
        MessageService.sendMessage("Status: %s", status);
    }

    public static void handleSayCommand(CommandContext context) {
        String text = String.join(" ", context.getArguments());
        MessageService.sendMessage(text);
    }
    
    public static void handleAnswerCommand(CommandContext context) {
        String answer = context.getFirstArgument();
        MathQuestionService.handleMathAnswer(answer, context.getUserName());
    }

public static void handleTransferCommand(CommandContext context) {
    String amount = context.getFirstArgument();
    List<String> receiverNameParts = context.getArguments().subList(1, context.getArguments().size());
    String receiverFullName = String.join(" ", receiverNameParts);
    String senderName = context.getUserName();

    boolean correctTransfer = UserRepository.handleTransfer(senderName, amount, receiverNameParts.toArray(new String[0]));

    if (correctTransfer) {
        MessageService.sendMessage("Transferred %s coins to %s", amount, receiverFullName);
    } else {
        MessageService.sendMessage("Transfer failed");
        LoggerUtil.logWarning("Transfer failed sender: %s, amount: %s, receiver: %s", senderName, amount, receiverFullName);
    }
}

    public static void handleRankCommand(CommandContext context) {
        String rankingString = UserRepository.getRanking();
        copyToClipboard(rankingString);
        pasteAndSend(context);
    }

    public static void handleHelpCommand(CommandContext context) {

        String[] helpMessages = {
            "Command list:",
            "> money - Shows your current balance.",
            "> roulette - /bot roulette <bet> <number or color (red, black, green)>",
            "> say - /bot say <text>",
            "> answer - /bot answer <number>",
            "> transfer - /bot transfer <amount> <first name> <last name>",
            "> rank - Shows the balance ranking",
            "> stop - Stops the bot",
            "> start - Starts the bot",
            "> kill - Completely shuts down the bot",
            "> help - Displays this list of available commands"
        };

        String helpMessageString = String.join("\n", helpMessages);
        copyToClipboard(helpMessageString);
        pasteAndSend(context);
    }

    private static void copyToClipboard(String text) {
        StringSelection stringSelection = new StringSelection(text);
        Clipboard clipboard = Toolkit.getDefaultToolkit().getSystemClipboard();
        clipboard.setContents(stringSelection, null);
    }

    private static void pasteAndSend(CommandContext context) {

        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        WebElement inputBox = wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector(messageInputBoxCssSelector)));

        inputBox.sendKeys(Keys.CONTROL + "v");
        inputBox.sendKeys(Keys.ENTER);
    }

}
