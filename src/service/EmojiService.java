package service;

import utils.ConfigReader;

import java.util.Map;

public class EmojiService {

    private static final Map<Integer, String> colorEmojiMap = Map.of(
        0, ConfigReader.getEmojiUrl("red_heart"),
        1, ConfigReader.getEmojiUrl("black_heart"),
        2, ConfigReader.getEmojiUrl("green_heart")
    );

    private static final String[] numberEmojiUrls = {
        ConfigReader.getEmojiUrl("number_0"),
        ConfigReader.getEmojiUrl("number_1"),
        ConfigReader.getEmojiUrl("number_2"),
        ConfigReader.getEmojiUrl("number_3"),
        ConfigReader.getEmojiUrl("number_4"),
        ConfigReader.getEmojiUrl("number_5"),
        ConfigReader.getEmojiUrl("number_6"),
        ConfigReader.getEmojiUrl("number_7"),
        ConfigReader.getEmojiUrl("number_8"),
        ConfigReader.getEmojiUrl("number_9")
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