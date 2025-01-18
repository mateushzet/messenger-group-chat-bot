package model;

import java.util.Random;

public class Horse {
    private final String name;
    private final int minMove;
    private final int maxMove;
    private final double fallChance;
    private int position;
    private boolean fallen;
    private int imageNumber;

    public Horse(String name, int minMove, int maxMove, double fallChance, int imageNumber) {
        this.name = name;
        this.minMove = minMove;
        this.maxMove = maxMove;
        this.fallChance = fallChance;
        this.position = 0;
        this.fallen = false;
        this.imageNumber = imageNumber;
    }

    public void move() {
        if (fallen) {
            fallen = false;
            return;
        }

        Random random = new Random();
        position += random.nextInt(maxMove - minMove + 1) + minMove;

        if (random.nextDouble() < fallChance) {
            fallen = true;
        }
    }

    public int getPosition() {
        return position;
    }

    public boolean isFallen() {
        return fallen;
    }

    public String getName() {
        return name;
    }

    public int getImageNumber() {
        return imageNumber;
    }
}