package games.caseopening;

import java.sql.*;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

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

    public static List<String> getSkinsFilesNames(int minPrice, int maxPrice) {

        if (maxPrice < minPrice) {
            Logger.logWarning("Invalid price range: maxPrice < minPrice", "SkinPriceRepository.getSkinsFilesNames()");
            return Collections.emptyList();
        }

        String query = "SELECT skin_name FROM skin_prices WHERE price >= ? AND price <= ?";
        List<String> skinsList = new ArrayList<>();

        try (Connection connection = DatabaseConnectionManager.getConnection();
            PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setInt(1, minPrice);
            statement.setInt(2, maxPrice);

            try (ResultSet resultSet = statement.executeQuery()) {
                while (resultSet.next()) {
                    String skinName = resultSet.getString("skin_name") + ".png";
                    skinsList.add(skinName);
                }
            }

        } catch (SQLException e) {
            Logger.logError("Error while fetching skin names", "SkinPriceRepository.getSkinsNames()", e);
        }

        return skinsList;
    }
}