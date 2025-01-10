package controller;

import utils.Logger;
import utils.ConfigReader;

import java.time.Duration;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import factory.WebDriverFactory;

public class BrowserController {
    
    private static WebDriver driver = WebDriverFactory.getDriver();
    private static String firstCookiesButtonId = ConfigReader.getFirstCookiesButtonId();
    private static String username = ConfigReader.getUsername();
    private static String password = ConfigReader.getPassword();
    private static String loginInputId = ConfigReader.getLoginInputId();
    private static String passwordInputId = ConfigReader.getPasswordInputId();
    private static String loginButtonId = ConfigReader.getLoginButtonId();
    private static String groupChatName = ConfigReader.getGroupChatName();

    public static void loginToMessenger() {
        Logger.logToConsole("INFO", "Starting login process", "BrowserController.loginToMessenger()");
        
        driver.get("https://www.messenger.com/?locale=en_US");

        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

        // Accept cookies and perform the login
        acceptFirstCookies(wait);

        performLogin(wait);

        try{
            WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath("//*[contains(text(), '"+groupChatName+"')]")));
            element.click();
        } catch(Exception e){
            Logger.logError( "Failed to open the group chat", "BrowserController.loginToMessenger()", e);
            System.out.println(e);
        }

}

    private static void acceptFirstCookies(WebDriverWait wait) {
        try {
            WebElement cookiesButton = wait.until(ExpectedConditions.elementToBeClickable(By.id(firstCookiesButtonId)));
            cookiesButton.click();
            Logger.logToConsole("INFO", "First cookies accepted", "BrowserController.acceptFirstCookies()");
        } catch (Exception e) {
            Logger.logError( "First cookies button not found or not clickable", "BrowserController.acceptFirstCookies()", e);
        }
    }

    private static void performLogin(WebDriverWait wait) {
        try {
            
            WebElement usernameField = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id(loginInputId)));
            usernameField.sendKeys(username);
            WebElement passwordField = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id(passwordInputId)));
            passwordField.sendKeys(password);
            WebElement loginButton = wait.until(ExpectedConditions.elementToBeClickable(By.id(loginButtonId)));
            Logger.logToConsole("INFO", "Waiting 10 seconds in login page to ommit the captcha", "BrowserController.performLogin()");
            Thread.sleep(20000);
            loginButton.click();
            Logger.logToConsole("INFO", "Login submitted with username: " + username, "BrowserController.performLogin()");

        } catch (Exception e) {
            Logger.logError("Error while performing login", "BrowserController.performLogin()", e);
        }
    }

}