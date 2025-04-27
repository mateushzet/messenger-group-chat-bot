package service;

import controller.CommandController;
import factory.WebDriverFactory;
import games.jackpot.JackpotService;
import model.UserCooldownInfo;
import utils.ConfigReader;
import utils.Logger;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.time.Duration;
import java.time.LocalTime;
import java.util.Base64;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.Keys;
import org.openqa.selenium.StaleElementReferenceException;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.interactions.Actions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

public class MessageService {

    private static final WebDriver driver = WebDriverFactory.getDriver();

    private static final String messageHeartReactionCssSelector = ConfigReader.getMessageHeartReactionCssSelector();
    private static final String messageReactButtonCssSelector = ConfigReader.getMessageReactButtonCssSelector();
    private static final String messageCssSelector = ConfigReader.getMessageCssSelector();
    private static final String botCommand = ConfigReader.getBotCommand();
    private static final String botAlternativeCommand = ConfigReader.getBotAlternativeCommand();
    private static final boolean optimizedModeEnabled = ConfigReader.isOptimizedModeEnabled();
    private static final String operatingSystem = getOperatingSystem();

    private static final int MAX_MESSAGES_BEFORE_COOLDOWN = 5;
    private static final int CLIPBOARD_MESSAGE_THRESHOLD = 5;
    private static final int MAX_CLIPBOARD_IDLE_SECONDS = 10;

    private static int counter = 0;
    private static int lastHourAPIfetch = 0;
    private static LocalTime lastHour = LocalTime.now();

