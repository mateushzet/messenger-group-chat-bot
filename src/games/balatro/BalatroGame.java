package games.balatro;

import java.util.List;

public class BalatroGame {
    private String userName;
    private int betAmount;
    private List<String> playerHand;
    private List<String> discardPile;
    private List<String> deck;
    private boolean gameInProgress;
    private int gameStatus;
    private int selectedJokerId;
    private List<Integer> availableJokers;
    private List<String> keptPile;
    private List<String> drawPile;
    private List<String> handValues;

 public BalatroGame(String userName, int currentBet, List<String> playerHand, List<String> discardPile,
                      boolean gameInProgress, int selectedJokerId, List<String> handValues) {
        this.userName = userName;
        this.betAmount = currentBet;
        this.playerHand = playerHand;
        this.discardPile = discardPile;
        this.gameInProgress = gameInProgress;
        this.gameStatus = 0;
        this.selectedJokerId = selectedJokerId;
        this.handValues = handValues;
    }

public BalatroGame(String userName, int currentBet, List<String> playerHand, List<String> discardPile,
                      boolean gameInProgress, int selectedJokerId, List<String> keptPile, List<String> drawPile, List<String> handValues) {
        this.userName = userName;
        this.betAmount = currentBet;
        this.playerHand = playerHand;
        this.discardPile = discardPile;
        this.gameInProgress = gameInProgress;
        this.gameStatus = 0;
        this.selectedJokerId = selectedJokerId;
        this.keptPile = keptPile;
        this.drawPile = drawPile;
        this.handValues = handValues;
    }

    public String getUserName() { return userName; }
    public int getBetAmount() { return betAmount; }
    public void setBetAmount(int currentBet) { this.betAmount = currentBet; }
    public List<String> getPlayerHand() { return playerHand; }
    public void setPlayerHand(List<String> playerHand) { this.playerHand = playerHand; }
    public List<String> getDiscardPile() { return discardPile; }
    public void setDiscardPile(List<String> discardPile) { this.discardPile = discardPile; }
    public boolean isGameInProgress() { return gameInProgress; }
    public void setGameInProgress(boolean gameInProgress) { this.gameInProgress = gameInProgress; }
    public int getGameStatus() { return gameStatus; }
    public void setGameStatus(int gameStatus) { this.gameStatus = gameStatus; }
    public int getSelectedJokerId() { return selectedJokerId; }
    public void setSelectedJokerId(int selectedJokerId) { this.selectedJokerId = selectedJokerId; }
    public List<Integer> getAvailableJokers() { return availableJokers; }
    public void setAvailableJokers(List<Integer> availableJokers) { this.availableJokers = availableJokers; }
    public List<Integer> getAvailableJokerIds() { return availableJokers; }
    public void setAvailableJokerIds(List<Integer> availableJokerIds) { this.availableJokers = availableJokerIds; }
    public List<String> getDeck() { return deck; }
    public void setDeck(List<String> deck) { this.deck = deck; }
    public List<String> getKeptPile() { return keptPile; }
    public void setKeptPile(List<String> keptPile) { this.keptPile = keptPile; }
    public List<String> getDrawPile() { return drawPile; }
    public void setDrawPile(List<String> drawPile) { this.drawPile = drawPile; }
    public List<String> getHandValues() { return handValues; }
    public void setHandValues(List<String> handValues) { this.handValues = handValues; }
}