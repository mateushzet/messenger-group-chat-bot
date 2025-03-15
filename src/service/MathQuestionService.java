package service;

import repository.RewardsHistoryRepository;
import repository.UserRepository;
import utils.Logger;
import utils.MathQuestionImageGenerator;

import java.util.concurrent.ThreadLocalRandom;

import model.MathQuestion;
import utils.ConfigReader;

public class MathQuestionService {

    private static int lastHour = ConfigReader.getMathQuestionSkipFirstHourAfterRestart() ? java.time.LocalTime.now().getHour() : -1; // The last hour when the question was sent, -1 won't skip question when restarting the app. 
    private static boolean isQuestionSolved = true;
    private static String currentMathQuestion = "";
    private static int currentAnswer = 0;
    private static boolean mathQuestionRandomTime = ConfigReader.getMathQuestionRandomTime();
    private static int mathQuestionRandomMinuteStart = ConfigReader.getMathQuestionRandomStartMinute();
    private static int mathQuestionRandomMinuteEnd = ConfigReader.getMathQuestionRandomEndMinute();
    private static int mathQuestionRandomMinute = setRandomMinute();
    private static int mathQuestionPrize = ConfigReader.getMathQuestionPrize();

    public static void handleMathAnswer(String answer, String userName) {
        if (!isQuestionSolved) {
            try {
                int userAnswer = Integer.parseInt(answer.trim());

                if (userAnswer == currentAnswer) {

                    isQuestionSolved = true;
                    rewardUser(userName);

                } else {
                    MessageService.sendMessage("%s incorrect answer!", userName);
                    Logger.logInfo("%s incorrect answer: %s", "MathQuestionService.handleMathAnswer()", userName, answer);
                }
            } catch (NumberFormatException e) {
                MessageService.sendMessage("Invalid answer arguments!");
                Logger.logInfo("%s incorrect command: %s", "MathQuestionService.handleMathAnswer()", userName, answer);
            }
        } else {
            MessageService.sendMessage("The last task was solved. Please wait for the next one.");
            Logger.logInfo("%s tried to solve old question: %s", "MathQuestionService.handleMathAnswer()", userName, answer);
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
                    Logger.logInfo("Math question sent at random minute: %d", "MathQuestionService.checkAndSendMathQuestion()", currentMinute);
                }
            } else {
                // full hour
                sendMathQuestion();
                isQuestionSolved = false;
                lastHour = currentHour;
                Logger.logInfo("Math question sent on the hour: %d", "MathQuestionService.checkAndSendMathQuestion()", currentHour);
            }
        }
    }

    private static void rewardUser(String userName) {
        int userBalance = UserRepository.getCurrentUserBalance(userName, true);
        UserRepository.updateUserBalance(userName, userBalance + mathQuestionPrize);
        MessageService.sendMessage("%s correct answer! You earn %d coins! Current balance: %d", userName, mathQuestionPrize, (userBalance + mathQuestionPrize));
        Logger.logInfo("%s solved math question and earned %d coins, previous balance: %d", "MathQuestionService.rewardUser()", userName, mathQuestionPrize, userBalance);
        RewardsHistoryRepository.addRewardHistory(userName, "Answer", mathQuestionPrize);
    }

    private static void sendMathQuestion(){
        MathQuestion question = new MathQuestion();
        currentMathQuestion = question.generateQuestion();
        currentAnswer = question.calculateAnswer();
        Logger.logInfo("Current math question: %s current answer: %d", "MathQuestionService.sendMathQuestion()", currentMathQuestion, currentAnswer);
        isQuestionSolved = false;
        MathQuestionImageGenerator.generateMathQuestionImage(currentMathQuestion);
        MessageService.sendMessageFromClipboard(true);
    }

    public static int setRandomMinute() {
        if (mathQuestionRandomMinuteStart == -1 || mathQuestionRandomMinuteEnd == -1) {
            mathQuestionRandomMinuteStart = 0;
            mathQuestionRandomMinuteEnd = 59;
            Logger.logWarning("Random time math question: invalid time configuration. Set to 0-59 by default.", "MathQuestionService.setRandomMinute()");
        } else if (mathQuestionRandomMinuteStart >= mathQuestionRandomMinuteEnd) {

            Logger.logWarning("Invalid time configuration: start minute must be less than end minute. Set to 0-59 by default.", "MathQuestionService.setRandomMinute()");
            mathQuestionRandomMinuteStart = 0;
            mathQuestionRandomMinuteEnd = 59;
        }
        
        int randomMinute = ThreadLocalRandom.current().nextInt(mathQuestionRandomMinuteStart, mathQuestionRandomMinuteEnd);
        Logger.logInfo("Time range: %d - %d, random minute set to = %d", "MathQuestionService.setRandomMinute()", mathQuestionRandomMinuteStart, mathQuestionRandomMinuteEnd, randomMinute);
        return randomMinute;
    }
}