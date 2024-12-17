package utils;

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
            ConsoleHandler consoleHandler = new ConsoleHandler();
            consoleHandler.setLevel(Level.ALL);
            consoleHandler.setFormatter(new SimpleFormatter());
            logger.addHandler(consoleHandler);

            FileHandler fileHandler = new FileHandler("logs/application.log", true);
            fileHandler.setLevel(Level.ALL);
            fileHandler.setFormatter(new SimpleFormatter());
            logger.addHandler(fileHandler);

            logger.setLevel(Level.ALL);
        } catch (IOException e) {
            logger.log(Level.SEVERE, "Error occurred while setting up the logger", e);
        }
    }

    public static void logInfo(String message, Object... params) {
        try{
            logger.info(String.format(message, params));
        } catch(Exception e){
            logger.log(Level.SEVERE, "Logger failed to parse the log message: " + message, e);
        }
    }

    public static void logWarning(String message, Object... params) {
        try{
        logger.warning(String.format(message, params));
        } catch(Exception e){
            logger.log(Level.SEVERE, "Logger failed to parse the log message: " + message, e);
        }
    }

    public static void logError(String message, Exception e, Object... params) {
        try{
        logger.log(Level.SEVERE, String.format(message, params), e);
        } catch(Exception e2){
            logger.log(Level.SEVERE, "Logger failed to parse the log message:" + message + " exception: " + e, e2);
        }
    }

}