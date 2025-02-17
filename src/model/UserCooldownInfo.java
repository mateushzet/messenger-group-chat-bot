package model;

import java.time.LocalTime;

public class UserCooldownInfo {
    private int messageCount;
    private LocalTime lastMessageTime;
    private int cooldownDuration;

    public UserCooldownInfo() {
        this.messageCount = 0;
        this.lastMessageTime = LocalTime.now();
        this.cooldownDuration = 10;
    }

    public int getMessageCount() {
        return messageCount;
    }

    public void incrementMessageCount() {
        this.messageCount++;
    }

    public LocalTime getLastMessageTime() {
        return lastMessageTime;
    }

    public void setLastMessageTime(LocalTime lastMessageTime) {
        this.lastMessageTime = lastMessageTime;
    }

    public int getCooldownDuration() {
        return cooldownDuration;
    }

    public void increaseCooldownDuration(long elapsedTime) {
        this.cooldownDuration += 10 - elapsedTime;

        if (this.cooldownDuration < 0) {
            this.cooldownDuration = 0;
        }
    }

    public void reset() {
        this.messageCount = 0;
        this.cooldownDuration = 10;
    }
}