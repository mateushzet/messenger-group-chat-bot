package repository;

import java.io.*;
import java.text.SimpleDateFormat;
import java.util.*;

public class DailyRewardRepository {

    private static final String DATE_FORMAT = "yyyy-MM-dd";
    private static final String DAILY_REWARDS_FILE_PATH = "src" + File.separator + "repository" + File.separator + "dailyReward.txt";

    public static Map<String, String> getAllDailyRewards() {
        List<String> lines = readFile(DAILY_REWARDS_FILE_PATH);
        Map<String, String> userRewards = new HashMap<>();
        for (String line : lines) {
            String[] parts = line.split(": ");
            if (parts.length == 2) {
                String userName = parts[0].trim();
                String date = parts[1].trim();
                userRewards.put(userName, date);
            }
        }
        return userRewards;
    }

    public static boolean hasReceivedDailyReward(String userName) {
        Map<String, String> dailyRewards = getAllDailyRewards();
        String lastReceivedDate = dailyRewards.get(userName);
    
        if (lastReceivedDate == null) {
            //LoggerUtil.logInfo("User %s has no record of claiming daily rewards.", userName);
            return false;
        }
    
        String today = getCurrentDate();
        return today.equals(lastReceivedDate);
    }

    public static void updateDailyReward(String userName) {
        Map<String, String> dailyRewards = getAllDailyRewards();
        dailyRewards.put(userName, getCurrentDate());
        writeRewardsToFile(dailyRewards);

        //LoggerUtil.logInfo("Updated daily reward date for user: %s", userName);
    }

    private static String getCurrentDate() {
        SimpleDateFormat dateFormat = new SimpleDateFormat(DATE_FORMAT);
        return dateFormat.format(new Date());
    }

    private static List<String> readFile(String filePath) {
        List<String> lines = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(filePath), "UTF-8"))) {
            String line;
            while ((line = reader.readLine()) != null) {
                lines.add(line);
            }
        } catch (IOException e) {
            //LoggerUtil.logError("Error reading file: %s", e, filePath);
        }
        return lines;
    }

    private static void writeRewardsToFile(Map<String, String> userRewards) {
        try (BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(DAILY_REWARDS_FILE_PATH), "UTF-8"))) {
            for (Map.Entry<String, String> entry : userRewards.entrySet()) {
                writer.write(entry.getKey() + ": " + entry.getValue());
                writer.newLine();
            }
        } catch (IOException e) {
            //LoggerUtil.logError("Error writing rewards to file.", e);
        }
    }
}