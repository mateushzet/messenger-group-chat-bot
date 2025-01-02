package utils;

import java.io.File;
import java.io.IOException;
import java.util.logging.ConsoleHandler;
import java.util.logging.FileHandler;
import java.util.logging.Logger;
import java.util.logging.Level;
import java.util.logging.SimpleFormatter;

public class LoggerUtil {

    private static final Logger logger = Logger.getLogger(LoggerUtil.class.getName());

    static {
        try {
            if (logger.getHandlers().length == 0) {
                ConsoleHandler consoleHandler = new ConsoleHandler();
                consoleHandler.setLevel(Level.ALL);
                consoleHandler.setFormatter(new SimpleFormatter());
                logger.addHandler(consoleHandler);
            }

            String logPath = System.getenv("LOG_PATH");
            if (logPath == null || logPath.isEmpty()) {
                logPath = "logs/application.log";
            }

            File logDirectory = new File("logs");
            if (!logDirectory.exists() && !logDirectory.mkdirs()) {
                throw new IOException("Failed to create logs directory.");
            }

            File logFile = new File(logPath);
            if (!logFile.exists() && !logFile.createNewFile()) {
                throw new IOException("Failed to create log file.");
            }

            FileHandler fileHandler = new FileHandler(logPath, true);
            fileHandler.setLevel(Level.ALL);
            fileHandler.setFormatter(new SimpleFormatter());
            logger.addHandler(fileHandler);

            logger.setLevel(Level.ALL);
        } catch (IOException e) {
            System.err.println("Error occurred while setting up the logger: " + e.getMessage());
        }
    }
    
    public static void logInfo(String message, Object... params) {
        try {
            logger.info(String.format(message, params));
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Logger failed to parse the log message: " + message, e);
        }
    }

    public static void logWarning(String message, Object... params) {
        try {
            logger.warning(String.format(message, params));
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Logger failed to parse the log message: " + message, e);
        }
    }

    public static void logError(String message, Exception e, Object... params) {
        try {
            logger.log(Level.SEVERE, String.format(message, params), e);
        } catch (Exception e2) {
            logger.log(Level.SEVERE, "Logger failed to parse the log message:" + message + " exception: " + e, e2);
        }
    }
}
