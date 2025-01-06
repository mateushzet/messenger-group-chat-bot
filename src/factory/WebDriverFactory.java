package factory;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;

import utils.ConfigReader;

public class WebDriverFactory {

    private static WebDriver driver;

    public static WebDriver initializeDriver() {
        String driverPath = System.getenv("CHROMEDRIVER_PATH");
        if (driverPath == null || driverPath.isEmpty()) {
            driverPath = ConfigReader.getWebDriverPath();
        }
        System.setProperty("webdriver.chrome.driver", driverPath);

        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless", "--no-sandbox", "--disable-dev-shm-usage");

        driver = new ChromeDriver(options);
        return driver;
    }

    public static WebDriver getDriver() {
        if (driver == null) {
            driver = initializeDriver();
        }
        return driver;
    }    

    public static void quitDriver() {
        if (driver != null) {
            driver.quit();
            driver = null;
        }
    }

}