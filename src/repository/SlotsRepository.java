package repository;

import java.io.*;
import java.util.Scanner;

import utils.LoggerUtil;

public class SlotsRepository {

    private static final String ACCESS_FILE = "src" + File.separator + "repository" + File.separator + "slots_access.txt";

    public static boolean addUserToSlotsFile(String userName) {
        File file = new File(ACCESS_FILE);

        if (!file.exists()) {
            LoggerUtil.logInfo("Missing users access file");
            return false;
        }

        try (FileWriter writer = new FileWriter(file, true)) {
            writer.write(userName + "\n");
        } catch (IOException e) {
            LoggerUtil.logError("Error adding user %s to slots access file: %s", e, userName);
            return false;
        }
        return true;
    }

    public static boolean hasSlotsAccess(String playerName) {
        try (Scanner scanner = new Scanner(new InputStreamReader(new FileInputStream(ACCESS_FILE), "UTF-8"))) {
            while (scanner.hasNextLine()) {
                String line = scanner.nextLine();
                if (line.equals(playerName)) {
                    return true;
                }
            }
        } catch (IOException e) {
            LoggerUtil.logError("Error reading slots access file: %s", e);
        }
        return false;
    }
}

