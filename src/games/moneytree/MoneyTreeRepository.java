package games.moneytree;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

import database.DatabaseConnectionManager;
import utils.Logger;

public class MoneyTreeRepository {

    public static void saveGame(String userName, int investedCoins, List<Integer> phaseDurations, int witherPhase, int witherTime) {
        String query = "INSERT INTO money_tree_game (user_name, invested_coins, phase_durations, wither_phase, wither_time, start_time, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName);
            statement.setInt(2, investedCoins);
            statement.setString(3, convertListToString(phaseDurations));
            statement.setInt(4, witherPhase);
            statement.setInt(5, witherTime);
            statement.setLong(6, System.currentTimeMillis() / 1000);
            statement.setBoolean(7, true);

            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while saving game", "MoneyTreeRepository.saveGame()", e);
        }
    }

    public static MoneyTreeGame getGameByUserName(String userName) {
        String query = "SELECT * FROM money_tree_game WHERE user_name = ? LIMIT 1";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName);
            ResultSet resultSet = statement.executeQuery();

            if (resultSet.next()) {
                List<Integer> phaseDurations = convertStringToList(resultSet.getString("phase_durations"));
                return new MoneyTreeGame(
                        resultSet.getString("user_name"),
                        resultSet.getInt("invested_coins"),
                        resultSet.getLong("start_time"),
                        phaseDurations,
                        resultSet.getInt("wither_phase"),
                        resultSet.getInt("wither_time"),
                        resultSet.getBoolean("is_active")
                );
            }
        } catch (SQLException e) {
            Logger.logError("Error while fetching game by username", "MoneyTreeRepository.getGameByUserName()", e);
        }
        return null;
    }

    public static void updateGame(MoneyTreeGame game) {
        String query = "UPDATE money_tree_game SET invested_coins = ?, phase_durations = ?, wither_phase = ?, wither_time = ?, is_active = ? WHERE user_name = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setInt(1, game.getInvestedCoins());
            statement.setString(2, convertListToString(game.getPhaseDurations()));
            statement.setInt(3, game.getWitherPhase());
            statement.setInt(4, game.getWitherTime());
            statement.setBoolean(5, game.isActive());
            statement.setString(6, game.getUserName());

            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while updating game", "MoneyTreeRepository.updateGame()", e);
        }
    }

    public static void endGame(String userName) {
        String query = "UPDATE money_tree_game SET is_active = false WHERE user_name = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName);
            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while ending game", "MoneyTreeRepository.endGame()", e);
        }
    }

    public static void deleteGame(String userName) {
        String query = "DELETE FROM money_tree_game WHERE user_name = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName);
            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while deleting game", "MoneyTreeRepository.deleteGame()", e);
        }
    }

    // Pomocnicza metoda do konwersji listy na string
    private static String convertListToString(List<Integer> list) {
        StringBuilder sb = new StringBuilder();
        for (Integer value : list) {
            sb.append(value).append(",");
        }
        return sb.length() > 0 ? sb.substring(0, sb.length() - 1) : "";
    }

    // Pomocnicza metoda do konwersji string na listę
    private static List<Integer> convertStringToList(String str) {
        List<Integer> list = new ArrayList<>();
        if (str != null && !str.isEmpty()) {
            String[] parts = str.split(",");
            for (String part : parts) {
                list.add(Integer.parseInt(part));
            }
        }
        return list;
    }
}