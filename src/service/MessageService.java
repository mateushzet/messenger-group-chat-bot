package service;

import controller.CommandController;
import database.DatabaseConnectionManager;
import factory.WebDriverFactory;
import games.jackpot.JackpotService;
import games.slots.JackpotRepository;
import model.UserCooldownInfo;
import repository.UserRepository;
import utils.ConfigReader;
import utils.Logger;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.Base64;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;

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
    private static LocalDate jackpotLastAdditionDate = JackpotRepository.getJackpotDailyIncraseDate();

    public static void sendMessage(String message) {

        closeIncomingCallPopupIfPresent();

        String inputCss = ConfigReader.getMessageInputBoxCssSelector();
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        WebElement inputBox = wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector(inputCss)));

        inputBox.click();
        Actions actions = new Actions(driver);
        for (char c : message.toCharArray()) {
            actions.sendKeys(Character.toString(c)).pause(Duration.ofMillis(10));
        }
        actions.sendKeys(Keys.RETURN).perform();

        Logger.logInfo("Message sent: " + message, "MessageService.sendMessage()");
    }

    public static void sendMessageFromClipboard(boolean instant) {
        closeIncomingCallPopupIfPresent();
        if(operatingSystem.equals("Linux")){
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

    public static void simulateImageDrop(BufferedImage image) {
        try {
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            ImageIO.write(image, "png", baos);
            byte[] imageBytes = baos.toByteArray();

            String base64Image = Base64.getEncoder().encodeToString(imageBytes);
            WebElement dropTarget = driver.findElement(By.cssSelector(ConfigReader.getMessageInputBoxCssSelector()));

            String js = """
                const dropZone = arguments[0];
                const fileContentBase64 = arguments[1];
                const fileName = "image.png";
                const fileMime = "image/png";

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

            ((JavascriptExecutor) driver).executeScript(js, dropTarget, base64Image);

            Logger.logInfo("Image dropped into message input.", "simulateImageDrop()");
            sleep(1000);
            new Actions(driver).sendKeys(Keys.RETURN).perform();
        } catch (IOException | NoSuchElementException e) {
            Logger.logError("Error during Image drop", "simulateImageDrop()", e);
        }
    }
    

    public static void processMessages() throws InterruptedException {
        Logger.logInfo("Starting message processing in " + (optimizedModeEnabled ? "OPTIMIZED" : "NORMAL") + " mode", "MessageService.processMessages()");

        //startIncomingCallWatcher();

        if (optimizedModeEnabled) {
            processMessagesInOptimizedMode();
        } else {
            processMessagesInNormalMode();
        }
    }

    private static void processMessagesInOptimizedMode() {
        while (true) {
            try {
                System.out.println("processCommonTasks()");
                processCommonTasks();
                //processAllValidMessages();
                processAllValidMessagesFromDB();
                System.out.println("processAllValidMessagesFromDB()");
            } catch (StaleElementReferenceException ignored) {
                System.out.println("IGNORDER" + ignored);
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
            closeIncomingCallPopupIfPresent();
            JackpotService.startJackpotGame();
        }
        MathQuestionService.checkAndSendMathQuestion();

        addToJackpotPoolOncePerDay(50);
    }



    private static void processAllValidMessagesFromDB() {
        try (Connection conn = DatabaseConnectionManager.getConnection()) {

            // Pobierz jedną wiadomość o najniższym ID
            try (PreparedStatement selectStmt = conn.prepareStatement(
                    "SELECT id, sender, message FROM commands WHERE status = 'pending' ORDER BY id ASC LIMIT 1")) {

                ResultSet rs = selectStmt.executeQuery();
                if (rs.next()) {
                    int id = rs.getInt("id");
                    String sender = rs.getString("sender");
                    String message = rs.getString("message");

                    // Oznacz jako "processing"
                    try (PreparedStatement updateToProcessing = conn.prepareStatement(
                            "UPDATE commands SET status = 'processing' WHERE id = ?")) {
                        updateToProcessing.setInt(1, id);
                        updateToProcessing.executeUpdate();
                    }


                    // Przetwórz komendę
                    Logger.logInfo("Przetwarzanie komendy: " + message, "MessageService");
                    processUserCommand(sender, message);

                    // Ustaw jako "processed"
                    try (PreparedStatement updateToProcessed = conn.prepareStatement(
                            "UPDATE commands SET status = 'processed' WHERE id = ?")) {
                        updateToProcessed.setInt(1, id);
                        updateToProcessed.executeUpdate();
                    }

                }

            } catch (SQLException e) {
                Logger.logWarning("Błąd podczas przetwarzania komendy: " + e.getMessage(), "MessageService");
            }

        } catch (SQLException e) {
            e.printStackTrace();
        }
    }


    private static void processAllValidMessages() {
        List<WebElement> messageRows = driver.findElements(By.cssSelector("div[role='row']"));
            
        for (WebElement row : messageRows) {
            try {
                WebElement messageElement = row.findElement(By.cssSelector("div[role='gridcell'] div[dir='auto']"));
                String text = messageElement.getText().trim().toLowerCase();
                if (text.isEmpty()) continue;

                String sender = findSenderName(row);
                if (sender == null || sender.isEmpty()) continue;

                if (isValidMessage(text)) {
                    closeIncomingCallPopupIfPresent();
                    addEmoji(messageElement);
                    updateUserAvatar(row);
                }

                boolean success = false;
                int attempts = 0;
                while (!success && attempts < 5) {
                    try {
                        closeIncomingCallPopupIfPresent();
                        clickMoreButton(messageElement);
                        clickRemoveMessageOption();
                        confirmRemovalInModal(messageElement);
                        success = true;
                    } catch (Exception e) {
                        attempts++;
                    }
                }

                if (isValidMessage(text) && success) {
                    processUserCommand(sender, text);
                    
                }

            } catch (Exception ignored) {
            }
        }
        ((JavascriptExecutor) driver).executeScript("window.scrollTo(0, document.body.scrollHeight);");
        Logger.logInfo("Scrolled to bottom after processing.", "MessageService.processAllValidMessages()");
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

    private static String findSenderName(WebElement messageRow) {
        String name = null;
        try {
            WebElement avatarElement = messageRow.findElement(By.cssSelector("img.x1rg5ohu"));
            name = avatarElement.getAttribute("alt");
        } catch (Exception ignored) {
            //Logger.logError("Failed to get sender name or avatar URL", "MessageService.getSenderName()", e);
        }
        return name;
    }

    private static void updateUserAvatar(WebElement messageRow) {
        String name = null;
        String avatarUrl = null;
        try {
            WebElement avatarElement = messageRow.findElement(By.cssSelector("img.x1rg5ohu"));
            avatarUrl = avatarElement.getAttribute("src");
                UserRepository.saveAvatarToDatabase(name.toLowerCase(), avatarUrl);
        } catch (Exception ignored) {
            //Logger.logError("Failed to get sender name or avatar URL", "MessageService.getSenderName()", e);
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
    
    public static void addToJackpotPoolOncePerDay(int amount) {
        LocalDate today = LocalDate.now();
        if (jackpotLastAdditionDate == null || !jackpotLastAdditionDate.equals(today)) {
            jackpotLastAdditionDate = today;
            JackpotRepository.jackpotDailyIncrease(amount);
        }
    }

    public static void closeIncomingCallPopupIfPresent() {
        try {
            WebElement closeButton = driver.findElement(By.cssSelector("div[aria-label='Close'][role='button']"));
            if (closeButton.isDisplayed()) {
                closeButton.click();
                Logger.logInfo("Incoming call popup closed.", "MessageService.closeIncomingCallPopupIfPresent()");
            }
        } catch (Exception ignored) {
        }
    }

}

