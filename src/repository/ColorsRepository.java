package repository;

import java.io.*;
import java.util.Scanner;

public class ColorsRepository {

    private static final String ACCESS_FILE = "src" + File.separator + "repository" + File.separator + "colors_access.txt";

    public static boolean addUserToColorsFile(String userName) {
        File file = new File(ACCESS_FILE);

        if (!file.exists()) {
           //LoggerUtil.logInfo("Missing users access file");
            return false;
        }

        try (BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(file, true), "UTF-8"))) {
            writer.write(userName + "\n");
        } catch (IOException e) {
            //LoggerUtil.logError("Error adding user %s to colors access file: %s", e, userName);
            return false;
        }
        return true;
    }

    public static boolean hasColorsAccess(String playerName) {
        try (Scanner scanner = new Scanner(new InputStreamReader(new FileInputStream(ACCESS_FILE), "UTF-8"))) {
            while (scanner.hasNextLine()) {
                String line = scanner.nextLine();
                if (line.equals(playerName)) {
                    return true;
                }
            }
        } catch (IOException e) {
            //LoggerUtil.logError("Error reading colors access file: %s", e);
        }
        return false;
    }

}
