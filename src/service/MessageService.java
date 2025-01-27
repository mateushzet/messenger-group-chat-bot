package service;

import controller.CommandController;
import factory.WebDriverFactory;
import utils.ConfigReader;
import utils.Logger;

import java.time.Duration;
import java.time.LocalTime;
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
    private static int counter = 0;
    private static int lasthourAPIfetch = 0;

    private static LocalTime lastHour = java.time.LocalTime.now();

    public static boolean validateMessage(WebElement message) {
        
        // Check if message has profile picture
        List<WebElement> userImages = message.findElements(By.cssSelector(messageUserAvatarCssSelector));
        if (userImages.isEmpty()) {
            // No profile picture, message from bot, skip
            return false;
        }

        String text = message.getText();

        //dont check heart reaction for answer commands
        //if (text.startsWith(botCommand.toLowerCase()+" answer") && !Logger.doesLogExist(getSenderName(message) + text + LocalDateTime.now().withMinute(0).withSecond(0).withNano(0))) {
        //    Logger.logToDatabase("INFO",getSenderName(message) + text + LocalDateTime.now().withMinute(0).withSecond(0).withNano(0),"validateMessage");
        //    return true;
        //}

        // check if message starts with /bot
        if (!text.startsWith(botCommand.toLowerCase()) && !text.startsWith(botAlternativeCommand.toLowerCase())) {
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
        Logger.logInfo("Message sent: %s", "MessageService.sendMessage()", formattedMessage);
    }

    public static void sendMessageFromClipboard(boolean instant) {
        String messageInputBoxCssSelector = ConfigReader.getMessageInputBoxCssSelector();
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        WebElement inputBox = wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector(messageInputBoxCssSelector)));
    
        inputBox.click();
    


        Actions actions = new Actions(driver);
        actions.keyDown(Keys.CONTROL)
        .sendKeys("v")
        .keyUp(Keys.CONTROL)
        .perform();

        counter++;

        if(instant == true){
            try {
                Thread.sleep(100);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            actions.sendKeys(Keys.RETURN).perform();
            lastHour = java.time.LocalTime.now();
            counter = 0;
        } else if(counter==5) {
            actions.sendKeys(Keys.RETURN).perform();
            lastHour = java.time.LocalTime.now();
            counter = 0;
        }
    
        Logger.logToConsole("INFO", "Message sent from clipboard.", "MessageService.sendMessage()");
    }

    public static void processMessages() throws InterruptedException {
        while (true) {
            try {
                
                LocalTime currenttime = java.time.LocalTime.now();
                int currentHour = currenttime.getHour();
                int currentMinute = currenttime.getMinute();

                if((Duration.between(lastHour, currenttime).getSeconds() > 10) && counter != 0) {
                    Actions actions = new Actions(driver);
                    actions.sendKeys(Keys.RETURN).perform();
                    lastHour = java.time.LocalTime.now();
                    counter = 0;
                }

                if((currentHour >= 12 && currentHour <= 24) && currentMinute == 0 && lasthourAPIfetch != currentHour){
                    try {
                        lasthourAPIfetch = currentHour;
                        SportsApiToDatabase.fetchAndStoreMatchData();
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }

                MathQuestionService.checkAndSendMathQuestion();
                
                List<WebElement> messages = driver.findElements(By.cssSelector(messageCssSelector));
                
                for (WebElement message : messages) {
                    if (validateMessage(message)) {
                        String userName;

                        try{
                            userName = getSenderName(message).toLowerCase();
                        }catch(Exception e){
                            continue;
                        }
                        if(!userName.isEmpty()){

                            String text = message.getText().toLowerCase();
                            if (text.startsWith(botCommand.toLowerCase()) || text.startsWith(botAlternativeCommand.toLowerCase())) {
                                CommandController.processCommand(userName, text);
                            }
                    }  //else Get sender name error or two messages from the same sender in a row
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
       
            //if (name == null || name.trim().isEmpty()) {
            //  Sender name is null or empty in message
            //} else {
            //  Checked message sender name
            //}
        } catch (Exception e) {
            Logger.logError("Failed to get sender name", "MessageService.getSenderName()", e);
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
            Logger.logError("clickEmoji: Thread.sleep failure", "MessageService.clickEmoji()", e);
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
                Logger.logInfo("Added heart reaction to message: %s", "MessageService.addEmoji()", message.getText());
            } catch (Exception e) {
                Logger.logError("Failed to add heart reaction to message: %s", "MessageService.addEmoji()", e, message.getText());
            }

            hasEmoji = hasEmoji(message);
        }
    }
}
