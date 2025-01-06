package controller;

import utils.LoggerUtil;
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
        LoggerUtil.logInfo("Starting login process...");
   

        driver.get("https://www.messenger.com/?locale=en_US");

        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

        // Accept cookies and perform the login
        acceptFirstCookies(wait);

        performLogin(wait);

        try{
            WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath("//*[contains(text(), '"+groupChatName+"')]")));
            element.click();
        } catch(Exception e){
            System.out.println(e);
        }

}

    private static void acceptFirstCookies(WebDriverWait wait) {
        try {
            WebElement cookiesButton = wait.until(ExpectedConditions.elementToBeClickable(By.id(firstCookiesButtonId)));
            cookiesButton.click();
            LoggerUtil.logInfo("First cookies accepted.");
        } catch (Exception e) {
            LoggerUtil.logWarning("First cookies button not found or not clickable.");
        }
    }

    private static void performLogin(WebDriverWait wait) {
        try {
            
            WebElement usernameField = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id(loginInputId)));
            usernameField.sendKeys(username);
            WebElement passwordField = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id(passwordInputId)));
            passwordField.sendKeys(password);
            WebElement loginButton = wait.until(ExpectedConditions.elementToBeClickable(By.id(loginButtonId)));
            LoggerUtil.logInfo("Waiting 10 seconds in login page to ommit the captcha");
            Thread.sleep(20000);
            loginButton.click();
            LoggerUtil.logInfo("Login submitted with username: %s", username);

        } catch (Exception e) {
            LoggerUtil.logError("Error while performing login", e);
        }
    }

}