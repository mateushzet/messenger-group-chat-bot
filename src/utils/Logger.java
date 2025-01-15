package utils;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.Arrays;
import java.util.stream.Collectors;

import database.DatabaseConnectionManager;

public class Logger {

    public static void logToDatabase(String level, String message, String source) {
        String sql = "INSERT INTO logs(timestamp, level, message, source) VALUES(?, ?, ?, ?)";

        try (Connection conn = DatabaseConnectionManager.getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {
            pstmt.setString(1, java.time.LocalDateTime.now().toString());
            pstmt.setString(2, level);
            pstmt.setString(3, message);
            pstmt.setString(4, source);
            pstmt.executeUpdate();
        } catch (SQLException e) {
            System.out.println("Encountered Error while logging to database: " + e.getMessage());
        }
    }

    public static void logToConsole(String level, String message, String source) {
        System.out.println(String.format(
            "LOG: %s\n" +
            "  Log message: %s\n" +
            "  Source: %s\n" +
            "  Level: %s\n",
            java.time.LocalDateTime.now().toString(),
            message,
            source,
            level
        ));
    }

    public static void log(String level, String message, String source) {
        logToDatabase(level, message, source);
        logToConsole(level, message, source);
    }

    public static void info(String message, String source) {
        log("INFO", message, source);
    }

    public static void warning(String message, String source) {
        log("WARNING", message, source);
    }

    public static void error(String message, String source) {
        log("ERROR", message, source);
    }

    public static void logInfo(String message, String source, Object... params) {
        try {
            info(String.format(message, params), source);
        } catch (Exception e) {
            error("Logger failed to format log message. Error: " + e.getMessage(), source);
        }
    }

    public static void logWarning(String message, String source, Object... params) {
        try {
            warning(String.format(message, params), source);
        } catch (Exception e) {
            error("Logger failed to format log message. Error: " + e.getMessage(), source);
        }
    }

    public static void logError(String message, String source, Exception e, Object... params) {
        try {
            String formattedMessage = String.format(message, params);
            String fullMessage = formattedMessage + " Exception: " + e.getMessage() + " Stack trace: " + Arrays.stream(e.getStackTrace())
                .map(StackTraceElement::toString)
                .collect(Collectors.joining("\n"));
            error(fullMessage, source);
        } catch (Exception e2) {
            String errorMessage = "Logger failed to format log message. Error: " + e2.getMessage() + " Stack trace: " + Arrays.stream(e2.getStackTrace())
                .map(StackTraceElement::toString)
                .collect(Collectors.joining("\n"));
            error(errorMessage, source);
        }
    }

    public static boolean doesLogExist(String message) {
        String sql = "SELECT COUNT(*) FROM logs WHERE message = ?";
        try (Connection conn = DatabaseConnectionManager.getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {
            pstmt.setString(1, message);
            try (java.sql.ResultSet rs = pstmt.executeQuery()) {
                if (rs.next()) {
                    return rs.getInt(1) > 0;
                }
            }
        } catch (SQLException e) {
            error("Encountered Error while checking log existence: " + e.getMessage(), "doesLogExist()");
        }
        return false;
    }
}