package utils;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

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

    public static void logInfo(String message, String source) {
        log("INFO", message, source);
    }

    public static void logWarning(String message, String source) {
        log("WARNING", message, source);
    }

    public static void logError(String message, String source, Exception e) {
        log("ERROR", message, source);
    }

    public static boolean doesLogExist(String message) {

        String sql = "SELECT COUNT(*) FROM logs WHERE message = ? AND timestamp > ?";
        try (Connection conn = DatabaseConnectionManager.getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {
            
            pstmt.setString(1, message);
            
            String currentTime = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm"));
            pstmt.setString(2, currentTime);
            
            try (java.sql.ResultSet rs = pstmt.executeQuery()) {
                if (rs.next()) {
                    return rs.getInt(1) > 0;
                }
            }
        } catch (SQLException e) {
            logError("Encountered Error while checking log existence: " + e.getMessage(), "doesLogExist()", e);
        }
        return false;
    }
}