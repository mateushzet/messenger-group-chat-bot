package model;

import java.util.Random;

public class MathQuestion {
    private int num1, num2, num3, num4;
    private String[] operations;

    public MathQuestion() {
        Random random = new Random();
        this.num1 = random.nextInt(10) + 1;
        this.num2 = random.nextInt(10) + 1;
        this.num3 = random.nextInt(10) + 1;
        this.num4 = random.nextInt(10) + 1;

        this.operations = new String[3];
        for (int i = 0; i < 3; i++) {
            operations[i] = random.nextBoolean() ? "+" : "-";
        }
    }

    public String generateQuestion() {
        return num1 + " " + operations[0] + " " + num2 + " " + operations[1] + " " + num3 + " " + operations[2] + " " + num4 + " = ?";
    }

    public int calculateAnswer() {
        int result = num1;

        result = applyOperation(result, num2, operations[0]);
        result = applyOperation(result, num3, operations[1]);
        result = applyOperation(result, num4, operations[2]);

        return result;
    }

    private int applyOperation(int current, int number, String operation) {
        if (operation.equals("+")) {
            return current + number;
        } else {
            return current - number;
        }
    }
}