package model;

public class Command {
    public int id;
    public String sender;
    public String message;

    public Command(int id, String sender, String message) {
        this.id = id;
        this.sender = sender;
        this.message = message;
    }
}