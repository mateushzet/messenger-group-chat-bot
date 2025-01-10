package utils;

import java.io.FileInputStream;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

public class ConfigReader {

    private static final Map<String, String> emojiUrls = new HashMap<>();

    static {
        emojiUrls.put("cherry", "https://static.xx.fbcdn.net/images/emoji.php/v9/t60/1/30/1f352.png");
        emojiUrls.put("lemon", "https://static.xx.fbcdn.net/images/emoji.php/v9/tf1/1/30/1f34b.png");
        emojiUrls.put("orange", "https://static.xx.fbcdn.net/images/emoji.php/v9/t70/1/30/1f34a.png");
        emojiUrls.put("lobster", "https://static.xx.fbcdn.net/images/emoji.php/v9/t15/1/30/1f99e.png");
        emojiUrls.put("watermelon", "https://static.xx.fbcdn.net/images/emoji.php/v9/t48/1/30/1f349.png");
        emojiUrls.put("apple", "https://static.xx.fbcdn.net/images/emoji.php/v9/t74/1/30/1f34e.png");
        emojiUrls.put("slot_machine", "https://static.xx.fbcdn.net/images/emoji.php/v9/t51/1/30/1f3b0.png");
        emojiUrls.put("red_heart", "https://static.xx.fbcdn.net/images/emoji.php/v9/t38/1/30/1f5a4.png");
        emojiUrls.put("black_heart", "https://static.xx.fbcdn.net/images/emoji.php/v9/t34/1/30/2764.png");
        emojiUrls.put("green_heart", "https://static.xx.fbcdn.net/images/emoji.php/v9/tcc/1/30/1f49a.png");
        emojiUrls.put("number_0", "https://static.xx.fbcdn.net/images/emoji.php/v9/t93/1/30/30_20e3.png");
        emojiUrls.put("number_1", "https://static.xx.fbcdn.net/images/emoji.php/v9/tb2/1/30/31_20e3.png");
        emojiUrls.put("number_2", "https://static.xx.fbcdn.net/images/emoji.php/v9/td1/1/30/32_20e3.png");
        emojiUrls.put("number_3", "https://static.xx.fbcdn.net/images/emoji.php/v9/tf0/1/30/33_20e3.png");
        emojiUrls.put("number_4", "https://static.xx.fbcdn.net/images/emoji.php/v9/tf/1/30/34_20e3.png");
        emojiUrls.put("number_5", "https://static.xx.fbcdn.net/images/emoji.php/v9/t2e/1/30/35_20e3.png");
        emojiUrls.put("number_6", "https://static.xx.fbcdn.net/images/emoji.php/v9/t4d/1/30/36_20e3.png");
        emojiUrls.put("number_7", "https://static.xx.fbcdn.net/images/emoji.php/v9/t6c/1/30/37_20e3.png");
        emojiUrls.put("number_8", "https://static.xx.fbcdn.net/images/emoji.php/v9/t8b/1/30/38_20e3.png");
        emojiUrls.put("number_9", "https://static.xx.fbcdn.net/images/emoji.php/v9/taa/1/30/39_20e3.png");
    }

    private static Properties properties;

