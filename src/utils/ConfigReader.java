package utils;

import java.io.FileInputStream;
import java.io.IOException;
import java.util.Properties;

public class ConfigReader {

    private static Properties properties;

    static {
        try {
            FileInputStream input = new FileInputStream("/etc/secrets/config.propertis");
            properties = new Properties();
            properties.load(input);
            input.close();
        } catch (IOException e) {
    
            try {
                FileInputStream input = new FileInputStream("src/resources/config.properties");
                properties = new Properties();
                properties.load(input);
                input.close();
            } catch (IOException ex) {
            }
        }
    }

    public static String getUsername() {
        return properties.getProperty("username");
    }

    public static String getPassword() {
        return properties.getProperty("password");
    }

    public static String getWebDriverPath() {
        return properties.getProperty("webdriver.path");
    }

    public static boolean getMathQuestionRandomTime() {
        String mathQuestionRandomTime = properties.getProperty("math_question_random_time");
        
        return mathQuestionRandomTime != null && mathQuestionRandomTime.equalsIgnoreCase("true");
    }

    public static String getMessageInputBoxCssSelector() {
        String messageInputBoxCssSelector = properties.getProperty("message_input_box_css_selector");
        return (messageInputBoxCssSelector != null && !messageInputBoxCssSelector.isEmpty())
                ? messageInputBoxCssSelector
                : "div[aria-label='Message']";
    }

    public static String getFirstCookiesButtonId() {
        String firstCookiesButtonId = properties.getProperty("first_cookies_button_id");
        return (firstCookiesButtonId != null && !firstCookiesButtonId.isEmpty())
                ? firstCookiesButtonId
                : "allow_button";
    }

    public static String getSecondCookiesButtonXpath() {
        String secondCookiesButtonXpath = properties.getProperty("second_cookies_button_xpath");
        return (secondCookiesButtonXpath != null && !secondCookiesButtonXpath.isEmpty())
                ? secondCookiesButtonXpath
                : "//span[text()='Allow all cookies']";
    }

    public static String getLoginInputId() {
        String loginInputId = properties.getProperty("login_input_id");
        return (loginInputId != null && !loginInputId.isEmpty())
                ? loginInputId
                : "email";
    }

    public static String getPasswordInputId() {
        String passwordInputId = properties.getProperty("password_input_id");
        return (passwordInputId != null && !passwordInputId.isEmpty())
                ? passwordInputId
                : "pass";
    }

    public static String getGroupChatName() {
        String groupChatName = properties.getProperty("group_chat_name");
        return (groupChatName != null && !groupChatName.isEmpty())
                ? groupChatName
                : "name";
    }

    public static String getLoginButtonId() {
        String loginButtonId = properties.getProperty("login_button_id");
        return (loginButtonId != null && !loginButtonId.isEmpty())
                ? loginButtonId
                : "loginbutton";
    }

    public static String getContinueLoginButtonCssSelector() {
        String continueLoginButtonCssSelector = properties.getProperty("continue_login_button_css_selector");
        return (continueLoginButtonCssSelector != null && !continueLoginButtonCssSelector.isEmpty())
                ? continueLoginButtonCssSelector
                : "button[type='submit']:not([name='login'])";
    }
    
    public static String getBotCommand() {
        String botCommand = properties.getProperty("bot_command");
        return (botCommand != null && !botCommand.isEmpty())
                ? botCommand
                : "/bot";
    }

    public static String getMessageUserAvatarCssSelector() {
        String messageUserAvatarCssSelector = properties.getProperty("message_user_avatar_css_selector");
        return (messageUserAvatarCssSelector != null && !messageUserAvatarCssSelector.isEmpty())
                ? messageUserAvatarCssSelector
                : "img.x1rg5ohu";
    }

    public static String getMessageCssSelector() {
        String messageCssSelector = properties.getProperty("message_css_selector");
        return (messageCssSelector != null && !messageCssSelector.isEmpty())
                ? messageCssSelector
                : "div.xexx8yu.x4uap5.x18d9i69";
    }
    
    public static String getEmojiButtonCssSelector() {
        String emojiButtonCssSelector = properties.getProperty("emoji_button_css_selector");
        return (emojiButtonCssSelector != null && !emojiButtonCssSelector.isEmpty())
                ? emojiButtonCssSelector
                : "div[aria-label='Choose an emoji']";
    }

