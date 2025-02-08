package games.caseopening;

import java.sql.*;
import database.DatabaseConnectionManager;
import utils.Logger;

public class SkinPriceRepository {

    public static int getSkinPrice(String skinName, String condition, String stattrakStatus) {
        String query = "SELECT price FROM skin_prices WHERE skin_name = ? AND condition = ? AND stattrak_status = ? LIMIT 1";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, skinName);
            statement.setString(2, condition);
            statement.setString(3, stattrakStatus);

            ResultSet resultSet = statement.executeQuery();

            if (resultSet.next()) {
                return resultSet.getInt("price");
            }
        } catch (SQLException e) {
            Logger.logError("Error while fetching skin price", "SkinPriceRepository.getSkinPrice()", e);
        }

        return 0;
    }
}