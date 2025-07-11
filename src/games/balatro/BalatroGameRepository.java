package games.balatro;

import java.sql.*;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import database.DatabaseConnectionManager;
import utils.Logger;

public class BalatroGameRepository {

    public static void saveGame(BalatroGame game) {
        String query = "INSERT INTO balatro_game (user_name, bet_amount, player_hand, discard_pile, deck, game_in_progress, game_status, selected_joker_id, available_jokers, draw_pile, kept_pile, hand_values) " +
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";

        try (Connection connection = DatabaseConnectionManager.getConnection();
            PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, game.getUserName());
            statement.setInt(2, game.getBetAmount());
            statement.setString(3, convertListToString(game.getPlayerHand()));
            statement.setString(4, convertListToString(game.getDiscardPile()));
            statement.setString(5, convertListToString(game.getDeck()));
            statement.setBoolean(6, game.isGameInProgress());
            statement.setInt(7, game.getGameStatus());
            statement.setInt(8, game.getSelectedJokerId());
            statement.setString(9, convertIntListToString(game.getAvailableJokers()));
            statement.setString(10, convertListToString(game.getDrawPile()));
            statement.setString(11, convertListToString(game.getKeptPile()));
            statement.setString(12, convertListToString(game.getHandValues()));

            statement.executeUpdate();
        } catch (Exception e) {
            Logger.logError("Error while saving game", "BalatroGameRepository.saveGame()", e);
        }
    }

    public static BalatroGame getGameByUserName(String userName) {
        String query = "SELECT * FROM balatro_game WHERE user_name = ? AND game_in_progress = 1";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName);
            ResultSet resultSet = statement.executeQuery();

            if (resultSet.next()) {
                List<String> playerHand = convertStringToList(resultSet.getString("player_hand"));
                List<String> discardPile = convertStringToList(resultSet.getString("discard_pile"));
                List<String> deck = convertStringToList(resultSet.getString("deck"));
                List<Integer> availableJokers = convertStringToIntList(resultSet.getString("available_jokers"));
                List<String> keptPile = convertStringToList(resultSet.getString("kept_pile"));
                List<String> drawPile = convertStringToList(resultSet.getString("draw_pile"));
                List<String> handValues = convertStringToList(resultSet.getString("hand_values"));

                BalatroGame game = new BalatroGame(
                        resultSet.getString("user_name"),
                        resultSet.getInt("bet_amount"),
                        playerHand,
                        discardPile,
                        resultSet.getBoolean("game_in_progress"),
                        resultSet.getInt("selected_joker_id"),
                        keptPile,
                        drawPile,
                        handValues
                );

                game.setGameStatus(resultSet.getInt("game_status"));
                game.setAvailableJokers(availableJokers);
                game.setDeck(deck);

                return game;
            }
        } catch (SQLException e) {
            Logger.logError("Error while fetching game by username", "BalatroGameRepository.getGameByUserName()", e);
        }
        return null;
    }

    public static void updateGame(BalatroGame game) {
        String query = "UPDATE balatro_game SET bet_amount = ?, player_hand = ?, discard_pile = ?, game_in_progress = ?, game_status = ?, selected_joker_id = ?, available_jokers = ? , deck = ?, " +
                       "draw_pile = ?, kept_pile = ?, hand_values = ? WHERE user_name = ? AND game_in_progress = 1";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setInt(1, game.getBetAmount());
            statement.setString(2, convertListToString(game.getPlayerHand()));
            statement.setString(3, convertListToString(game.getDiscardPile()));
            statement.setBoolean(4, game.isGameInProgress());
            statement.setInt(5, game.getGameStatus());
            statement.setInt(6, game.getSelectedJokerId());
            statement.setString(7, convertIntListToString(game.getAvailableJokers()));
            statement.setString(8, convertListToString(game.getDeck()));
            statement.setString(9, convertListToString(game.getDrawPile()));
            statement.setString(10, convertListToString(game.getKeptPile()));
            statement.setString(11, convertListToString(game.getHandValues()));
            statement.setString(12, game.getUserName());

            statement.executeUpdate();

        } catch (SQLException e) {
            Logger.logError("Error while updating game", "BalatroGameRepository.updateGame()", e);
        }
    }

    public static void deleteGame(String userName) {
        String query = "DELETE FROM balatro_game WHERE user_name = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName);
            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while deleting game", "BalatroGameRepository.deleteGame()", e);
        }
    }

    public static String convertListToString(List<String> list) {
        if (list == null || list.isEmpty()) {
            return "";
        }
        return String.join(",", list);
    }

    private static List<String> convertStringToList(String str) {
        List<String> list = new ArrayList<>();
        if (str != null && !str.isEmpty()) {
            String[] items = str.split(",");
            Collections.addAll(list, items);
        }
        return list;
    }

    private static String convertIntListToString(List<Integer> list) {
        if (list == null || list.isEmpty()) return "";
        StringBuilder sb = new StringBuilder();
        for (Integer i : list) {
            sb.append(i).append(",");
        }
        sb.deleteCharAt(sb.length() - 1);
        return sb.toString();
    }

    private static List<Integer> convertStringToIntList(String str) {
        List<Integer> list = new ArrayList<>();
        if (str != null && !str.isEmpty()) {
            String[] parts = str.split(",");
            for (String p : parts) {
                try {
                    list.add(Integer.parseInt(p));
                } catch (NumberFormatException ignored) {}
            }
        }
        return list;
    }
}