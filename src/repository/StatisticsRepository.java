package repository;

import java.sql.*;
import database.DatabaseConnectionManager;
import utils.Logger;

public class StatisticsRepository {

    public static void printViewData(String viewName) {
        String query = "SELECT * FROM " + viewName;

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query);
             ResultSet resultSet = statement.executeQuery()) {

            ResultSetMetaData metaData = resultSet.getMetaData();
            int columnCount = metaData.getColumnCount();

            for (int i = 1; i <= columnCount; i++) {
                System.out.print(metaData.getColumnName(i) + "\t");
            }
            System.out.println();


            while (resultSet.next()) {
                for (int i = 1; i <= columnCount; i++) {
                    System.out.print(resultSet.getString(i) + "\t");
                }
                System.out.println();
            }

        } catch (SQLException e) {
            Logger.logError("Error retrieving data from view: %s", "ViewDataRepository.printViewData()", e, viewName);
            e.printStackTrace();
        }
    }
}