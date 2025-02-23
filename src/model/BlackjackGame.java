package model;

import java.util.ArrayList;
import java.util.List;

public class BlackjackGame {

    private String userName;
    private int currentBet;
    private int balance;
    private List<String> playerHand;
    private List<String> splitHand;
    private List<String> dealerHand;
    private boolean gameInProgress;
    private boolean playerStands;
    private boolean isSplit;

    public BlackjackGame(String userName, int currentBet, boolean gameInProgress, boolean playerStands, int balance) {
        this.userName = userName;
        this.currentBet = currentBet;
        this.playerHand = new ArrayList<>();
        this.splitHand = new ArrayList<>();
        this.dealerHand = new ArrayList<>();
        this.gameInProgress = gameInProgress;
        this.playerStands = playerStands;
        this.isSplit = false;
    }

    public BlackjackGame(String userName, int currentBet, List<String> playerHand, List<String> dealerHand, boolean gameInProgress, int balance) {
        this.userName = userName;
        this.currentBet = currentBet;
        this.playerHand = playerHand;
        this.splitHand = new ArrayList<>();
        this.dealerHand = dealerHand;
        this.gameInProgress = gameInProgress;
        this.playerStands = false;
        this.isSplit = false;
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

    public List<String> getSplitHand() {
        return splitHand;
    }

    public void setSplitHand(List<String> splitHand) {
        this.splitHand = splitHand;
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

    public boolean isSplit() {
        return isSplit;
    }

    public void setSplit(boolean split) {
        isSplit = split;
    }

    public boolean canSplit() {
        if (playerHand.size() == 2 && splitHand.isEmpty()) {
            String card1 = playerHand.get(0).replaceAll("[♠♣♦♥]", "");
            String card2 = playerHand.get(1).replaceAll("[♠♣♦♥]", "");
            return card1.equals(card2);
        }
        return false;
    }

    public void split() {
        if (canSplit()) {
            splitHand.add(playerHand.remove(1));
            isSplit = true;
        }
    }
}