    public static String getSearchEmojiInputCssSelector() {
        String searchEmojiInputCssSelector = properties.getProperty("search_emoji_input_css_selector");
        return (searchEmojiInputCssSelector != null && !searchEmojiInputCssSelector.isEmpty())
                ? searchEmojiInputCssSelector
                : "input[aria-label='Search emoji']";
    }

    public static String getClearSearchEmojiButtonCssSelector() {
        String clearSearchEmojiButtonCssSelector = properties.getProperty("clear_search_emoji_button_css_selector");
        return (clearSearchEmojiButtonCssSelector != null && !clearSearchEmojiButtonCssSelector.isEmpty())
                ? clearSearchEmojiButtonCssSelector
                : "div[aria-label='Clear search']";
    }

    public static String getMessageReceivedReactionsCssSelector() {
        String messageReceivedReactionsCssSelector = properties.getProperty("message_received_reactions_css_selector");
        return (messageReceivedReactionsCssSelector != null && !messageReceivedReactionsCssSelector.isEmpty())
                ? messageReceivedReactionsCssSelector
                : "div[aria-label*='see who reacted to this']";
    }

    public static String getMessageReceivedReactionsHeartCssSelector() {
        String messageReceivedReactionsHeartCssSelector = properties.getProperty("message_received_reactions_heart_css_selector");
        return (messageReceivedReactionsHeartCssSelector != null && !messageReceivedReactionsHeartCssSelector.isEmpty())
                ? messageReceivedReactionsHeartCssSelector
                : "div[aria-label='1 reaction with ❤️; see who reacted to this'] img[alt='❤️']";
    }

    public static String getMessageReactButtonCssSelector() {
        String messageReactButtonCssSelector = properties.getProperty("message_react_button_css_selector");
        return (messageReactButtonCssSelector != null && !messageReactButtonCssSelector.isEmpty())
                ? messageReactButtonCssSelector
                : "div[aria-label='React']";
    }

    public static String getMessageHeartReactionCssSelector() {
        String messageReceivedReactionsHeartCssSelector = properties.getProperty("message_heart_reaction_css_selector");
        return (messageReceivedReactionsHeartCssSelector != null && !messageReceivedReactionsHeartCssSelector.isEmpty())
                ? messageReceivedReactionsHeartCssSelector
                : "div[role='menuitem'] img[alt='❤']";
    }

    public static String getRedHeartEmojiUrl() {
        String redHeartEmojiUrl = properties.getProperty("red_heart_emoji_url");
        return (redHeartEmojiUrl != null && !redHeartEmojiUrl.isEmpty())
                ? redHeartEmojiUrl
                : "static.xx.fbcdn.net/images/emoji.php/v9/t38/1/30/1f5a4.png";
    }

    public static String getBlackHeartEmojiUrl() {
        String blackHeartEmojiUrl = properties.getProperty("black_heart_emoji_url");
        return (blackHeartEmojiUrl != null && !blackHeartEmojiUrl.isEmpty())
                ? blackHeartEmojiUrl
                : "static.xx.fbcdn.net/images/emoji.php/v9/t34/1/30/2764.png";
    }

    public static String getGreenHeartEmojiUrl() {
        String greenHeartEmojiUrl = properties.getProperty("green_heart_emoji_url");
        return (greenHeartEmojiUrl != null && !greenHeartEmojiUrl.isEmpty())
                ? greenHeartEmojiUrl
                : "static.xx.fbcdn.net/images/emoji.php/v9/tcc/1/30/1f49a.png";
    }

    public static String getHeartsEmojisName() {
        String heartsEmojisName = properties.getProperty("hearts_emojis_name");
        return (heartsEmojisName != null && !heartsEmojisName.isEmpty())
                ? heartsEmojisName
                : "heart";
    }

    public static String getNumbersEmojisName() {
        String numbersEmojisName = properties.getProperty("numbers_emojis_name");
        return (numbersEmojisName != null && !numbersEmojisName.isEmpty())
                ? numbersEmojisName
                : "number";
    }

    public static String getNumberEmojiUrl0() {
        String numberEmojiUrl0 = properties.getProperty("number_emoji_url_0");
        return (numberEmojiUrl0 != null && !numberEmojiUrl0.isEmpty())
                ? numberEmojiUrl0
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/t93/1/30/30_20e3.png";
    }
    
