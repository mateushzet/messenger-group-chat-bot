package games.moneytree;

import java.util.List;

public class MoneyTreeGame {
    private String userName;
    private int investedCoins;
    private long startTime;
    private List<Integer> phaseDurations;
    private int witherPhase; // Może wynosić 1–5 lub 7
    private int witherTime; // Dodane pole
    private boolean isActive;


    public MoneyTreeGame() {
    }

    public MoneyTreeGame(String userName, int investedCoins, long startTime, List<Integer> phaseDurations, int witherPhase, int witherTime, boolean isActive) {
        this.userName = userName;
        this.investedCoins = investedCoins;
        this.startTime = startTime;
        this.phaseDurations = phaseDurations;
        this.witherPhase = witherPhase;
        this.witherTime = witherTime;
        this.isActive = isActive;
    }

    public String getUserName() {
        return this.userName;
    }

    public void setUserName(String userName) {
        this.userName = userName;
    }

    public int getInvestedCoins() {
        return this.investedCoins;
    }

    public void setInvestedCoins(int investedCoins) {
        this.investedCoins = investedCoins;
    }

    public long getStartTime() {
        return this.startTime;
    }

    public void setStartTime(long startTime) {
        this.startTime = startTime;
    }

    public List<Integer> getPhaseDurations() {
        return this.phaseDurations;
    }

    public void setPhaseDurations(List<Integer> phaseDurations) {
        this.phaseDurations = phaseDurations;
    }

    public int getWitherPhase() {
        return this.witherPhase;
    }

    public void setWitherPhase(int witherPhase) {
        this.witherPhase = witherPhase;
    }

    public int getWitherTime() {
        return this.witherTime;
    }

    public void setWitherTime(int witherTime) {
        this.witherTime = witherTime;
    }

    public boolean isActive() {
        return this.isActive;
    }

    public void setIsActive(boolean isActive) {
        this.isActive = isActive;
    }

    public MoneyTreeGame userName(String userName) {
        setUserName(userName);
        return this;
    }

    public MoneyTreeGame investedCoins(int investedCoins) {
        setInvestedCoins(investedCoins);
        return this;
    }

    public MoneyTreeGame startTime(long startTime) {
        setStartTime(startTime);
        return this;
    }

    public MoneyTreeGame phaseDurations(List<Integer> phaseDurations) {
        setPhaseDurations(phaseDurations);
        return this;
    }

    public MoneyTreeGame witherPhase(int witherPhase) {
        setWitherPhase(witherPhase);
        return this;
    }

    public MoneyTreeGame witherTime(int witherTime) {
        setWitherTime(witherTime);
        return this;
    }

    public MoneyTreeGame isActive(boolean isActive) {
        setIsActive(isActive);
        return this;
    }
}
