package database;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.io.File;

public class DatabaseConnectionManager {

    private static final String databasePath = "src" + File.separator + "database" + File.separator + "mydatabase.db";
    private static final String DATABASE_URL = "jdbc:sqlite:" + databasePath;

    private DatabaseConnectionManager() {
    }

    public static Connection getConnection() throws SQLException {
        return DriverManager.getConnection(DATABASE_URL);
    }

}
