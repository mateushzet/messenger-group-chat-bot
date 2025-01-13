package model;

import java.time.LocalDateTime;

public class GameHistory {
    private int id;
    private String userName;
    private String gameType;
    private String betCommand;
    private int betAmount;
    private int resultAmount;
    private String note;
    private LocalDateTime createdAt;

    public GameHistory(int id, String userName, String gameType, String betCommand, int betAmount, int resultAmount, String note, LocalDateTime createdAt) {
        this.id = id;
        this.userName = userName;
        this.gameType = gameType;
        this.betCommand = betCommand;
        this.betAmount = betAmount;
        this.resultAmount = resultAmount;
        this.note = note;
        this.createdAt = createdAt;
    }

    public int getId() {
        return id;
    }

    public String getUserName() {
        return userName;
    }

    public String getGameType() {
        return gameType;
    }

    public String getBetCommand() {
        return betCommand;
    }

    public int getBetAmount() {
        return betAmount;
    }

    public int getResultAmount() {
        return resultAmount;
    }

    public String getNote() {
        return note;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    @Override
    public String toString() {
        return "GameHistory{" +
               "id=" + id +
               ", userName='" + userName + '\'' +
               ", gameType='" + gameType + '\'' +
               ", betCommand='" + betCommand + '\'' +
               ", betAmount=" + betAmount +
               ", resultAmount=" + resultAmount +
               ", note='" + note + '\'' +
               ", createdAt=" + createdAt +
               '}';
    }
}