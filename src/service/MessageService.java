package service;

import controller.CommandController;
import factory.WebDriverFactory;
import utils.ConfigReader;
import utils.LoggerUtil;

import java.time.Duration;
import java.util.List;

import org.openqa.selenium.By;
import org.openqa.selenium.Keys;
import org.openqa.selenium.StaleElementReferenceException;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.interactions.Actions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

public class MessageService {

    private static WebDriver driver = WebDriverFactory.getDriver();
    private static final String botCommand = ConfigReader.getBotCommand();
    private static final String messageUserAvatarCssSelector = ConfigReader.getMessageUserAvatarCssSelector();
    private static final String messageCssSelector = ConfigReader.getMessageCssSelector();
    private static final String emojiButtonCssSelector = ConfigReader.getEmojiButtonCssSelector();
    private static final String searchEmojiInputCssSelector = ConfigReader.getSearchEmojiInputCssSelector();
    private static final String clearSearchEmojiButtonCssSelector = ConfigReader.getClearSearchEmojiButtonCssSelector();
    private static final String messageReceivedReactionsCssSelector = ConfigReader.getMessageReceivedReactionsCssSelector();
    private static final String messageReceivedReactionsHeartCssSelector = ConfigReader.getMessageReceivedReactionsHeartCssSelector();
    private static final String messageHeartReactionCssSelector = ConfigReader.getMessageHeartReactionCssSelector();
    private static final String messageReactButtonCssSelector = ConfigReader.getMessageReactButtonCssSelector();
    


    public static boolean validateMessage(WebElement message) {
        // Check if message has profile picture
        List<WebElement> userImages = message.findElements(By.cssSelector(messageUserAvatarCssSelector));
        if (userImages.isEmpty()) {
            // No profile picture, message from bot, skip
            return false;
        }
    
        String text = message.getText();
    
        // check if message starts with /bot
        if (!text.startsWith(botCommand.toLowerCase())) {
            return false;
        }
    
        // Check if message has reactions (emojis)
        if (hasEmoji(message)) {
            // There is already a reaction, message already processed, skip
            return false;
        }
    
        // Add heart emoji if not already reacted
        addEmoji(message);
    
        return true;
    }
    
    public static void sendMessage(String message, Object... params) {
        String messageInputBoxCssSelector = ConfigReader.getMessageInputBoxCssSelector();
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        WebElement inputBox = wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector(messageInputBoxCssSelector)));

        String formattedMessage = String.format(message, params);
        inputBox.sendKeys(formattedMessage);
        inputBox.sendKeys(Keys.RETURN);
        LoggerUtil.logInfo("Message sent: %s", formattedMessage);
    }

    public static void processMessages() throws InterruptedException {
        while (true) {
            try {
                
                MathQuestionService.checkAndSendMathQuestion();
                
                List<WebElement> messages = driver.findElements(By.cssSelector(messageCssSelector));
                
                for (WebElement message : messages) {
                    if (validateMessage(message)) {
                        String userName = getSenderName(message).toLowerCase();
                        if(!userName.isEmpty()){

                        String text = message.getText().toLowerCase();
                        if (text.startsWith(botCommand.toLowerCase())) {
                            CommandController.processCommand(userName, text);
                        }
                    } else LoggerUtil.logWarning("Get sender name error or two messages from the same sender in a row");
                    }
                 }
            } catch (StaleElementReferenceException e) {
                //The element has been changed in the DOM. Ignoring the exception.
            }
        }
    }

    private static String getSenderName(WebElement message) {
        String name = null;
        try {
            name = message.findElement(By.cssSelector(messageUserAvatarCssSelector)).getAttribute("alt");
       
            if (name == null || name.trim().isEmpty()) {
                LoggerUtil.logWarning("Sender name is null or empty in message: %s", message);
            } else {
                LoggerUtil.logInfo("Checked message sender name: %s", name);
            }
        } catch (Exception e) {
            LoggerUtil.logError("Failed to get sender name", e);
        }
        return name;
    }

    public static void clickEmoji(String emojiUrl, String emojiName) {
   
        // click on emoji selection icon
         WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        WebElement emojiButton = wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector(emojiButtonCssSelector)));

        emojiButton.click();
        
        try {
         Thread.sleep(500);
        } catch (InterruptedException e) {
            LoggerUtil.logError("clickEmoji: Thread.sleep failure", e);
    }

    // find emoji search input and type emoji name, than click on the emoji based on src url
    WebElement inputField = driver.findElement(By.cssSelector(searchEmojiInputCssSelector));
    inputField.sendKeys(emojiName);
    
    WebElement imgElement = wait.until(ExpectedConditions.presenceOfElementLocated(
        By.cssSelector("img[src='" + emojiUrl + "']")));

    // click on emoji, clean search bar and leave emoji selector
    imgElement.click();
    WebElement clearSearchButton = driver.findElement(By.cssSelector(clearSearchEmojiButtonCssSelector));
    clearSearchButton.click();
    emojiButton.click();
    }

    public static boolean hasEmoji(WebElement message) {
        // Check if the message has any reaction (emoji)
        List<WebElement> reactions = message.findElements(By.cssSelector(messageReceivedReactionsCssSelector));
    
        // If there are no reactions found, try to check for a a heart reaction
        if (reactions.isEmpty()) {
            reactions = message.findElements(By.cssSelector(messageReceivedReactionsHeartCssSelector));
        }
    
        return !reactions.isEmpty(); // Return true if there is at least one reaction, false otherwise
    }

    public static void addEmoji(WebElement message) {
        // Hover the message to make the reaction button appear

        boolean hasEmoji = false;

        while (!hasEmoji) {
            try {

                Actions actions = new Actions(driver);
                actions.moveToElement(message).perform();
                
                // Try to find and click the react button
                WebElement reactButton = message.findElement(By.cssSelector(messageReactButtonCssSelector));
                reactButton.click();
                
                // Find the heart emoji and click it
                WebElement heartEmoticon = driver.findElement(By.cssSelector(messageHeartReactionCssSelector));
                heartEmoticon.click();
                LoggerUtil.logInfo("Added heart reaction to message: %s", message.getText());
            } catch (Exception e) {
                LoggerUtil.logError("Failed to add heart reaction to message: %s", e, message.getText());
            }

            hasEmoji = hasEmoji(message);
        }

    }

}
