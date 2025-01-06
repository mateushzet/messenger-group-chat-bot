package repository;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Scanner;

import utils.LoggerUtil;

public class JackpotRepository {

    private static final String JACKPOT_FILE = "src" + File.separator + "repository" + File.separator + "jackpot.txt";
    private static int jackpotPool = 0;

    public static void loadJackpot() {
        File jackpotFile = new File(JACKPOT_FILE);
        if (jackpotFile.exists()) {
            try (Scanner scanner = new Scanner(jackpotFile)) {
                jackpotPool = Integer.parseInt(scanner.nextLine());
            } catch (IOException | NumberFormatException e) {
                LoggerUtil.logError("Error loading jackpot state", e);
            }
        }
    }

    public static void saveJackpot() {
        try (FileWriter writer = new FileWriter(JACKPOT_FILE)) {
            writer.write(Integer.toString(jackpotPool));
        } catch (IOException e) {
            LoggerUtil.logError("Error saving jackpot state", e);
        }
    }

    public static int getJackpot() {
        loadJackpot();
        return jackpotPool;
    }

    public static void addToJackpotPool(int betAmount) {
        loadJackpot();
        jackpotPool += (int) (betAmount * 0.1);
    }

    public static double getJackpotMultiplier() {
        loadJackpot();
        return jackpotPool;
    }

    public static void resetJackpot() {
        jackpotPool = 0;
        saveJackpot();
    }

}
