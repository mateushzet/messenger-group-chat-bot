package service;

import utils.ConfigReader;

import java.util.Map;

public class EmojiService {

    private static final Map<Integer, String> colorEmojiMap = Map.of(
        0, ConfigReader.getRedHeartEmojiUrl(),
        1, ConfigReader.getBlackHeartEmojiUrl(),
        2, ConfigReader.getGreenHeartEmojiUrl()
    );

    private static final String[] numberEmojiUrls = {
        ConfigReader.getNumberEmojiUrl0(),
        ConfigReader.getNumberEmojiUrl1(),
        ConfigReader.getNumberEmojiUrl2(),
        ConfigReader.getNumberEmojiUrl3(),
        ConfigReader.getNumberEmojiUrl4(),
        ConfigReader.getNumberEmojiUrl5(),
        ConfigReader.getNumberEmojiUrl6(),
        ConfigReader.getNumberEmojiUrl7(),
        ConfigReader.getNumberEmojiUrl8(),
        ConfigReader.getNumberEmojiUrl9()
    };

    public static void sendRouletteResultEmojis(int randomNumber) {
        String heartEmoji = colorEmojiMap.get(getRouletteColorNumber(randomNumber));
        MessageService.clickEmoji(heartEmoji, ConfigReader.getHeartsEmojisName());

        if (randomNumber >= 10) {
            int tens = randomNumber / 10;
            int ones = randomNumber % 10;
            MessageService.clickEmoji(numberEmojiUrls[tens], ConfigReader.getNumbersEmojisName());
            MessageService.clickEmoji(numberEmojiUrls[ones], ConfigReader.getNumbersEmojisName());
        } else {
            MessageService.clickEmoji(numberEmojiUrls[randomNumber], ConfigReader.getNumbersEmojisName());
        }
    }

    public static String getRouletteColorEmoji(int colorNumber) {
        return colorEmojiMap.get(colorNumber);
    }

    private static int getRouletteColorNumber(int number) {
        return number == 0 ? 2 : number % 2; // 0 = black, 1 = red, 2 = green
    }
}