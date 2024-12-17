package service;

import repository.UserRepository;
import utils.LoggerUtil;

import java.util.concurrent.ThreadLocalRandom;

import model.MathQuestion;
import utils.ConfigReader;

public class MathQuestionService {

    private static int lastHour = java.time.LocalTime.now().getHour(); // The last hour when the question was sent, change to -1 to trigger the question when runing the app. 
    private static boolean isQuestionSolved = true;
    private static String currentMathQuestion = "";
    private static int currentAnswer = 0;
    private static boolean mathQuestionRandomTime = ConfigReader.getMathQuestionRandomTime();
    private static int mathQuestionRandomMinuteStart = ConfigReader.getMathQuestionRandomStartMinute();
    private static int mathQuestionRandomMinuteEnd = ConfigReader.getMathQuestionRandomEndMinute();
    private static int mathQuestionRandomMinute = setRandomMinute();

    public static void handleMathAnswer(String answer, String userName) {
        if (!isQuestionSolved) {
            try {
                int userAnswer = Integer.parseInt(answer.trim());

                if (userAnswer == currentAnswer) {

                    isQuestionSolved = true;
                    rewardUser(userName);

                } else {
                    MessageService.sendMessage("%s incorrect answer!", userName);
                    LoggerUtil.logInfo("%s incorrect answer: %s", userName, answer);
                }
            } catch (NumberFormatException e) {
                MessageService.sendMessage("Invalid answer arguments!");
                LoggerUtil.logInfo("%s incorrect command: %s", userName, answer);
            }
        } else {
            MessageService.sendMessage("The last task was solved. Please wait for the next one.");
            LoggerUtil.logInfo("%s tried to solve old question: %s",userName, answer);
        }
    }

    public static void checkAndSendMathQuestion() {
        int currentHour = java.time.LocalTime.now().getHour();
        int currentMinute = java.time.LocalTime.now().getMinute();

        if (currentHour != lastHour && isQuestionSolved) {
            if (mathQuestionRandomTime) {
                // random minute
                if (currentMinute == mathQuestionRandomMinute) {
                    sendMathQuestion();
                    mathQuestionRandomMinute = setRandomMinute();
                    isQuestionSolved = false;
                    lastHour = currentHour;
                    LoggerUtil.logInfo("Math question sent at random minute: %d", currentMinute);
                }
            } else {
                // full hour
                sendMathQuestion();
                isQuestionSolved = false;
                lastHour = currentHour;
                LoggerUtil.logInfo("Math question sent on the hour: %d", currentHour);
            }
        }
    }

    private static void rewardUser(String userName) {
        int userBalance = UserRepository.getUserBalance(userName, true);
        UserRepository.updateUserBalance(userName, userBalance + 10);
        MessageService.sendMessage("%s correct answer! You earn 10 coins! Current balance: %d", userName, (userBalance + 10));
        LoggerUtil.logInfo("%s solved math question and earned 10 coins, previous balance: %d", userName, userBalance);
    }

    private static void sendMathQuestion(){
        MathQuestion question = new MathQuestion();
        currentMathQuestion = question.generateQuestion();
        currentAnswer = question.calculateAnswer();
        LoggerUtil.logInfo("Current math question: %s current answer: %d", currentMathQuestion, currentAnswer);

        isQuestionSolved = false;
        MessageService.sendMessage("Math question (/bot answer <number>): %s", currentMathQuestion);
        LoggerUtil.logInfo("Math question (/bot answer <number>): %s", currentMathQuestion);
    }

    public static int setRandomMinute() {
        if (mathQuestionRandomMinuteStart == -1 || mathQuestionRandomMinuteEnd == -1) {
            mathQuestionRandomMinuteStart = 0;
            mathQuestionRandomMinuteEnd = 59;
            LoggerUtil.logWarning("Random time math question: invalid time configuration. Set to 0-59 by default.");
        } else if (mathQuestionRandomMinuteStart >= mathQuestionRandomMinuteEnd) {

            LoggerUtil.logWarning("Invalid time configuration: start minute must be less than end minute. Set to 0-59 by default.");
            mathQuestionRandomMinuteStart = 0;
            mathQuestionRandomMinuteEnd = 59;
        }
        
        int randomMinute = ThreadLocalRandom.current().nextInt(mathQuestionRandomMinuteStart, mathQuestionRandomMinuteEnd);
        LoggerUtil.logInfo("Time range: %d - %d, random minute set to = %d", mathQuestionRandomMinuteStart, mathQuestionRandomMinuteEnd, randomMinute);
        return randomMinute;
    }
}