    static {
        try {
            properties = loadProperties("/etc/secrets/config.properties");
            if (properties == null) {
                properties = loadProperties("src/resources/config.properties");
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static Properties loadProperties(String filePath) throws IOException {
        FileInputStream input = new FileInputStream(filePath);
        Properties props = new Properties();
        props.load(input);
        input.close();
        return props;
    }

    private static String getProperty(String key, String defaultValue) {
        String value = properties.getProperty(key);
        return (value != null && !value.isEmpty()) ? value : defaultValue;
    }

    private static int getPropertyInt(String key, int defaultValue) {
        String value = properties.getProperty(key);
        if (value != null && !value.isEmpty()) {
            try {
                return Integer.parseInt(value);
            } catch (NumberFormatException e) {
                Logger.logError("Invalid number format for %s: %s", "ConfigReader.getPropertyInt()", e, value, key);
            }
        }
        return defaultValue;
    }

    public static String getEmojiUrl(String emojiName) {
        String emojiUrl = properties.getProperty(emojiName + "_emoji_url");

        if (emojiUrl == null || emojiUrl.isEmpty()) {
            emojiUrl = emojiUrls.getOrDefault(emojiName, "");
        }

        return emojiUrl;
    }

    public static String getUsername() {
        return getProperty("username", "");
    }

    public static String getPassword() {
        return getProperty("password", "");
    }

    public static String getWebDriverPath() {
        return getProperty("webdriver.path", "");
    }

    public static boolean getMathQuestionRandomTime() {
        return Boolean.parseBoolean(getProperty("math_question_random_time", "false"));
    }

    public static String getMessageInputBoxCssSelector() {
        return getProperty("message_input_box_css_selector", "div[aria-label='Message']");
    }

    public static String getLoginInputId() {
        return getProperty("login_input_id", "email");
    }

    public static String getPasswordInputId() {
        return getProperty("password_input_id", "pass");
    }

    public static int getSlotsAccessCost() {
        return getPropertyInt("slots_access_cost", 200);
    }

    public static int getColorsAccessCost() {
        return getPropertyInt("colors_access_cost", 1000);
    }

    public static String getCherryEmojiUrl() {
        return getProperty("cherry_emoji_url", "https://static.xx.fbcdn.net/images/emoji.php/v9/t60/1/30/1f352.png");
    }

    public static String getLemonEmojiUrl() {
        return getProperty("lemon_emoji_url", "https://static.xx.fbcdn.net/images/emoji.php/v9/tf1/1/30/1f34b.png");
    }

    public static String getOrangeEmojiUrl() {
        return getProperty("orange_emoji_url", "https://static.xx.fbcdn.net/images/emoji.php/v9/t70/1/30/1f34a.png");
    }

    public static int getMathQuestionRandomStartMinute() {
        return getPropertyInt("math_question_random_start_minute", -1);
    }

    public static int getMathQuestionRandomEndMinute() {
        return getPropertyInt("math_question_random_end_minute", -1);
    }

    public static boolean getEnableManualLogin() {
        return Boolean.parseBoolean(getProperty("enable_manual_login", "false"));
    }

    public static int getMathQuestionPrize() {
        return getPropertyInt("math_question_prize", 10);
    }

    public static int getDailyRewardPrize() {
        return getPropertyInt("daily_reward_prize", 10);
    }

    public static String getFirstCookiesButtonId() {
        return getProperty("first_cookies_button_id", "allow_button");
    }

    public static String getSecondCookiesButtonXpath() {
        return getProperty("second_cookies_button_xpath", "//span[text()='Allow all cookies']");
    }

    public static String getGroupChatName() {
        return getProperty("group_chat_name", "name");
    }

    public static String getLoginButtonId() {
        return getProperty("login_button_id", "loginbutton");
    }

    public static String getContinueLoginButtonCssSelector() {
        return getProperty("continue_login_button_css_selector", "button[type='submit']:not([name='login'])");
    }

    public static String getBotCommand() {
        return getProperty("bot_command", "/bot");
    }

    public static String getMessageUserAvatarCssSelector() {
        return getProperty("message_user_avatar_css_selector", "img.x1rg5ohu");
    }

    public static String getMessageCssSelector() {
        return getProperty("message_css_selector", "div.xexx8yu.x4uap5.x18d9i69");
    }

    public static String getEmojiButtonCssSelector() {
        return getProperty("emoji_button_css_selector", "div[aria-label='Choose an emoji']");
    }

    public static String getSearchEmojiInputCssSelector() {
        return getProperty("search_emoji_input_css_selector", "input[aria-label='Search emoji']");
    }

    public static String getClearSearchEmojiButtonCssSelector() {
        return getProperty("clear_search_emoji_button_css_selector", "div[aria-label='Clear search']");
    }

    public static String getMessageReceivedReactionsCssSelector() {
        return getProperty("message_received_reactions_css_selector", "div[aria-label*='see who reacted to this']");
    }

    public static String getMessageReceivedReactionsHeartCssSelector() {
        return getProperty("message_received_reactions_heart_css_selector", "div[aria-label='1 reaction with ❤️; see who reacted to this'] img[alt='❤️']");
    }

    public static String getMessageReactButtonCssSelector() {
        return getProperty("message_react_button_css_selector", "div[aria-label='React']");
    }

    public static String getMessageHeartReactionCssSelector() {
        return getProperty("message_heart_reaction_css_selector", "div[role='menuitem'] img[alt='❤']");
    }

    public static String getHeartsEmojisName() {
        return getProperty("hearts_emojis_name", "heart");
    }

    public static String getNumbersEmojisName() {
        return getProperty("numbers_emojis_name", "number");
    }

}