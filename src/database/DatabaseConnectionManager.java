package database;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.Statement;
import java.io.File;

public class DatabaseConnectionManager {

    private static Connection connection;

    private static final String databasePath = "src" + File.separator + "database" + File.separator + "mydatabase.db";
    private static final String DATABASE_URL = "jdbc:sqlite:" + databasePath;

    private DatabaseConnectionManager() {
    }

    public static Connection getConnection() throws SQLException {
        try {
            Thread.sleep(100);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        if (connection == null || connection.isClosed()) {
            connection = DriverManager.getConnection(DATABASE_URL);
            setupDatabase(connection);
        }
        return connection;
    }

    private static void setupDatabase(Connection conn) throws SQLException {
        try (Statement stmt = conn.createStatement()) {
            stmt.execute("PRAGMA busy_timeout = 5000;");
        }
    }
}
