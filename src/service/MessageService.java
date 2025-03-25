package service;

import controller.CommandController;
import factory.WebDriverFactory;
import games.jackpot.JackpotService;
import model.UserCooldownInfo;
import repository.UserRepository;
import utils.ConfigReader;
import utils.Logger;

import java.time.Duration;
import java.time.LocalTime;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;

import org.openqa.selenium.By;
import org.openqa.selenium.Keys;
import org.openqa.selenium.StaleElementReferenceException;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.interactions.Actions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

public class MessageService {

    private static final WebDriver driver = WebDriverFactory.getDriver();
    private static final String botCommand = ConfigReader.getBotCommand();
    private static final String botAlternativeCommand = ConfigReader.getBotAlternativeCommand();
    private static final String messageUserAvatarCssSelector = ConfigReader.getMessageUserAvatarCssSelector();
    private static final String messageCssSelector = ConfigReader.getMessageCssSelector();
    private static final String emojiButtonCssSelector = ConfigReader.getEmojiButtonCssSelector();
    private static final String searchEmojiInputCssSelector = ConfigReader.getSearchEmojiInputCssSelector();
    private static final String clearSearchEmojiButtonCssSelector = ConfigReader.getClearSearchEmojiButtonCssSelector();
    private static final String messageReceivedReactionsCssSelector = ConfigReader.getMessageReceivedReactionsCssSelector();
    private static final String messageReceivedReactionsHeartCssSelector = ConfigReader.getMessageReceivedReactionsHeartCssSelector();
    private static final String messageHeartReactionCssSelector = ConfigReader.getMessageHeartReactionCssSelector();
    private static final String messageReactButtonCssSelector = ConfigReader.getMessageReactButtonCssSelector();
    
    private static final boolean optimizedModeEnabled = ConfigReader.isOptimizedModeEnabled();
    private static final int MAX_MESSAGES_BEFORE_COOLDOWN = 5;
    private static final int CLIPBOARD_MESSAGE_THRESHOLD = 5;
    private static final int MAX_CLIPBOARD_IDLE_SECONDS = 10;
    
    private static int counter = 0;
    private static int lastHourAPIfetch = 0;
    private static LocalTime lastHour = LocalTime.now();

    public static void sendMessage(String message) {
        String messageInputBoxCssSelector = ConfigReader.getMessageInputBoxCssSelector();
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        WebElement inputBox = wait.until(ExpectedConditions.visibilityOfElementLocated(
            By.cssSelector(messageInputBoxCssSelector)));
        
        inputBox.sendKeys(message);
        inputBox.sendKeys(Keys.RETURN);
        Logger.logInfo("Message sent: " + message, "MessageService.sendMessage()");
    }

    public static void sendMessageFromClipboard(boolean instant) {
        String messageInputBoxCssSelector = ConfigReader.getMessageInputBoxCssSelector();
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        WebElement inputBox = wait.until(ExpectedConditions.visibilityOfElementLocated(
            By.cssSelector(messageInputBoxCssSelector)));
        
        inputBox.click();
        
        Actions actions = new Actions(driver);
        actions.keyDown(Keys.CONTROL)
               .sendKeys("v")
               .keyUp(Keys.CONTROL)
               .perform();

        if(instant || optimizedModeEnabled) {
            actions.sendKeys(Keys.RETURN).perform();
            lastHour = LocalTime.now();
            counter = 0;
        } else if(++counter == CLIPBOARD_MESSAGE_THRESHOLD) {
            actions.sendKeys(Keys.RETURN).perform();
            lastHour = LocalTime.now();
            counter = 0;
        }
        
        Logger.logToConsole("INFO", "Message sent from clipboard.", "MessageService.sendMessage()");
    }

    public static void processMessages() throws InterruptedException {
        Logger.logInfo(("Starting message processing in " + (optimizedModeEnabled ? "OPTIMIZED" : "NORMAL") + " mode"),"MessageService.processMessages()");
        
        if (optimizedModeEnabled) {
            processMessagesInOptimizedMode();
        } else {
            processMessagesInNormalMode();
        }
    }

    private static void processMessagesInOptimizedMode() {
        while (true) {
            try {
                processCommonTasks();
                processAllValidMessages();
            } catch (StaleElementReferenceException e) {
                continue;
            }
        }
    }

    private static void processMessagesInNormalMode() {
        ConcurrentHashMap<String, UserCooldownInfo> userCooldownMap = new ConcurrentHashMap<>();
        
        while (true) {
            try {
                LocalTime currentTime = LocalTime.now();
                
                handleClipboardTimeout(currentTime);
                handleScheduledTasks(currentTime);
                processCommonTasks();
                
                List<WebElement> messages = driver.findElements(By.cssSelector(messageCssSelector));
                for (WebElement message : messages) {
                    if (!isValidMessage(message)) {
                        continue;
                    }
                    
                    String userName = getSenderName(message);
                    if (userName == null || userName.isEmpty()) {
                        continue;
                    }
                    
                    UserCooldownInfo userInfo = userCooldownMap.computeIfAbsent(
                        userName.toLowerCase(), 
                        k -> new UserCooldownInfo());
                    
                    if (handleUserCooldown(userName, userInfo, currentTime)) {
                        continue;
                    }
                    
                    processUserCommand(userName, message.getText().toLowerCase());
                }
            } catch (StaleElementReferenceException e) {
                continue;
            }
        }
    }

    private static void processCommonTasks() {
        if (JackpotService.hasTenMinutesPassedSinceOldestTimestamp()) {
            CompletableFuture.runAsync(JackpotService::startJackpotGame);
        }
        CompletableFuture.runAsync(MathQuestionService::checkAndSendMathQuestion);
    }