    public static String getNumberEmojiUrl1() {
        String numberEmojiUrl1 = properties.getProperty("number_emoji_url_1");
        return (numberEmojiUrl1 != null && !numberEmojiUrl1.isEmpty())
                ? numberEmojiUrl1
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/tb2/1/30/31_20e3.png";
    }
    
    public static String getNumberEmojiUrl2() {
        String numberEmojiUrl2 = properties.getProperty("number_emoji_url_2");
        return (numberEmojiUrl2 != null && !numberEmojiUrl2.isEmpty())
                ? numberEmojiUrl2
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/td1/1/30/32_20e3.png";
    }
    
    public static String getNumberEmojiUrl3() {
        String numberEmojiUrl3 = properties.getProperty("number_emoji_url_3");
        return (numberEmojiUrl3 != null && !numberEmojiUrl3.isEmpty())
                ? numberEmojiUrl3
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/tf0/1/30/33_20e3.png";
    }
    
    public static String getNumberEmojiUrl4() {
        String numberEmojiUrl4 = properties.getProperty("number_emoji_url_4");
        return (numberEmojiUrl4 != null && !numberEmojiUrl4.isEmpty())
                ? numberEmojiUrl4
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/tf/1/30/34_20e3.png";
    }
    
    public static String getNumberEmojiUrl5() {
        String numberEmojiUrl5 = properties.getProperty("number_emoji_url_5");
        return (numberEmojiUrl5 != null && !numberEmojiUrl5.isEmpty())
                ? numberEmojiUrl5
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/t2e/1/30/35_20e3.png";
    }
    
    public static String getNumberEmojiUrl6() {
        String numberEmojiUrl6 = properties.getProperty("number_emoji_url_6");
        return (numberEmojiUrl6 != null && !numberEmojiUrl6.isEmpty())
                ? numberEmojiUrl6
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/t4d/1/30/36_20e3.png";
    }
    
    public static String getNumberEmojiUrl7() {
        String numberEmojiUrl7 = properties.getProperty("number_emoji_url_7");
        return (numberEmojiUrl7 != null && !numberEmojiUrl7.isEmpty())
                ? numberEmojiUrl7
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/t6c/1/30/37_20e3.png";
    }
    
    public static String getNumberEmojiUrl8() {
        String numberEmojiUrl8 = properties.getProperty("number_emoji_url_8");
        return (numberEmojiUrl8 != null && !numberEmojiUrl8.isEmpty())
                ? numberEmojiUrl8
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/t8b/1/30/38_20e3.png";
    }
    
    public static String getNumberEmojiUrl9() {
        String numberEmojiUrl9 = properties.getProperty("number_emoji_url_9");
        return (numberEmojiUrl9 != null && !numberEmojiUrl9.isEmpty())
                ? numberEmojiUrl9
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/taa/1/30/39_20e3.png";
    }

    public static int getMathQuestionRandomStartMinute() {
        String startMinute = properties.getProperty("math_question_random_start_minute");
        if (startMinute != null && !startMinute.isEmpty()) {
            try {
                int value = Integer.parseInt(startMinute);
    
                if (value < 0 || value > 59) {
                    LoggerUtil.logWarning("Invalid value for math_question_random_start_minute: %s. It should be between 0 and 59.", startMinute);
                }
    
                return value;
            } catch (NumberFormatException e) {
                LoggerUtil.logError("Invalid format for math_question_random_start_minute: %s", e, startMinute);
            }
        }
        return -1;
    }
    
    public static int getMathQuestionRandomEndMinute() {
        String endMinute = properties.getProperty("math_question_random_end_minute");
        if (endMinute != null && !endMinute.isEmpty()) {
            try {
                int value = Integer.parseInt(endMinute);
    
                if (value < 0 || value > 59) {
                    LoggerUtil.logWarning("Invalid value for math_question_random_end_minute: %s. It should be between 0 and 59.", endMinute);
                    return -1;
                }
    
                return value;
            } catch (NumberFormatException e) {
                LoggerUtil.logError("Invalid format for math_question_random_end_minute: %s", e, endMinute);
            }
        }
        return -1;
    }

    public static boolean getEnableManualLogin() {
        String enableManualLogin = properties.getProperty("enable_manual_login");
        
        return enableManualLogin != null && enableManualLogin.equalsIgnoreCase("true");
    }

