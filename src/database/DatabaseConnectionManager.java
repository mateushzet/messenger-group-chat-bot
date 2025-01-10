package database;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.io.File;

public class DatabaseConnectionManager {

    private static Connection connection;

    private static String databasePath = "src" + File.separator + "database" + File.separator + "mydatabase.db";
    private static final String DATABASE_URL = "jdbc:sqlite:" + databasePath;
    
    private DatabaseConnectionManager() {
    }

    public static Connection getConnection() throws SQLException {
        if (connection == null || connection.isClosed()) {
            connection = DriverManager.getConnection(DATABASE_URL);
        }
        return connection;
    } 
        
}