    private static void processAllValidMessages() {
        List<WebElement> messages = driver.findElements(By.cssSelector(messageCssSelector));
        for (WebElement message : messages) {
            if (!isValidMessage(message)) {
                continue;
            }
            
            String userName = getSenderName(message);
            if (userName == null || userName.isEmpty()) {
                continue;
            }
            
            processUserCommand(userName, message.getText().toLowerCase());
        }
    }

    private static void handleClipboardTimeout(LocalTime currentTime) {
        if (Duration.between(lastHour, currentTime).getSeconds() > MAX_CLIPBOARD_IDLE_SECONDS && counter != 0) {
            new Actions(driver).sendKeys(Keys.RETURN).perform();
            lastHour = currentTime;
            counter = 0;
        }
    }

    private static void handleScheduledTasks(LocalTime currentTime) {
        int currentHour = currentTime.getHour();
        int currentMinute = currentTime.getMinute();
        
        if ((currentHour >= 12 && currentHour <= 24) && currentMinute == 0 && lastHourAPIfetch != currentHour) {
            lastHourAPIfetch = currentHour;
            CompletableFuture.runAsync(() -> {
                try {
                    SportsApiToDatabase.fetchAndStoreMatchData();
                } catch (Exception e) {
                    Logger.logError("Failed to fetch sports data", "MessageService.processMessages", e);
                }
            });
        }
    }

    private static boolean isValidMessage(WebElement message) {

        String text = message.getText().toLowerCase();
        if (!text.startsWith(botCommand.toLowerCase()) && !text.startsWith(botAlternativeCommand.toLowerCase())) {
            return false;
        }

        if (hasEmoji(message)) {
            return false;
        }

        try {
            if (message.findElements(By.cssSelector(messageUserAvatarCssSelector)).isEmpty()) {
                return false;
            }
        } catch (StaleElementReferenceException e) {
            return false;
        }

        addEmoji(message);
        return true;
    }

    private static boolean handleUserCooldown(String userName, UserCooldownInfo userInfo, LocalTime currentTime) {
        long elapsedSeconds = Duration.between(userInfo.getLastMessageTime(), currentTime).getSeconds();
        if (elapsedSeconds > userInfo.getCooldownDuration()) {
            userInfo.reset();
            return false;
        }
        
        userInfo.incrementMessageCount();
        userInfo.setLastMessageTime(currentTime);
        
        if (userInfo.getMessageCount() > MAX_MESSAGES_BEFORE_COOLDOWN) {
            long elapsedTime = Duration.between(userInfo.getLastMessageTime(), currentTime).getSeconds();
            userInfo.increaseCooldownDuration(elapsedTime);
            sendMessage(userName + " cooldown: " + userInfo.getCooldownDuration() + " s");
            return true;
        }
        return false;
    }

    private static void processUserCommand(String userName, String messageText) {
        CommandController.processCommand(userName, messageText);
    }

    private static String getSenderName(WebElement message) {
        String name = null;
        String avatarUrl = null;
        try {
            WebElement avatarElement = message.findElement(By.cssSelector(messageUserAvatarCssSelector));
    
            name = avatarElement.getAttribute("alt");
    
            avatarUrl = avatarElement.getAttribute("src");
    
            if (name != null && !name.trim().isEmpty() && avatarUrl != null && !avatarUrl.trim().isEmpty()) {
                UserRepository.saveAvatarToDatabase(name.toLowerCase(), avatarUrl);
            } else {
                Logger.logWarning("Name or avatar URL is null or empty", "MessageService.getSenderName()");
            }
        } catch (Exception e) {
            Logger.logError("Failed to get sender name or avatar URL", "MessageService.getSenderName()", e);
        }
        return name;
    }

    public static void clickEmoji(String emojiUrl, String emojiName) {
   
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        WebElement emojiButton = wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector(emojiButtonCssSelector)));

        emojiButton.click();
        
        try {
         Thread.sleep(500);
        } catch (InterruptedException e) {
            Logger.logError("clickEmoji: Thread.sleep failure", "MessageService.clickEmoji()", e);
    }

    WebElement inputField = driver.findElement(By.cssSelector(searchEmojiInputCssSelector));
    inputField.sendKeys(emojiName);
    
    WebElement imgElement = wait.until(ExpectedConditions.presenceOfElementLocated(
        By.cssSelector("img[src='" + emojiUrl + "']")));

    imgElement.click();
    WebElement clearSearchButton = driver.findElement(By.cssSelector(clearSearchEmojiButtonCssSelector));
    clearSearchButton.click();
    emojiButton.click();
    }

    public static boolean hasEmoji(WebElement message) {
        List<WebElement> reactions = message.findElements(By.cssSelector(messageReceivedReactionsCssSelector));
    
        if (reactions.isEmpty()) {
            reactions = message.findElements(By.cssSelector(messageReceivedReactionsHeartCssSelector));
        }
    
        return !reactions.isEmpty();
    }

    public static void addEmoji(WebElement message) {

        boolean hasEmoji = false;

        while (!hasEmoji) {
            try {

                Actions actions = new Actions(driver);
                actions.moveToElement(message).perform();
                
                WebElement reactButton = message.findElement(By.cssSelector(messageReactButtonCssSelector));
                reactButton.click();
                
                WebElement heartEmoticon = driver.findElement(By.cssSelector(messageHeartReactionCssSelector));
                heartEmoticon.click();
                Logger.logInfo("Added heart reaction to message: " +  message.getText(), "MessageService.addEmoji()");
            } catch (Exception e) {
                Logger.logError("Failed to add heart reaction to message: " +  message.getText(), "MessageService.addEmoji()", e);
            }

            hasEmoji = hasEmoji(message);
        }
    }

}
