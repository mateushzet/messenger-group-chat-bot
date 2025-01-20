package service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import database.DatabaseConnectionManager;

import utils.ConfigReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;

public class SportsApiToDatabase {

    private static final String API_KEY = ConfigReader.getTheOddsApiKey();
    private static final String API_URL_ODDS = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds/";
    private static final String API_URL_SCORES = "https://api.the-odds-api.com/v4/sports/soccer_epl/scores/";

    private static final String[] bookmakersOrder = {
            "Pinnacle", "Betfair", "William Hill", "Unibet", "888sport", "Betsson", 
            "1xBet", "Marathon Bet", "Betclic", "Nordic Bet", "Tipico", "Coolbet",
            "GTbets", "Everygame", "Matchbook", "BetOnline.ag"
    };

    public static void main(String[] args) {
        try {
            SportsApiToDatabase.fetchAndStoreMatchData();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static void fetchAndStoreMatchData() throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        
        String queryParamsForOdds = "?regions=eu&markets=h2h&apiKey=" + API_KEY;
        HttpRequest requestForOdds = HttpRequest.newBuilder()
                .uri(URI.create(API_URL_ODDS + queryParamsForOdds))
                .build();
        HttpResponse<String> responseForOdds = client.send(requestForOdds, HttpResponse.BodyHandlers.ofString());
        
        String queryParamsForScores = "?apiKey=" + API_KEY + "&dateFormat=iso";
        HttpRequest requestForScores = HttpRequest.newBuilder()
                .uri(URI.create(API_URL_SCORES + queryParamsForScores))
                .build();
        HttpResponse<String> responseForScores = client.send(requestForScores, HttpResponse.BodyHandlers.ofString());
        
        if (responseForOdds.statusCode() == 200 && responseForScores.statusCode() == 200) {
            ObjectMapper objectMapper = new ObjectMapper();
        
            JsonNode oddsRootNode = objectMapper.readTree(responseForOdds.body());
            JsonNode scoresRootNode = objectMapper.readTree(responseForScores.body());
    
            System.out.println("Response for Scores: " + responseForScores.body());
        
            for (JsonNode match : oddsRootNode) {
                String matchId = match.path("id").asText();
                String homeTeam = match.path("home_team").asText();
                String awayTeam = match.path("away_team").asText();
                String commenceTime = match.path("commence_time").asText();
                JsonNode bookmakers = match.path("bookmakers");
        
                JsonNode scoreNode = findScoreForMatch(scoresRootNode, homeTeam, awayTeam, commenceTime);
        
                int homeScore = -1;
                int awayScore = -1;
                if (scoreNode != null) {
                    homeScore = scoreNode.path("home_score").asInt();
                    awayScore = scoreNode.path("away_score").asInt();
                }
        
                saveMatchAndOddsToDatabase(matchId, homeTeam, awayTeam, commenceTime, bookmakers, homeScore, awayScore);
            }
        } else {
            System.out.println("Błąd API: " + responseForOdds.statusCode() + " lub " + responseForScores.statusCode());
        }
    }

    private static JsonNode findScoreForMatch(JsonNode scoresRootNode, String homeTeam, String awayTeam, String commenceTime) {
        for (JsonNode match : scoresRootNode) {
            String matchHomeTeam = match.path("home_team").asText();
            String matchAwayTeam = match.path("away_team").asText();
            String matchCommenceTime = match.path("commence_time").asText();
    
            if (matchHomeTeam.equalsIgnoreCase(homeTeam) && matchAwayTeam.equalsIgnoreCase(awayTeam) && matchCommenceTime.equals(commenceTime)) {
                JsonNode scores = match.path("scores");
    
                int homeScore = -1;
                int awayScore = -1;
    
                if (scores.isArray()) {
                    for (JsonNode score : scores) {
                        String teamName = score.path("name").asText();
                        int teamScore = score.path("score").asInt();
    
                        if (teamName.equalsIgnoreCase(homeTeam)) {
                            homeScore = teamScore;
                        } else if (teamName.equalsIgnoreCase(awayTeam)) {
                            awayScore = teamScore;
                        }
                    }
                }
    
                ObjectMapper objectMapper = new ObjectMapper();
                return objectMapper.createObjectNode()
                    .put("home_score", homeScore)
                    .put("away_score", awayScore);
            }
        }
        return null;
    }

    private static void saveMatchAndOddsToDatabase(String matchId, String homeTeam, String awayTeam, String commenceTime, JsonNode bookmakers, int homeScore, int awayScore) {
        String checkMatchQuery = "SELECT COUNT(*) FROM match_odds WHERE match_id = ?";
        
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement checkStatement = connection.prepareStatement(checkMatchQuery);
            checkStatement.setString(1, matchId);
            var resultSet = checkStatement.executeQuery();
            resultSet.next();
            
            if (resultSet.getInt(1) > 0) {
                String updateQuery = "UPDATE match_odds SET home_team = ?, away_team = ?, commence_time = ?, bookmaker = ?, home_odds = ?, away_odds = ?, draw_odds = ?, home_score = ?, away_score = ? WHERE match_id = ?";
                
                for (String bookmakerName : bookmakersOrder) {
                    JsonNode bookmakerNode = getBookmakerData(bookmakers, bookmakerName);
                    if (bookmakerNode != null) {
                        JsonNode markets = bookmakerNode.path("markets");
        
                        for (JsonNode market : markets) {
                            String marketKey = market.path("key").asText();
                            if ("h2h".equals(marketKey)) {
                                JsonNode outcomes = market.path("outcomes");
        
                                Double homeOdds = null;
                                Double awayOdds = null;
                                Double drawOdds = null;
        
                                for (JsonNode outcome : outcomes) {
                                    String outcomeName = outcome.path("name").asText();
                                    double price = outcome.path("price").asDouble();
        
                                    if (outcomeName.equalsIgnoreCase(homeTeam)) {
                                        homeOdds = price;
                                    } else if (outcomeName.equalsIgnoreCase(awayTeam)) {
                                        awayOdds = price;
                                    } else if ("Draw".equalsIgnoreCase(outcomeName)) {
                                        drawOdds = price;
                                    }
                                }
        
                                if (homeOdds != null && awayOdds != null && drawOdds != null) {
                                    PreparedStatement statement = connection.prepareStatement(updateQuery);
                                    statement.setString(1, homeTeam);
                                    statement.setString(2, awayTeam);
                                    statement.setString(3, commenceTime);
                                    statement.setString(4, bookmakerName);
                                    statement.setDouble(5, homeOdds);
                                    statement.setDouble(6, awayOdds);
                                    statement.setDouble(7, drawOdds);
                                    statement.setInt(8, homeScore);
                                    statement.setInt(9, awayScore);
                                    statement.setString(10, matchId);
                                    statement.executeUpdate();
        
                                    return;
                                }
                            }
                        }
                    }
                }
            } else {
                String insertQuery = "INSERT INTO match_odds (match_id, home_team, away_team, commence_time, bookmaker, home_odds, away_odds, draw_odds, home_score, away_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
                
                for (String bookmakerName : bookmakersOrder) {
                    JsonNode bookmakerNode = getBookmakerData(bookmakers, bookmakerName);
                    if (bookmakerNode != null) {
                        JsonNode markets = bookmakerNode.path("markets");
        
                        for (JsonNode market : markets) {
                            String marketKey = market.path("key").asText();
                            if ("h2h".equals(marketKey)) {
                                JsonNode outcomes = market.path("outcomes");
        
                                Double homeOdds = null;
                                Double awayOdds = null;
                                Double drawOdds = null;
        
                                for (JsonNode outcome : outcomes) {
                                    String outcomeName = outcome.path("name").asText();
                                    double price = outcome.path("price").asDouble();
        
                                    if (outcomeName.equalsIgnoreCase(homeTeam)) {
                                        homeOdds = price;
                                    } else if (outcomeName.equalsIgnoreCase(awayTeam)) {
                                        awayOdds = price;
                                    } else if ("Draw".equalsIgnoreCase(outcomeName)) {
                                        drawOdds = price;
                                    }
                                }
        
                                if (homeOdds != null && awayOdds != null && drawOdds != null) {
                                    PreparedStatement statement = connection.prepareStatement(insertQuery);
                                    statement.setString(1, matchId);
                                    statement.setString(2, homeTeam);
                                    statement.setString(3, awayTeam);
                                    statement.setString(4, commenceTime);
                                    statement.setString(5, bookmakerName);
                                    statement.setDouble(6, homeOdds);
                                    statement.setDouble(7, awayOdds);
                                    statement.setDouble(8, drawOdds);
                                    statement.setInt(9, homeScore);
                                    statement.setInt(10, awayScore);
                                    statement.executeUpdate();
        
                                    return;
                                }
                            }
                        }
                    }
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    private static JsonNode getBookmakerData(JsonNode bookmakers, String bookmakerName) {
        for (JsonNode bookmaker : bookmakers) {
            String title = bookmaker.path("title").asText();
            if (bookmakerName.equalsIgnoreCase(title)) {
                return bookmaker;
            }
        }
        return null;
    }
}
