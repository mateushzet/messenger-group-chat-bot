package repository;

import java.sql.*;
import model.DiceGame;
import utils.Logger;
import database.DatabaseConnectionManager;

public class DiceGameRepository {

    public static void saveGame(DiceGame game) {
        String query = "INSERT INTO dice_game (user_name, balance, current_bet, dice_rolls, game_in_progress) VALUES (?, ?, ?, ?, ?)";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, game.getUserName());
            statement.setInt(2, game.getUserBalance());
            statement.setInt(3, game.getBetAmount());
            statement.setString(4, convertRollsToString(game.getDiceValues()));
            statement.setBoolean(5, game.isGameInProgress());

            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while saving game", "DiceGameRepository.saveGame()", e);
        }
    }

    public static DiceGame getGameByUserName(String userName) {
        String query = "SELECT * FROM dice_game WHERE user_name = ? AND game_in_progress = 1";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName);
            ResultSet resultSet = statement.executeQuery();

            if (resultSet.next()) {
                int[] rolls = convertRollsFromString(resultSet.getString("dice_rolls"));
                DiceGame game = new DiceGame(
                        resultSet.getString("user_name"),
                        resultSet.getInt("current_bet"),
                        rolls,
                        resultSet.getBoolean("game_in_progress"),
                        resultSet.getInt("balance")
                );
                return game;
            }
        } catch (SQLException e) {
            Logger.logError("Error while fetching game by username", "DiceGameRepository.getGameByUserName()", e);
        }
        return null;
    }

    public static void updateGame(DiceGame game) {
        String query = "UPDATE dice_game SET balance = ?, current_bet = ?, dice_rolls = ?, game_in_progress = ? WHERE user_name = ? AND game_in_progress = 1";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setInt(1, game.getUserBalance());
            statement.setInt(2, game.getBetAmount());
            statement.setString(3, convertRollsToString(game.getDiceValues()));
            statement.setBoolean(4, game.isGameInProgress());
            statement.setString(5, game.getUserName());

            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while updating game", "DiceGameRepository.updateGame()", e);
        }
    }

    public static void deleteGame(String userName) {
        String query = "DELETE FROM dice_game WHERE user_name = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName);
            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while deleting game", "DiceGameRepository.deleteGame()", e);
        }
    }

    private static String convertRollsToString(int[] rolls) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < rolls.length; i++) {
            sb.append(rolls[i]);
            if (i < rolls.length - 1) {
                sb.append(",");
            }
        }
        return sb.toString();
    }

    private static int[] convertRollsFromString(String rollsString) {
        if (rollsString != null && !rollsString.isEmpty()) {
            String[] rollsArray = rollsString.split(",");
            int[] rolls = new int[rollsArray.length];

            for (int i = 0; i < rollsArray.length; i++) {
                rolls[i] = Integer.parseInt(rollsArray[i].trim());
            }

            return rolls;
        }
        return new int[0];
    }
}
