package app;

import utils.ConfigReader;
import utils.Logger;
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
        Logger.logToConsole("INFO", "Browser initialized and logged into Messenger", "App.initializeBrowser()");
    }

    private static void processMessages() throws Exception {
        MessageService.processMessages();
    }

    private static void shutdownBrowser() {
            try {
                WebDriverFactory.quitDriver();
                Logger.logInfo("Web browser closed", "App.shutdownBrowser()");
            } catch (Exception e) {
                Logger.logWarning("Failed to close the browser cleanly", "App.shutdownBrowser()");
            }
    }

    public static void startApp() {
        Logger.logToConsole("INFO", "App started", "App.startApp()");
        
        boolean enableManualLogin = ConfigReader.getEnableManualLogin();

        try {
            if (enableManualLogin) {
                System.out.println("Manual login is enabled. Please log in manually.");
               } else {
                   initializeBrowser();
               }
            Logger.logInfo("The application has started listening for messages and processing them.", "App.startApp()");
            processMessages();
        } catch (WebDriverException e) {
            Logger.logError("Critical error with WebDriver", "App.startApp()", e);
        } catch (Exception e) {
            Logger.logError("Unexpected error occurred", "App.startApp()", e);
        } finally {
            shutdownBrowser();
            startApp();
        }
    }

}
