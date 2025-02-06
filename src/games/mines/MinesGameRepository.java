package repository;

import java.sql.*;
import database.DatabaseConnectionManager;
import model.MinesGame;
import utils.Logger;

public class MinesGameRepository {

    public static void saveGame(MinesGame game) {
        String query = "INSERT INTO mines_game (user_name, bet_amount, total_bombs, revealed_fields, game_in_progress, bomb_board, revealed_board) VALUES (?, ?, ?, ?, ?, ?, ?)";
    
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
    
            statement.setString(1, game.getUserName());
            statement.setInt(2, game.getBetAmount());
            statement.setInt(3, game.getTotalBombs());
            statement.setInt(4, game.getRevealedFields());
            statement.setBoolean(5, game.isGameInProgress());
            statement.setObject(6, convertToBlob(game.getBombBoard()));
            statement.setObject(7, convertToBlob(game.getRevealedBoard()));
    
            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while saving game", "MinesGameRepository.saveGame()", e);
        }
    }

    public static MinesGame getGameByUserName(String userName) {
        String query = "SELECT * FROM mines_game WHERE user_name = ? LIMIT 1";
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
    
            statement.setString(1, userName);
            ResultSet resultSet = statement.executeQuery();
    
            if (resultSet.next()) {
                boolean[][] bombBoard = convertFromBlob(resultSet.getBytes("bomb_board"));
                boolean[][] revealedBoard = convertFromBlob(resultSet.getBytes("revealed_board"));
    
                return new MinesGame(
                        resultSet.getString("user_name"),
                        resultSet.getInt("bet_amount"),
                        resultSet.getInt("total_bombs"),
                        resultSet.getInt("revealed_fields"),
                        resultSet.getBoolean("game_in_progress"),
                        bombBoard,
                        revealedBoard
                );
            }
        } catch (SQLException e) {
            Logger.logError("Error while fetching game by username", "MinesGameRepository.getGameByUserName()", e);
        }
        return null;
    }

    public static void updateGame(MinesGame game) {

        String query = "UPDATE mines_game SET bet_amount = ?, total_bombs = ?, revealed_fields = ?, game_in_progress = ?, bomb_board = ?, revealed_board = ? WHERE user_name = ?";
    
        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {
    
            statement.setInt(1, game.getBetAmount());
            statement.setInt(2, game.getTotalBombs());
            statement.setInt(3, game.getRevealedFields());
            statement.setBoolean(4, game.isGameInProgress());
            statement.setObject(5, convertToBlob(game.getBombBoard()));
            statement.setObject(6, convertToBlob(game.getRevealedBoard()));
            statement.setString(7, game.getUserName());
    
            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while updating game", "MinesGameRepository.updateGame()", e);
        }

    }

    public static void deleteGame(String userName) {
        String query = "DELETE FROM mines_game WHERE user_name = ?";

        try (Connection connection = DatabaseConnectionManager.getConnection();
             PreparedStatement statement = connection.prepareStatement(query)) {

            statement.setString(1, userName);
            statement.executeUpdate();
        } catch (SQLException e) {
            Logger.logError("Error while deleting game", "MinesGameRepository.deleteGame()", e);
        }
    }

    private static byte[] convertToBlob(boolean[][] board) {
        StringBuilder sb = new StringBuilder();
        for (boolean[] row : board) {
            for (boolean cell : row) {
                sb.append(cell ? "1" : "0");
            }
            sb.append("\n");
        }
        return sb.toString().getBytes();
    }

    private static boolean[][] convertFromBlob(byte[] data) {
        String str = new String(data);
        String[] rows = str.split("\n");
        boolean[][] board = new boolean[rows.length][rows[0].length()];
    
        for (int i = 0; i < rows.length; i++) {
            for (int j = 0; j < rows[i].length(); j++) {
                board[i][j] = rows[i].charAt(j) == '1';
            }
        }
        return board;
    }

}
