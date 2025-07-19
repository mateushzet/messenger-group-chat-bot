package service;

import repository.RewardsHistoryRepository;
import repository.UserRepository;
import utils.Logger;
import utils.MathQuestionImageGenerator;
import utils.RewardGifGenerator;

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
    private static boolean isRandomPrizeEnabled = ConfigReader.isMathQuestionRandomPrizeEnabled();
    private static int randomPrizeMin = ConfigReader.getMathQuestionRandomPrizeMinCap();
    private static int randomPrizeMax = ConfigReader.getMathQuestionRandomPrizeMaxCap();
    private static boolean lowerChanceForUpperHalf = ConfigReader.isLowerChanceForUpperHalfEnabled();


    public static void handleMathAnswer(String answer, String userName) {
        if (!isQuestionSolved) {
            try {
                int userAnswer = Integer.parseInt(answer.trim());

                if (userAnswer == currentAnswer) {

                    isQuestionSolved = true;
                    rewardUser(userName);

                } else {
                    MessageService.sendMessage(userName + " incorrect answer!");
                    Logger.logInfo(userName + " incorrect answer: " + answer, "MathQuestionService.handleMathAnswer()");
                }
            } catch (NumberFormatException e) {
                MessageService.sendMessage("Invalid answer arguments!");
                Logger.logInfo(userName + " incorrect command: " + answer, "MathQuestionService.handleMathAnswer()");
            }
        } else {
            MessageService.sendMessage("The last task was solved. Please wait for the next one.");
            Logger.logInfo(userName + " tried to solve old question: " + answer, "MathQuestionService.handleMathAnswer()");
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
                    Logger.logInfo("Math question sent at random minute: " + currentMinute, "MathQuestionService.checkAndSendMathQuestion()");
                }
            } else {
                // full hour
                sendMathQuestion();
                isQuestionSolved = false;
                lastHour = currentHour;
                Logger.logInfo("Math question sent on the hour: " + currentHour, "MathQuestionService.checkAndSendMathQuestion()");
            }
        }
    }

    private static void rewardUser(String userName) {
        int reward;

        if (isRandomPrizeEnabled) {
            if (lowerChanceForUpperHalf) {
                double biased = Math.pow(Math.random(), 2);
                reward = randomPrizeMin + (int) (biased * (randomPrizeMax - randomPrizeMin + 1));
            } else {
                reward = randomPrizeMin + (int) (Math.random() * (randomPrizeMax - randomPrizeMin + 1));
            }

            reward = (reward / 10) * 10;

            if (reward < randomPrizeMin) {
                reward = randomPrizeMin + (10 - randomPrizeMin % 10) % 10;
            }
            
        } else {
            reward = mathQuestionPrize;
        }

        int userBalance = UserRepository.getCurrentUserBalance(userName, true);
        int newBalance = userBalance + reward;

        if(isRandomPrizeEnabled){
            RewardGifGenerator.generateGif(reward, userName, newBalance, randomPrizeMin, randomPrizeMax);
            MessageService.sendMessageFromClipboardWindows(true);
        } else {
            MessageService.sendMessage(userName + " correct answer! You earn *" + reward + "* coins! Current balance: " + newBalance);
        }
        UserRepository.updateUserBalance(userName, newBalance);

        Logger.logInfo(userName + " solved math question and earned " + reward + " coins, previous balance: " + userBalance, "MathQuestionService.rewardUser()");
        RewardsHistoryRepository.addRewardHistory(userName, "Answer", reward);
    }

    private static void sendMathQuestion(){
        MathQuestion question = new MathQuestion();
        currentMathQuestion = question.generateQuestion();
        currentAnswer = question.calculateAnswer();
        Logger.logInfo("Current math question: " + currentMathQuestion + " current answer: " + currentAnswer, "MathQuestionService.sendMathQuestion()");
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
        Logger.logInfo("Time range: " + mathQuestionRandomMinuteStart + " - " + mathQuestionRandomMinuteEnd + ", random minute set to = " + randomMinute, "MathQuestionService.setRandomMinute()");
        return randomMinute;
    }
}