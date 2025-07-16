package model;

import java.awt.image.BufferedImage;

import java.util.List;

public class GameHelp {
    private final String description;
    private final List<String> commands;
    private final BufferedImage exampleImage;

    public GameHelp(String description, List<String> commands, BufferedImage exampleImage) {
        this.description = description;
        this.commands = commands;
        this.exampleImage = exampleImage;
    }

    public String getDescription() { return description; }
    public List<String> getCommands() { return commands; }
    public BufferedImage getExampleImage() { return exampleImage; }
}