    public static void sendMessage(String message) {
        String inputCss = ConfigReader.getMessageInputBoxCssSelector();
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        WebElement inputBox = wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector(inputCss)));

        inputBox.click();
        Actions actions = new Actions(driver);
        for (char c : message.toCharArray()) {
            actions.sendKeys(Character.toString(c)).pause(Duration.ofMillis(20));
        }
        actions.sendKeys(Keys.RETURN).perform();

        Logger.logInfo("Message sent: " + message, "MessageService.sendMessage()");
    }

    public static void sendMessageFromClipboard(boolean instant) {
        if(operatingSystem.equals("Linux")){
            sendMessageFromClipboardLinux(instant);
        } else {
            sendMessageFromClipboardWindows(instant);
        }
    }

    public static void sendMessageFromClipboardLinux(boolean instant) {
        String inputCss = ConfigReader.getMessageInputBoxCssSelector();
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        WebElement inputBox = wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector(inputCss)));

        inputBox.click();
        Actions actions = new Actions(driver);
        actions.keyDown(Keys.CONTROL).sendKeys("v").keyUp(Keys.CONTROL).perform();
        inputBox.click();

        if (instant || optimizedModeEnabled) {
            resetCounterAndTime();
            sleep(200);
            actions.sendKeys(Keys.RETURN).perform();
        } else if (++counter == CLIPBOARD_MESSAGE_THRESHOLD) {
            actions.sendKeys(Keys.RETURN).perform();
            resetCounterAndTime();
        }

        Logger.logToConsole("INFO", "Message sent from clipboard.", "MessageService.sendMessageFromClipboard()");
    }

    public static void sendMessageFromClipboardWindows(boolean instant) {
        if (operatingSystem.equals("Linux")) {
            return; // Skipping, because GIF sending is handled differently on Linux
        } 
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

            try {
                Thread.sleep(200);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }

            actions.sendKeys(Keys.RETURN).perform();

        } else if(++counter == CLIPBOARD_MESSAGE_THRESHOLD) {
            actions.sendKeys(Keys.RETURN).perform();
            lastHour = LocalTime.now();
            counter = 0;
        }
        
        Logger.logToConsole("INFO", "Message sent from clipboard.", "MessageService.sendMessage()");
    }

    public static void simulateGifDrop(byte[] gifBytes) {
        try {
            File tempFile = File.createTempFile("temp_gif_", ".gif");
            Files.write(tempFile.toPath(), gifBytes);

            String base64Gif = Base64.getEncoder().encodeToString(gifBytes);
            WebElement dropTarget = driver.findElement(By.cssSelector(ConfigReader.getMessageInputBoxCssSelector()));

            String js = """
                const dropZone = arguments[0];
                const fileName = arguments[1];
                const fileMime = arguments[2];
                const fileContentBase64 = arguments[3];

                const byteCharacters = atob(fileContentBase64);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], { type: fileMime });
                const file = new File([blob], fileName, { type: fileMime });

                const dt = new DataTransfer();
                dt.items.add(file);

                const event = new DragEvent('drop', {
                    dataTransfer: dt,
                    bubbles: true,
                    cancelable: true
                });

                dropZone.dispatchEvent(event);
            """;

            ((JavascriptExecutor) driver).executeScript(js, dropTarget, "animated.gif", "image/gif", base64Gif);

            Logger.logInfo("GIF dropped into message input.", "simulateGifDrop()");
            sleep(1000);
            new Actions(driver).sendKeys(Keys.RETURN).perform();
        } catch (IOException | NoSuchElementException e) {
            Logger.logError("Error during GIF drop", "simulateGifDrop()", e);
        }
    }

    public static void processMessages() throws InterruptedException {
        Logger.logInfo("Starting message processing in " + (optimizedModeEnabled ? "OPTIMIZED" : "NORMAL") + " mode", "MessageService.processMessages()");

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
            } catch (StaleElementReferenceException ignored) {
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

                List<WebElement> messages = driver.findElements(By.cssSelector(messageCssSelector)).stream()
                        .filter(el -> {
                            String text = el.getText().toLowerCase();
                            return text.contains(botCommand.toLowerCase()) || text.contains(botAlternativeCommand.toLowerCase());
                        })
                        .collect(Collectors.toList());

                for (WebElement message : messages) {
                    if (!isValidMessage("message")) continue;

                    String userName = findSenderName(message);
                    if (userName == null || userName.isEmpty()) continue;

                    UserCooldownInfo userInfo = userCooldownMap.computeIfAbsent(userName.toLowerCase(), k -> new UserCooldownInfo());

                    if (handleUserCooldown(userName, userInfo, currentTime)) continue;

                    processUserCommand(userName, message.getText().toLowerCase());
                }
            } catch (Exception ignored) {
            }
        }
    }

    private static void processCommonTasks() {
        if (JackpotService.hasTenMinutesPassedSinceOldestTimestamp()) {
            JackpotService.startJackpotGame();
        }
        MathQuestionService.checkAndSendMathQuestion();
    }

    private static void processAllValidMessages() {
        List<WebElement> messages = driver.findElements(By.cssSelector("div[role='row'] div[role='gridcell'] div[dir='auto']"));

        for (WebElement message : messages) {
            try {
                String text = message.getText().trim().toLowerCase();
                if (text.isEmpty()) continue;

                String sender = findSenderName(message);
                if (sender == null || sender.isEmpty()) continue;

                if (isValidMessage(text)) {
                    addEmoji(message);
                }

                boolean success = false;
                int attempts = 0;
                while (!success && attempts < 10) {
                    try {
                        clickMoreButton(message);
                        clickRemoveMessageOption();
                        confirmRemovalInModal(message);
                        success = true;
                    } catch (Exception e) {
                        attempts++;
                    }
                }

                if (isValidMessage(text) && success) {
                    processUserCommand(sender, text);
                }

                ((JavascriptExecutor) driver).executeScript("window.scrollTo(0, document.body.scrollHeight);");
                Logger.logInfo("Scrolled to bottom after processing.", "MessageService.processAllValidMessages()");
            } catch (Exception ignored) {
            }
        }
    }

    private static void handleClipboardTimeout(LocalTime currentTime) {
        if (Duration.between(lastHour, currentTime).getSeconds() > MAX_CLIPBOARD_IDLE_SECONDS && counter != 0) {
            new Actions(driver).sendKeys(Keys.RETURN).perform();
            resetCounterAndTime();
        }
    }

    private static void handleScheduledTasks(LocalTime currentTime) {
        int currentHour = currentTime.getHour();
        int currentMinute = currentTime.getMinute();

        if (currentHour >= 12 && currentMinute == 0 && lastHourAPIfetch != currentHour) {
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

    private static boolean isValidMessage(String text) {
        try {
            return text.startsWith(botCommand.toLowerCase()) || text.startsWith(botAlternativeCommand.toLowerCase());
        } catch (Exception e) {
            return false;
        }
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
            userInfo.increaseCooldownDuration(elapsedSeconds);
            sendMessage(userName + " cooldown: " + userInfo.getCooldownDuration() + " s");
            return true;
        }
        return false;
    }

    private static void processUserCommand(String userName, String messageText) {
        CommandController.processCommand(userName.toLowerCase(), messageText.toLowerCase());
    }

    private static String findSenderName(WebElement messageElement) {
        try {
            List<WebElement> containers = messageElement.findElements(By.xpath(
                    "./ancestor::div[contains(@class, 'x78zum5') and contains(@class, 'xdj266r') and contains(@class, 'x11i5rnm') and contains(@class, 'xat24cr') and contains(@class, 'x1mh8g0r') and contains(@class, 'xexx8yu') and contains(@class, 'x4uap5') and contains(@class, 'x18d9i69') and contains(@class, 'xkhd6sd') and contains(@class, 'x1eb86dx')]"));

            for (WebElement container : containers) {
                List<WebElement> images = container.findElements(By.cssSelector("img[alt]"));
                for (WebElement img : images) {
                    String alt = img.getAttribute("alt");
                    if (alt != null && !alt.trim().isEmpty()) {
                        return alt.trim();
                    }
                }
            }
            return null;
        } catch (Exception e) {
            return null;
        }
    }

    public static void clickMoreButton(WebElement messageDiv) throws Exception {
        WebElement row = getRowForMessage(messageDiv);
        if (row == null) return;

        JavascriptExecutor js = (JavascriptExecutor) driver;
        Actions actions = new Actions(driver);

        js.executeScript("arguments[0].scrollIntoView(true);", row);
        actions.moveToElement(row).perform();
        sleep(400);

        WebElement more = row.findElement(By.cssSelector("div[aria-label='More']"));
        more.click();
    }

    public static void clickRemoveMessageOption() throws Exception {
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(3));
        WebElement remove = wait.until(ExpectedConditions.elementToBeClickable(By.cssSelector("div[aria-label='Remove message']")));
        remove.click();
    }

    public static void confirmRemovalInModal(WebElement messageBeforeRemoval) throws Exception {
        String messageText = messageBeforeRemoval.getText();

        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(3));
        WebElement confirm = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//span[text()='Remove']/ancestor::div[@role='button']")));

        confirm.click();
        new WebDriverWait(driver, Duration.ofSeconds(5)).until(d -> {
            try {
                return !messageBeforeRemoval.getText().equals(messageText);
            } catch (StaleElementReferenceException e) {
                return true;
            }
        });
    }

    public static boolean hasEmoji(WebElement messageDiv) {
        try {
            WebElement row = getRowForMessage(messageDiv);
            if (row == null) return false;

            List<WebElement> reactions = row.findElements(By.cssSelector("div[aria-label*='reaction']"));
            return !reactions.isEmpty();
        } catch (Exception e) {
            return false;
        }
    }

    public static WebElement getRowForMessage(WebElement messageElement) {
        WebElement current = messageElement;
        JavascriptExecutor js = (JavascriptExecutor) driver;

        while (current != null) {
            if ("row".equals(current.getAttribute("role"))) return current;

            try {
                current = (WebElement) js.executeScript("return arguments[0].parentNode;", current);
            } catch (Exception e) {
                return null;
            }
        }
        return null;
    }

    public static void addEmoji(WebElement messageDiv) {
        boolean hasEmoji = false;
        int attempts = 0;

        while (!hasEmoji && attempts <= 10) {
            try {
                WebElement row = getRowForMessage(messageDiv);
                if (row == null) return;

                Actions actions = new Actions(driver);
                actions.moveToElement(row).perform();

                WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(2));
                WebElement reactButton = wait.until(ExpectedConditions.elementToBeClickable(row.findElement(By.cssSelector(messageReactButtonCssSelector))));
                reactButton.click();

                WebElement heart = wait.until(ExpectedConditions.elementToBeClickable(driver.findElement(By.cssSelector(messageHeartReactionCssSelector))));
                heart.click();

                return;
            } catch (Exception e) {
                attempts++;
            }
        }
    }

    private static void resetCounterAndTime() {
        counter = 0;
        lastHour = LocalTime.now();
    }

    private static void sleep(int ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException ignored) {
        }
    }



    private static String getOperatingSystem() {
        final String os = System.getProperty("os.name").toLowerCase();
    
        if (os.contains("win")) {
            return "Windows";
        } else if (os.contains("nux") || os.contains("nix") || os.contains("aix")) {
            return "Linux";
        } else if (os.contains("mac")) {
            return "MacOS";
        } else {
            return "Unknown";
        }
    }
}
