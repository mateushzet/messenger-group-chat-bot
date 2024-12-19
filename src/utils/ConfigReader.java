package utils;

public class ConfigReader {

    public static String getUsername() {
        return System.getenv("USERNAME");
    }

    public static String getPassword() {
        return System.getenv("PASS");
    }

    public static String getWebDriverPath() {
        return "/webdriver"; 
    }

    public static boolean getMathQuestionRandomTime() {
        return true; 
    }

    public static String getMessageInputBoxCssSelector() {
        return "div[aria-label='Message']"; 
    }

    public static String getFirstCookiesButtonId() {
        return "allow_button"; 
    }

    public static String getSecondCookiesButtonXpath() {
        return "//span[text()='Allow all cookies']"; 
    }

    public static String getLoginInputId() {
        return "email"; 
    }

    public static String getPasswordInputId() {
        return "pass"; 
    }

    public static String getLoginButtonId() {
        return "loginbutton"; 
    }

    public static String getContinueLoginButtonCssSelector() {
        return "button[type='submit']:not([name='login'])"; 
    }

    public static String getBotCommand() {
        return "/bot"; 
    }

    public static String getMessageUserAvatarCssSelector() {
        return "img.x1rg5ohu"; 
    }

    public static String getMessageCssSelector() {
        return "div.xexx8yu.x4uap5.x18d9i69"; 
    }

    public static String getEmojiButtonCssSelector() {
        return "div[aria-label='Choose an emoji']"; 
    }

    public static String getSearchEmojiInputCssSelector() {
        return "input[aria-label='Search emoji']"; 
    }

    public static String getClearSearchEmojiButtonCssSelector() {
        return "div[aria-label='Clear search']"; 
    }

    public static String getMessageReceivedReactionsCssSelector() {
        return "div[aria-label*='see who reacted to this']"; 
    }

    public static String getMessageReceivedReactionsHeartCssSelector() {
        return "div[aria-label='1 reaction with ❤️; see who reacted to this'] img[alt='❤️']"; 
    }

    public static String getMessageReactButtonCssSelector() {
        return "div[aria-label='React']"; 
    }

    public static String getMessageHeartReactionCssSelector() {
        return "div[role='menuitem'] img[alt='❤']"; 
    }

    public static String getRedHeartEmojiUrl() {
        return "static.xx.fbcdn.net/images/emoji.php/v9/t38/1/30/1f5a4.png"; 
    }

    public static String getBlackHeartEmojiUrl() {
        return "static.xx.fbcdn.net/images/emoji.php/v9/t34/1/30/2764.png"; 
    }

    public static String getGreenHeartEmojiUrl() {
        return "static.xx.fbcdn.net/images/emoji.php/v9/tcc/1/30/1f49a.png"; 
    }

    public static String getHeartsEmojisName() {
        return "heart"; 
    }

    public static String getNumbersEmojisName() {
        return "number"; 
    }

    public static String getNumberEmojiUrl0() {
        return "https://static.xx.fbcdn.net/images/emoji.php/v9/t93/1/30/30_20e3.png"; 
    }

    public static String getNumberEmojiUrl1() {
        return "https://static.xx.fbcdn.net/images/emoji.php/v9/tb2/1/30/31_20e3.png"; 
    }

    public static String getNumberEmojiUrl2() {
        return "https://static.xx.fbcdn.net/images/emoji.php/v9/td1/1/30/32_20e3.png"; 
    }

    public static String getNumberEmojiUrl3() {
        return "https://static.xx.fbcdn.net/images/emoji.php/v9/tf0/1/30/33_20e3.png"; 
    }

    public static String getNumberEmojiUrl4() {
        return "https://static.xx.fbcdn.net/images/emoji.php/v9/tf/1/30/34_20e3.png"; 
    }

    public static String getNumberEmojiUrl5() {
        return "https://static.xx.fbcdn.net/images/emoji.php/v9/t2e/1/30/35_20e3.png"; 
    }

    public static String getNumberEmojiUrl6() {
        return "https://static.xx.fbcdn.net/images/emoji.php/v9/t4d/1/30/36_20e3.png"; 
    }

    public static String getNumberEmojiUrl7() {
        return "https://static.xx.fbcdn.net/images/emoji.php/v9/t6c/1/30/37_20e3.png"; 
    }

    public static String getNumberEmojiUrl8() {
        return "https://static.xx.fbcdn.net/images/emoji.php/v9/t8b/1/30/38_20e3.png"; 
    }

    public static String getNumberEmojiUrl9() {
        return "https://static.xx.fbcdn.net/images/emoji.php/v9/taa/1/30/39_20e3.png"; 
    }

    public static int getMathQuestionRandomStartMinute() {
        return 0; 
    }

    public static int getMathQuestionRandomEndMinute() {
        return 59; 
    }

    public static boolean getEnableManualLogin() {
        return false; 
    }
}