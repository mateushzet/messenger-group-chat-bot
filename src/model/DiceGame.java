package model;

public class DiceGame {
    private String userName;
    private int betAmount;
    private int[] diceValues;
    private boolean gameInProgress;
    private int userBalance;

    public DiceGame(String userName, int betAmount, int[] rolls, boolean gameInProgress, int userBalance) {
        this.userName = userName;
        this.betAmount = betAmount;
        this.diceValues = rolls;
        this.gameInProgress = gameInProgress;
        this.userBalance = userBalance;
    }

    public String getUserName() {
        return userName;
    }

    public void setUserName(String userName) {
        this.userName = userName;
    }

    public int getBetAmount() {
        return betAmount;
    }

    public void setBetAmount(int betAmount) {
        this.betAmount = betAmount;
    }

    public int[] getDiceValues() {
        return diceValues;
    }

    public void setDiceValues(int[] diceValues) {
        this.diceValues = diceValues;
    }

    public boolean isGameInProgress() {
        return gameInProgress;
    }

    public void setGameInProgress(boolean gameInProgress) {
        this.gameInProgress = gameInProgress;
    }

    public int getUserBalance() {
        return userBalance;
    }

    public void setUserBalance(int userBalance) {
        this.userBalance = userBalance;
    }
}
