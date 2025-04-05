package factory;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.firefox.FirefoxDriver;
import org.openqa.selenium.firefox.FirefoxOptions;

import utils.ConfigReader;

public class WebDriverFactory {

    private static WebDriver driver;

    public static WebDriver initializeDriver() {
        String browserType = System.getenv("BROWSER_TYPE");
        if (browserType == null || browserType.isEmpty()) {
            browserType = ConfigReader.getBrowserType(); // Możesz ustawić w konfiguracji preferowaną przeglądarkę
        }

        if (browserType.equalsIgnoreCase("chrome")) {
            return initializeChromeDriver();
        } else if (browserType.equalsIgnoreCase("firefox")) {
            return initializeFirefoxDriver();
        } else {
            throw new IllegalArgumentException("Unsupported browser type: " + browserType);
        }
    }

    private static WebDriver initializeChromeDriver() {
        String driverPath = System.getenv("CHROMEDRIVER_PATH");
        if (driverPath == null || driverPath.isEmpty()) {
            driverPath = ConfigReader.getWebDriverPath();
        }
        System.setProperty("webdriver.chrome.driver", driverPath);

        ChromeOptions options = new ChromeOptions();
        options.addArguments("--no-sandbox", "--disable-dev-shm-usage");
        if (!ConfigReader.getEnableGui()) options.addArguments("--headless");

        return new ChromeDriver(options);
    }

    private static WebDriver initializeFirefoxDriver() {
        String driverPath = System.getenv("GECKODRIVER_PATH");
        if (driverPath == null || driverPath.isEmpty()) {
            driverPath = ConfigReader.getWebDriverPath();
        }
        System.setProperty("webdriver.gecko.driver", driverPath);

        FirefoxOptions options = new FirefoxOptions();
        options.addArguments("--no-sandbox", "--disable-dev-shm-usage");
        if (!ConfigReader.getEnableGui()) options.addArguments("--headless");

        return new FirefoxDriver(options);
    }

    public static WebDriver getDriver() {
        if (driver == null) {
            driver = initializeDriver();
        }
        return driver;
    }

    public static void reinitializeDriver() {
        quitDriver();
        driver = initializeDriver();
    }

    public static void quitDriver() {
        if (driver != null) {
            driver.quit();
            driver = null;
        }
    }
}
