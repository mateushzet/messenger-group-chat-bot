package games.match;

import model.CommandContext;
import repository.UserAvatarRepository;
import repository.UserRepository;
import service.MessageService;
import database.DatabaseConnectionManager;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class SportsBettingService {

    public static void showAllMatches() {
        List<Map<String, Object>> matches = getMatchesFromDatabase();
    
        if (matches.isEmpty()) {
            MessageService.sendMessage("There are no available matches to display.");
            return;
        }
    
        List<String> matchTextsForImage = new ArrayList<>();
    
        for (Map<String, Object> match : matches) {
            String matchId = String.valueOf(match.get("id"));
            String homeTeam = (String) match.get("home_team");
            String awayTeam = (String) match.get("away_team");
            String commenceTime = (String) match.get("commence_time");
            String bookmaker = (String) match.get("bookmaker");
            Double homeOdds = (Double) match.get("home_odds");
            Double drawOdds = (Double) match.get("draw_odds");
            Double awayOdds = (Double) match.get("away_odds");
            Integer homeScore = (Integer) match.get("home_score");
            Integer awayScore = (Integer) match.get("away_score");
    
            if (homeTeam == null || awayTeam == null || commenceTime == null) {
                MessageService.sendMessage("Invalid match data found. Skipping match.");
                continue;
            }
    
            String matchText = String.format("Match ID: %s - %s vs %s at %s\n", matchId, homeTeam, awayTeam, commenceTime);
            String bookmakerText = String.format("Bookmaker: %s\n", bookmaker);
            String oddsText = String.format("Odds: Home - %.2f, Draw - %.2f, Away - %.2f\n", homeOdds, drawOdds, awayOdds);
            String scoreText;
            if(homeScore == -1 && awayScore == -1){
                scoreText = String.format("Score: ? - ?\n");
            } else scoreText = String.format("Score: %d - %d\n", homeScore, awayScore);
    
            matchTextsForImage.add(matchText + bookmakerText + oddsText + scoreText);
        }
    
        MatchesImageGenerator.generateMatchImage(matchTextsForImage);
        MessageService.sendMessageFromClipboard(true);
    }

    public static void showAllResults() {
        List<Map<String, Object>> matches = getResultsFromDatabase();
    
        if (matches.isEmpty()) {
            MessageService.sendMessage("There are no available matches to display.");
            return;
        }
    
        List<String> matchTextsForImage = new ArrayList<>();
    
        for (Map<String, Object> match : matches) {
            String matchId = String.valueOf(match.get("id"));
            String homeTeam = (String) match.get("home_team");
            String awayTeam = (String) match.get("away_team");
            String commenceTime = (String) match.get("commence_time");
            String bookmaker = (String) match.get("bookmaker");
            Double homeOdds = (Double) match.get("home_odds");
            Double drawOdds = (Double) match.get("draw_odds");
            Double awayOdds = (Double) match.get("away_odds");
            Integer homeScore = (Integer) match.get("home_score");
            Integer awayScore = (Integer) match.get("away_score");
    
            if (homeTeam == null || awayTeam == null || commenceTime == null) {
                MessageService.sendMessage("Invalid match data found. Skipping match.");
                continue;
            }
    
            String matchText = String.format("Match ID: %s - %s vs %s at %s\n", matchId, homeTeam, awayTeam, commenceTime);
            String bookmakerText = String.format("Bookmaker: %s\n", bookmaker);
            String oddsText = String.format("Odds: Home - %.2f, Draw - %.2f, Away - %.2f\n", homeOdds, drawOdds, awayOdds);
            String scoreText;
            if(homeScore == -1 && awayScore == -1){
                scoreText = String.format("Score: ? - ?\n");
            } else scoreText = String.format("Score: %d - %d\n", homeScore, awayScore);
    
            matchTextsForImage.add(matchText + bookmakerText + oddsText + scoreText);
        }
    
        MatchesImageGenerator.generateMatchImage(matchTextsForImage);
        MessageService.sendMessageFromClipboard(true);
    }

       private static List<Map<String, Object>> getMatchesFromDatabase() {
        List<Map<String, Object>> matches = new ArrayList<>();
        
        String query = "SELECT id, home_team, away_team, commence_time, bookmaker, home_odds, draw_odds, away_odds, home_score, away_score FROM match_odds WHERE commence_time >= datetime('now', '-3 days')";
        
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(query);
            ResultSet resultSet = statement.executeQuery();
            
            while (resultSet.next()) {
                String commenceTime = resultSet.getString("commence_time");
                Timestamp parsedCommenceTime = null;
                try {
                    parsedCommenceTime = parseCommenceTime(commenceTime);
                } catch (ParseException e) {
                    e.printStackTrace();
                }

                Map<String, Object> match = new HashMap<>();
                match.put("id", resultSet.getInt("id"));
                match.put("home_team", resultSet.getString("home_team"));
                match.put("away_team", resultSet.getString("away_team"));
                match.put("commence_time", parsedCommenceTime != null ? parsedCommenceTime.toString() : null);
                match.put("bookmaker", resultSet.getString("bookmaker"));
                match.put("home_odds", resultSet.getDouble("home_odds"));
                match.put("draw_odds", resultSet.getDouble("draw_odds"));
                match.put("away_odds", resultSet.getDouble("away_odds"));
                match.put("home_score", resultSet.getInt("home_score"));
                match.put("away_score", resultSet.getInt("away_score"));

                matches.add(match);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        
        return matches;
    }

    public static List<Map<String, Object>> getResultsFromDatabase() {
        List<Map<String, Object>> matches = new ArrayList<>();
        
        String query = "SELECT id, home_team, away_team, commence_time, bookmaker, home_odds, draw_odds, away_odds, home_score, away_score FROM match_odds WHERE home_score != -1 AND away_score != -1";
        
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(query);
            ResultSet resultSet = statement.executeQuery();
            
            while (resultSet.next()) {
                String commenceTime = resultSet.getString("commence_time");
                Timestamp parsedCommenceTime = null;
                try {
                    parsedCommenceTime = parseCommenceTime(commenceTime);
                } catch (ParseException e) {
                    e.printStackTrace();
                }

                Map<String, Object> match = new HashMap<>();
                match.put("id", resultSet.getInt("id"));
                match.put("home_team", resultSet.getString("home_team"));
                match.put("away_team", resultSet.getString("away_team"));
                match.put("commence_time", parsedCommenceTime != null ? parsedCommenceTime.toString() : null);
                match.put("bookmaker", resultSet.getString("bookmaker"));
                match.put("home_odds", resultSet.getDouble("home_odds"));
                match.put("draw_odds", resultSet.getDouble("draw_odds"));
                match.put("away_odds", resultSet.getDouble("away_odds"));
                match.put("home_score", resultSet.getInt("home_score"));
                match.put("away_score", resultSet.getInt("away_score"));

                matches.add(match);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        
        return matches;
    }

    public static void placeBet(CommandContext context) {
        String playerName = context.getUserName();
        String betAmount = context.getSecondArgument();
        String matchId = context.getThirdArgument();
        String selectedOutcome = context.getFourthArgument();  
        
        int matchIdParsed = parseMatchId(matchId);
        if (matchIdParsed == -1) return;

        int betAmountParsed = parseBetAmount(betAmount);
        if (betAmountParsed == -1) return;

        if (!MatchOddsRepository.isMatchExist(matchIdParsed)) {
            MessageService.sendMessage("There is no upcoming match with this id.");
            return;
        }

        int currentBalance = UserRepository.getCurrentUserBalance(playerName, true);
        if (currentBalance < betAmountParsed) {
            MessageService.sendMessage("Insufficient funds. Your balance: " + currentBalance);
            return;
        }

        double odds = fetchOddsForMatchAndOutcome(matchIdParsed, selectedOutcome);
        if (odds == -1) {
            MessageService.sendMessage("Invalid outcome or odds could not be fetched.");
            return;
        }

        int newBalance = currentBalance - betAmountParsed;
        UserRepository.updateUserBalance(playerName, newBalance);

        saveBetToDatabase(playerName, matchIdParsed, betAmountParsed, odds, selectedOutcome);

        MessageService.sendMessage(String.format("Bet placed successfully! Your new balance: %d", newBalance));
    }

    private static double fetchOddsForMatchAndOutcome(int matchId, String outcome) {
        double odds = -1;
        
        Map<String, Double> oddsData = MatchOddsRepository.getOddsForMatchAndOutcomes(matchId);
        if (oddsData.containsKey(outcome)) {
            odds = oddsData.get(outcome);
        }
        
        return odds;
    }

    private static void saveBetToDatabase(String playerName, int matchId, int betAmount, double odds, String betType) {
        String insertBetQuery = "INSERT INTO user_bets (match_id, user_name, bet_amount, odds, bet_type) VALUES (?, ?, ?, ?, ?)";
        try (Connection connection = DatabaseConnectionManager.getConnection()) {
            PreparedStatement statement = connection.prepareStatement(insertBetQuery);
            statement.setInt(1, matchId);
            statement.setString(2, playerName);
            statement.setInt(3, betAmount);
            statement.setDouble(4, odds);
            statement.setString(5, betType);
            statement.executeUpdate();
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    private static int parseMatchId(String matchId) {
        try {
            return Integer.parseInt(matchId);
        } catch (NumberFormatException e) {
            MessageService.sendMessage("Invalid match ID.");
            return -1;
        }
    }

    private static int parseBetAmount(String betAmount) {
        try {
            int bet = Integer.parseInt(betAmount);
            if (bet <= 0) {
                MessageService.sendMessage("Bet amount must be greater than 0.");
                return -1;
            }
            return bet;
        } catch (NumberFormatException e) {
            MessageService.sendMessage("Invalid bet amount.");
            return -1;
        }
    }

    public static void checkAndPayOutBets(CommandContext context) {
        String playerName = context.getUserName();
        
        List<Map<String, Object>> userBets = MatchOddsRepository.getUserBets(playerName);
        if (userBets.isEmpty()) {
            MessageService.sendMessage("You have no bets placed.");
            return;
        }
        
        StringBuilder response = new StringBuilder(playerName+": ");
        StringBuilder payoutResponse = new StringBuilder("");
        
        for (Map<String, Object> bet : userBets) {
            int matchId = (int) bet.get("match_id");
            int betAmount = (int) bet.get("bet_amount");
            String outcome = (String) bet.get("outcome");
            boolean isPaid = (boolean) bet.get("is_paid");
            int betId = (int) bet.get("bet_id");
            if (isPaid) {
                continue;
            }
        
            Map<String, Object> result = MatchOddsRepository.getResultByMatchId(matchId);
            if (result == null) {
                payoutResponse.append(String.format("No result yet for match %d.\n", matchId));
                continue;
            }
        
            int homeScore = (int) result.get("homeScore");
            int awayScore = (int) result.get("awayScore");
        
            String matchResult = determineMatchResult(homeScore, awayScore);
            boolean isBetWon = checkIfBetIsWon(outcome, matchResult);
        
            if (isBetWon) {
                double odds = MatchOddsRepository.getOddsForMatchAndOutcome(matchId, playerName);
                double winnings = betAmount * odds;
                int currentBalance = UserRepository.getCurrentUserBalance(playerName, true);
                int newBalance = (int) (currentBalance + winnings);
                UserRepository.updateUserBalance(playerName, newBalance);
        
                MatchOddsRepository.updateBetAsPaid(betId);
        
                response.append(String.format("You won on match %d! Your winnings: %.2f. New balance: %d\n", matchId, winnings, newBalance));
                UserAvatarRepository.assignAvatarToUser(playerName, "sports");
            } else {
                response.append(String.format("You lost on match %d. No winnings.\n", matchId));
            }
        }
        if(payoutResponse.isEmpty()) response.append(String.format("No applicable bet to check result"));
        else response.append(payoutResponse);
        MessageService.sendMessage(response.toString());
    }
    
    private static String determineMatchResult(int homeScore, int awayScore) {
        if (homeScore > awayScore) {
            return "home";
        } else if (awayScore > homeScore) {
            return "away";
        } else {
            return "draw";
        }
    }
    
    public static Timestamp parseCommenceTime(String commenceTime) throws ParseException {
        String format = "yyyy-MM-dd'T'HH:mm:ss'Z'";

        SimpleDateFormat sdf = new SimpleDateFormat(format);
        
        Date date = sdf.parse(commenceTime);
        
        return new Timestamp(date.getTime());
    }

    private static boolean checkIfBetIsWon(String betOutcome, String matchResult) {
        return betOutcome.equals(matchResult);
    }
}