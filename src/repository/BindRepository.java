package repository;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

import database.DatabaseConnectionManager;
import utils.Logger;

public class BindRepository {

    public static String getCommand(String username, int bindId) {
        String sql = "SELECT command FROM binds WHERE username = ? AND bind_id = ?";

        try (Connection conn = DatabaseConnectionManager.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, username);
            stmt.setInt(2, bindId);

            ResultSet rs = stmt.executeQuery();
            if (rs.next()) {
                return rs.getString("command");
            }

        } catch (SQLException e) {
            Logger.logError("BindRepository Error for user: " + username, "BindRepository.getCommand()", e);
        }

        return null;
    }

    public static boolean saveBind(String username, int bindId, String command) {
        String sql = "INSERT OR REPLACE INTO binds (username, bind_id, command) VALUES (?, ?, ?)";

        try (Connection conn = DatabaseConnectionManager.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, username);
            stmt.setInt(2, bindId);
            stmt.setString(3, command);

            stmt.executeUpdate();
            return true;

        } catch (SQLException e) {
            Logger.logError("BindRepository Error for user: " + username, "BindRepository.saveBind()", e);
        }

        return false;
    }

    public static List<String> getUserBinds(String username) {
        String sql = "SELECT bind_id, command FROM binds WHERE username = ? ORDER BY bind_id ASC";
        List<String> binds = new ArrayList<>();

        try (Connection conn = DatabaseConnectionManager.getConnection();
            PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, username);
            ResultSet rs = stmt.executeQuery();

            while (rs.next()) {
                int bindId = rs.getInt("bind_id");
                String command = rs.getString("command");
                binds.add("[" + bindId + "] " + command);
            }

        } catch (SQLException e) {
            Logger.logError("BindRepository Error for user: " + username, "BindRepository.getUserBinds()", e);
        }

        return binds;
    }

}