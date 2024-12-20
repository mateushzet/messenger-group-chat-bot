package factory;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;

public class WebDriverFactory {

    private static WebDriver driver;

    public static WebDriver getDriver() {
        if (driver == null) {
            initializeDriver();
        }
        return driver;
    }

    private static void initializeDriver() {
        // Ustawienie ścieżki do ChromeDriver (kontener Docker ma go w /usr/local/bin/)
        System.setProperty("webdriver.chrome.driver", "/usr/local/bin/chromedriver");

        // Tworzenie instancji ChromeOptions i dodanie argumentów
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--disable-notifications");  // Wyłączenie powiadomień
        options.addArguments("--headless");  // Uruchomienie w trybie headless (bez interfejsu graficznego)
        options.addArguments("--no-sandbox");  // Ważne w środowiskach kontenerowych
        options.addArguments("--disable-gpu");  // Wyłączenie GPU (opcjonalne, ale może pomóc w kontenerach)
        
        // Tworzenie instancji ChromeDriver z ustawionymi opcjami
        driver = new ChromeDriver(options);
    }

    public static void quitDriver() {
        if (driver != null) {
            driver.quit();
            driver = null;
        }
    }
}
