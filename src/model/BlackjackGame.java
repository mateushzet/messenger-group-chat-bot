package model;

import java.util.ArrayList;
import java.util.List;

public class BlackjackGame {

    private String userName;
    private int currentBet;
    private int balance;
    private List<String> playerHand;
    private List<String> dealerHand;
    private boolean gameInProgress;
    private boolean playerStands;

    public BlackjackGame(String userName, int currentBet, boolean gameInProgress, boolean playerStands, int balance) {
        this.userName = userName;
        this.currentBet = currentBet;
        this.playerHand = new ArrayList<>();
        this.dealerHand = new ArrayList<>();
        this.gameInProgress = gameInProgress;
        this.playerStands = playerStands;
    }

    public BlackjackGame(String userName, int currentBet, List<String> playerHand, List<String> dealerHand, boolean gameInProgress, int balance) {
        this.userName = userName;
        this.currentBet = currentBet;
        this.playerHand = playerHand;
        this.dealerHand = dealerHand;
        this.gameInProgress = gameInProgress;
        this.playerStands = false;
    }

    public String getUserName() {
        return userName;
    }

    public int getBetAmount() {
        return currentBet;
    }

    public int getBalance() {
        return balance;
    }

    public void setUserName(String userName) {
        this.userName = userName;
    }

    public int getCurrentBet() {
        return currentBet;
    }

    public void setCurrentBet(int currentBet) {
        this.currentBet = currentBet;
    }

    public List<String> getPlayerHand() {
        return playerHand;
    }

    public void setPlayerHand(List<String> playerHand) {
        this.playerHand = playerHand;
    }

    public List<String> getDealerHand() {
        return dealerHand;
    }

    public void setDealerHand(List<String> dealerHand) {
        this.dealerHand = dealerHand;
    }

    public boolean isGameInProgress() {
        return gameInProgress;
    }

    public void setGameInProgress(boolean gameInProgress) {
        this.gameInProgress = gameInProgress;
    }

    public boolean isPlayerStands() {
        return playerStands;
    }

    public void setPlayerStands(boolean playerStands) {
        this.playerStands = playerStands;
    }
}