    public static int getSlotsAccessCost() {
        String slotsAccessCost = properties.getProperty("slots_access_cost");
        if (slotsAccessCost != null && !slotsAccessCost.isEmpty()) {
            try {
                return Integer.parseInt(slotsAccessCost);
            } catch (NumberFormatException e) {
                LoggerUtil.logError("Invalid slots access cost: %s. Using default value of 500.", e, slotsAccessCost);
            }
        }
        return 200;
    }

    public static int getColorsAccessCost() {
        String colorsAccessCost = properties.getProperty("colors_access_cost");
        if (colorsAccessCost != null && !colorsAccessCost.isEmpty()) {
            try {
                return Integer.parseInt(colorsAccessCost);
            } catch (NumberFormatException e) {
                LoggerUtil.logError("Invalid colors access cost: %s. Using default value of 500.", e, colorsAccessCost);
            }
        }
        return 1000;
    }

    public static String getCherryEmojiUrl() {
        String cherryEmojiUrl = properties.getProperty("cherry_emoji_url");
        return (cherryEmojiUrl != null && !cherryEmojiUrl.isEmpty())
                ? cherryEmojiUrl
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/t60/1/30/1f352.png";
    }
    
    public static String getLemonEmojiUrl() {
        String lemonEmojiUrl = properties.getProperty("lemon_emoji_url");
        return (lemonEmojiUrl != null && !lemonEmojiUrl.isEmpty())
                ? lemonEmojiUrl
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/tf1/1/30/1f34b.png";
    }
    
    public static String getOrangeEmojiUrl() {
        String orangeEmojiUrl = properties.getProperty("orange_emoji_url");
        return (orangeEmojiUrl != null && !orangeEmojiUrl.isEmpty())
                ? orangeEmojiUrl
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/t70/1/30/1f34a.png";
    }
    
    public static String getLobsterEmojiUrl() {
        String lobsterEmojiUrl = properties.getProperty("lobster_emoji_url");
        return (lobsterEmojiUrl != null && !lobsterEmojiUrl.isEmpty())
                ? lobsterEmojiUrl
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/t15/1/30/1f99e.png";
    }
    
    public static String getWatermelonEmojiUrl() {
        String watermelonEmojiUrl = properties.getProperty("watermelon_emoji_url");
        return (watermelonEmojiUrl != null && !watermelonEmojiUrl.isEmpty())
                ? watermelonEmojiUrl
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/t48/1/30/1f349.png";
    }
    
    public static String getAppleEmojiUrl() {
        String appleEmojiUrl = properties.getProperty("apple_emoji_url");
        return (appleEmojiUrl != null && !appleEmojiUrl.isEmpty())
                ? appleEmojiUrl
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/t74/1/30/1f34e.png";
    }
    
    public static String getSlotMachineEmojiUrl() {
        String slotMachineEmojiUrl = properties.getProperty("slot_machine_emoji_url");
        return (slotMachineEmojiUrl != null && !slotMachineEmojiUrl.isEmpty())
                ? slotMachineEmojiUrl
                : "https://static.xx.fbcdn.net/images/emoji.php/v9/t51/1/30/1f3b0.png";
    }
    
    
    public static int getMathQuestionPrize() {
        String mathQuestionPrize = properties.getProperty("math_question_prize");
        if (mathQuestionPrize != null && !mathQuestionPrize.isEmpty()) {
            try {
                int value = Integer.parseInt(mathQuestionPrize);
                
                if (value <= 0) {
                    LoggerUtil.logWarning("Value for math_question_prize must be greater than zero: %s", mathQuestionPrize);
                }
    
                return value;
            } catch (NumberFormatException e) {
                LoggerUtil.logError("Invalid format for math_question_prize: %s", e, mathQuestionPrize);
            }
        }
        return 10;
    }
    
    public static int getDailyRewardPrize() {
        String dailyRewardPrize = properties.getProperty("daily_reward_prize");
        if (dailyRewardPrize != null && !dailyRewardPrize.isEmpty()) {
            try {
                int value = Integer.parseInt(dailyRewardPrize);
                
                if (value <= 0) {
                    LoggerUtil.logWarning("Value for daily_reward_prize must be greater than zero: %s", dailyRewardPrize);
                }
    
                return value;
            } catch (NumberFormatException e) {
                LoggerUtil.logError("Invalid format for daily_reward_prize: %s", e, dailyRewardPrize);
            }
        }
        return 10;
    }

}
