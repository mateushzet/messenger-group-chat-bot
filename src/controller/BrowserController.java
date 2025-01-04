package controller;

import utils.LoggerUtil;
import utils.ConfigReader;

import java.time.Duration;
import java.util.List;

import org.openqa.selenium.By;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.interactions.Actions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
//import org.openqa.selenium.interactions.Actions;

import factory.WebDriverFactory;

public class BrowserController {
    
    private static WebDriver driver = WebDriverFactory.getDriver();
    private static String firstCookiesButtonId = ConfigReader.getFirstCookiesButtonId();
    private static String username = ConfigReader.getUsername();
    private static String password = ConfigReader.getPassword();
    private static String loginInputId = ConfigReader.getLoginInputId();
    private static String passwordInputId = ConfigReader.getPasswordInputId();
    private static String loginButtonId = ConfigReader.getLoginButtonId();
    //private static String secondCookiesButtonXpath = ConfigReader.getSecondCookiesButtonXpath();
    //private static String continueLoginButtonCssSelector = ConfigReader.getContinueLoginButtonCssSelector();

    public static void loginToMessenger() {
        LoggerUtil.logInfo("Starting login process...");
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

        driver.get("https://www.messenger.com");

        

        // Accept cookies and perform the login
        acceptFirstCookies(wait);
        performLogin(wait);



          try {

            // Znajdź wszystkie elementy typu button
            List<WebElement> buttons = driver.findElements(By.tagName("button"));

            // Wypisz szczegóły każdego przycisku
            System.out.println("Liczba znalezionych przycisków: " + buttons.size());
            for (int i = 0; i < buttons.size(); i++) {
                WebElement button = buttons.get(i);
                System.out.println("Przycisk " + (i + 1) + ":");
                System.out.println("Tekst: " + button.getText());
                System.out.println("ID: " + button.getAttribute("id"));
                System.out.println("Klasy: " + button.getAttribute("class"));
                System.out.println("HTML: " + button.getAttribute("outerHTML"));
                System.out.println("-------------------------");
            }

            // Dodatkowo, znajdź inne potencjalne przyciski, np. input type="submit"
            List<WebElement> inputs = driver.findElements(By.cssSelector("input[type='submit']"));
            System.out.println("Liczba znalezionych input[type='submit']: " + inputs.size());
            for (int i = 0; i < inputs.size(); i++) {
                WebElement input = inputs.get(i);
                System.out.println("Input " + (i + 1) + ":");
                System.out.println("Tekst: " + input.getAttribute("value"));
                System.out.println("ID: " + input.getAttribute("id"));
                System.out.println("Klasy: " + input.getAttribute("class"));
                System.out.println("HTML: " + input.getAttribute("outerHTML"));
                System.out.println("-------------------------");
            }

        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            // Zamknij przeglądarkę
            driver.quit();
        }
 



      //   Handle potential re-authentication scenarios
      //  acceptSecondCookies(wait);


        System.out.println("first screenshot");

        String screenshotBase64 = ((TakesScreenshot) driver).getScreenshotAs(OutputType.BASE64);
        System.out.println(screenshotBase64);

       // LoggerUtil.logInfo("Waiting for captcha resolution or further login prompts");
       // handleContinueAs(wait);

       System.out.println("seconf screenshot");

        try {
            Thread.sleep(3000);
        } catch (InterruptedException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }


        
        screenshotBase64 = ((TakesScreenshot) driver).getScreenshotAs(OutputType.BASE64);
        System.out.println(screenshotBase64);

 // WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath("//*[contains(text(), 'SundayCasino')]")));
    //    element.click();



    }

    //WebElement allowCookiesButton = driver.findElement(By.xpath("//span[text()='Allow all cookies']"));
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
            Thread.sleep(10000);
            loginButton.click();
            LoggerUtil.logInfo("Login submitted with username: %s", username);

        } catch (Exception e) {
            LoggerUtil.logError("Error while performing login", e);
        }
    }

    private static void acceptSecondCookies(WebDriverWait wait) {
        try {
            WebElement cookiesButton = driver.findElement(By.xpath(ConfigReader.getSecondCookiesButtonXpath()));
            new Actions(driver).moveToElement(cookiesButton).click().perform();

            LoggerUtil.logInfo("Second cookies accepted.");
        } catch (Exception e) {
            LoggerUtil.logWarning("Second cookies button not found or not clickable.");
        }
    }

  // private static void handleContinueAs(WebDriverWait wait) {
   //     try {
     //       WebElement continueAsButton = wait.until(ExpectedConditions.visibilityOfElementLocated(
       //     By.cssSelector(continueLoginButtonCssSelector)
         //   ));
         //   continueAsButton.click();
           // LoggerUtil.logInfo("Clicked 'Continue as' button.");
      //  } catch (Exception e) {
        //    LoggerUtil.logWarning("No 'Continue as' button found.");
            // In case no 'Continue as' button appears, we attempt to log in again
          //  performLogin(wait);
       // }
 //   }

}