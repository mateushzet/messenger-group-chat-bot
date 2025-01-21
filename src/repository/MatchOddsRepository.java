package repository;

import database.DatabaseConnectionManager;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.*;

public class MatchOddsRepository {

    public static List<Map<String, Object>> getUserBets(String playerName) {
        String query = "SELECT * FROM bets WHERE player_name = ?";
        List<Map<String, Object>> bets = new ArrayList<>();
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(query);
            statement.setString(1, playerName);
            ResultSet resultSet = statement.executeQuery();

            while (resultSet.next()) {
                Map<String, Object> bet = new HashMap<>();
                bet.put("match_id", resultSet.getInt("match_id"));
                bet.put("bet_amount", resultSet.getInt("bet_amount"));
                bet.put("outcome", resultSet.getString("outcome"));
                bets.add(bet);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return bets;
    }

    public static Map<String, Object> getResultByMatchId(int matchId) {
        String query = "SELECT home_score, away_score FROM match_odds WHERE id = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(query);
            statement.setInt(1, matchId);
            ResultSet resultSet = statement.executeQuery();

            if (resultSet.next()) {
                Map<String, Object> result = new HashMap<>();
                result.put("homeScore", resultSet.getInt("home_score"));
                result.put("awayScore", resultSet.getInt("away_score"));
                return result;
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static Map<String, Double> getOddsForMatchAndOutcomes(int matchId) {
        Map<String, Double> oddsData = new HashMap<>();
        String query = "SELECT bookmaker, home_odds, away_odds, draw_odds FROM match_odds WHERE id = ?";
        
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(query);
            statement.setInt(1, matchId);
            ResultSet resultSet = statement.executeQuery();
            
            while (resultSet.next()) {
                oddsData.put("home", resultSet.getDouble("home_odds"));
                oddsData.put("away", resultSet.getDouble("away_odds"));
                oddsData.put("draw", resultSet.getDouble("draw_odds"));
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        
        return oddsData;
    }

    public static double getOddsForMatchAndOutcome(int matchId, String outcome) {
        String query = "SELECT " + outcome + "_odds FROM match_odds WHERE match_id = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(query);
            statement.setInt(1, matchId);
            ResultSet resultSet = statement.executeQuery();
    
            if (resultSet.next()) {
                return resultSet.getDouble(outcome + "_odds");
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return -1;
    }

    public static void updateUserBalance(String playerName, double newBalance) {
        String query = "UPDATE users SET balance = ? WHERE player_name = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(query);
            statement.setDouble(1, newBalance);
            statement.setString(2, playerName);
            statement.executeUpdate();
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    public static void saveBetToDatabase(String playerName, int matchId, int betAmount, String outcome) {
        String insertBetQuery = "INSERT INTO bets (match_id, player_name, bet_amount, outcome) VALUES (?, ?, ?, ?)";
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(insertBetQuery);
            statement.setInt(1, matchId);
            statement.setString(2, playerName);
            statement.setInt(3, betAmount);
            statement.setString(4, outcome);
            statement.executeUpdate();
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    public static boolean isMatchExist(int id) {
        String query = "SELECT COUNT(*) FROM match_odds WHERE id = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(query);
            statement.setInt(1, id);
            ResultSet rs = statement.executeQuery();
            return rs.getInt(1) > 0;
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return false;
    }

    public static List<Map<String, Object>> getAllMatches() {
        List<Map<String, Object>> matches = new ArrayList<>();
        String query = "SELECT * FROM match_odds";
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(query);
            ResultSet rs = statement.executeQuery();
            while (rs.next()) {
                Map<String, Object> match = new HashMap<>();
                match.put("id", rs.getInt("id"));
                match.put("homeTeam", rs.getString("home_team"));
                match.put("awayTeam", rs.getString("away_team"));
                match.put("commenceTime", rs.getString("commence_time"));
                matches.add(match);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return matches;
    }

    public static List<Map<String, Object>> getAllResults() {
        List<Map<String, Object>> results = new ArrayList<>();
        String query = "SELECT id, home_score, away_score,  FROM match_odds";
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(query);
            ResultSet rs = statement.executeQuery();
            while (rs.next()) {
                Map<String, Object> result = new HashMap<>();
                result.put("matchId", rs.getInt("id"));
                result.put("homeScore", rs.getInt("home_score"));
                result.put("awayScore", rs.getInt("away_score"));
                result.put("homeTeam", rs.getString("home_team"));
                result.put("awayTeam", rs.getString("away_team"));
                result.put("resultTime", rs.getString("result_time"));
                results.add(result);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return results;
    }

    public static void updateBetAsPaid(Object betId) {
        String updateQuery = "UPDATE bets SET is_paid = TRUE WHERE bet_id = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(updateQuery);
            statement.setInt(1, (int) betId);
            statement.executeUpdate();
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }
}