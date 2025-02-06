package games.match;

import database.DatabaseConnectionManager;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;


public class MatchOddsRepository {

    public static List<Map<String, Object>> getUserBets(String playerName) {
        String query = "SELECT * FROM user_bets WHERE user_name = ?";
        List<Map<String, Object>> bets = new ArrayList<>();
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(query);
            statement.setString(1, playerName);
            ResultSet resultSet = statement.executeQuery();

            while (resultSet.next()) {
                Map<String, Object> bet = new HashMap<>();
                bet.put("match_id", resultSet.getInt("match_id"));
                bet.put("bet_amount", resultSet.getInt("bet_amount"));
                bet.put("outcome", resultSet.getString("bet_type"));
                bet.put("is_paid", resultSet.getBoolean("is_paid"));
                bet.put("bet_id", resultSet.getInt("bet_id"));
                bets.add(bet);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return bets;
    }

    public static Map<String, Object> getResultByMatchId(int matchId) {
        String query = "SELECT home_score, away_score FROM match_odds WHERE id = ? AND home_score != -1 AND away_score != -1";
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

    public static double getOddsForMatchAndOutcome(int matchId, String PlayerName) {
        String query = "SELECT odds FROM user_bets WHERE match_id = ? AND user_name = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(query);
            statement.setInt(1, matchId);
            statement.setString(2, PlayerName);
            ResultSet resultSet = statement.executeQuery();
    
            if (resultSet.next()) {
                return resultSet.getDouble("odds");
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return 1;
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
        String insertBetQuery = "INSERT INTO user_bets (match_id, player_name, bet_amount, outcome) VALUES (?, ?, ?, ?)";
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
        String query = "SELECT commence_time FROM match_odds WHERE id = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(query);
            statement.setInt(1, id);
            ResultSet rs = statement.executeQuery();
            if (rs.next()) {
                String commenceTimeString = rs.getString("commence_time");
                if (commenceTimeString != null) {
                    LocalDateTime utcTime = LocalDateTime.parse(commenceTimeString, DateTimeFormatter.ISO_DATE_TIME);

                    ZonedDateTime zonedTime = utcTime.atZone(ZoneId.of("UTC"))
                                                    .withZoneSameInstant(ZoneId.systemDefault());

                    return !zonedTime.toLocalDateTime().isBefore(LocalDateTime.now());
                }
            }
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
        String query = "SELECT id, home_score, away_score, home_team, away_team, commence_time FROM match_odds";
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
                result.put("resultTime", rs.getString("commence_time"));
                results.add(result);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return results;
    }

    public static void updateBetAsPaid(Object betId) {
        String updateQuery = "UPDATE user_bets SET is_paid = TRUE WHERE bet_id = ?";
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(updateQuery);
            statement.setInt(1, (int) betId);
            statement.executeUpdate();
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }
    
}