package utils;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import database.DatabaseConnectionManager;

public class Logger {
    private static final boolean SAVE_LOGS_TO_DB = ConfigReader.isSavingLogstodatabaseenabled();
    private static final DateTimeFormatter TIMESTAMP_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSS");
    private static final String LOG_FORMAT = "LOG: %s%n  Log message: %s%n  Source: %s%n  Level: %s%n";
    private static final String INSERT_LOG_SQL = "INSERT INTO logs(timestamp, level, message, source) VALUES(?, ?, ?, ?)";

    public static void logToDatabase(String level, String message, String source) {
        if (!SAVE_LOGS_TO_DB) {
            return;
        }

        try (Connection conn = DatabaseConnectionManager.getConnection();
             PreparedStatement pstmt = conn.prepareStatement(INSERT_LOG_SQL)) {
            
            pstmt.setString(1, LocalDateTime.now().format(TIMESTAMP_FORMATTER));
            pstmt.setString(2, level);
            pstmt.setString(3, message);
            pstmt.setString(4, source);
            pstmt.executeUpdate();
        } catch (SQLException e) {
            System.err.println("Error while logging to database: " + e.getMessage());
        }
    }

    public static void logToConsole(String level, String message, String source) {
        System.out.printf(LOG_FORMAT,
            LocalDateTime.now().format(TIMESTAMP_FORMATTER),
            message,
            source,
            level
        );
    }

    public static void log(String level, String message, String source) {
        if (SAVE_LOGS_TO_DB) {
            logToDatabase(level, message, source);
        }
        logToConsole(level, message, source);
    }

    public static void logInfo(String message, String source) {
        log("INFO", message, source);
    }

    public static void logWarning(String message, String source) {
        log("WARNING", message, source);
    }

    public static void logError(String message, String source, Exception e) {
        String errorMessage = message + " - Exception: " + e.getMessage();
        log("ERROR", errorMessage, source);
        e.printStackTrace();
    }
}