package app;

import utils.ConfigReader;
import utils.LoggerUtil;
import controller.BrowserController;
import service.MessageService;

import java.io.File;

import org.openqa.selenium.*;
import factory.WebDriverFactory;

public class App {

    public static final String USERS_MONEY_FILE_PATH = "src" + File.separator + "repository" + File.separator + "users_money.txt";
    public static int running = 1;

    public static void main(String[] args) {
        startApp();
    }

    private static void initializeBrowser() throws Exception {
        BrowserController.loginToMessenger();
        LoggerUtil.logInfo("Browser initialized and logged into Messenger");
    }

    private static void processMessages() throws Exception {
        MessageService.processMessages();
    }

    private static void shutdownBrowser() {
            try {
                WebDriverFactory.quitDriver();
                LoggerUtil.logInfo("Web browser closed");
            } catch (Exception e) {
                LoggerUtil.logWarning("Failed to close the browser cleanly");
            }
    }

    public static void startApp() {
        LoggerUtil.logInfo("App started");
        
        boolean enableManualLogin = ConfigReader.getEnableManualLogin();

        try {
            if (enableManualLogin) {
                    LoggerUtil.logInfo("Manual login is enabled. Please log in manually.");
               } else {
                   initializeBrowser();
               }

            LoggerUtil.logInfo("The application has started listening for messages and processing them.");
            processMessages();
        } catch (WebDriverException e) {
            LoggerUtil.logError("Critical error with WebDriver", e);
        } catch (Exception e) {
            LoggerUtil.logError("Unexpected error occurred", e);
        } finally {
            shutdownBrowser();
            startApp();
        }
    }

}
