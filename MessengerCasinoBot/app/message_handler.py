import os
import time
from datetime import datetime as dt
from utils import take_error_screenshot
from utils import take_info_screenshot
from auth import MessengerAuth
from logger import logger
from collections import deque

last_message_time = None

recent_messages = deque(maxlen=20)
MESSAGES_THRESHOLD = 2
TIME_WINDOW = 8

BASE_DIR = os.path.dirname(__file__)
TEMP_DIR = os.path.join(BASE_DIR, "temp")

def add_to_message_history(username):
    recent_messages.append((dt.now(), username))

def is_user_spamming(username):
    now = dt.now()
    
    count = 0
    for timestamp, user in recent_messages:
        if user == username and (now - timestamp).total_seconds() <= TIME_WINDOW:
            count += 1
    
    return count >= MESSAGES_THRESHOLD

def update_last_message_time():
    global last_message_time
    last_message_time = dt.now()

def get_sleep_time():
    global last_message_time
    
    if last_message_time is None:
        update_last_message_time()
        return 3
    
    now = dt.now()
    minutes_since_last = (now - last_message_time).total_seconds() / 60
    
    if minutes_since_last < 2:
        return 0
    if minutes_since_last < 5:
        return 1
    elif minutes_since_last < 30:
        return 3
    elif minutes_since_last < 60:
        return 5
    elif minutes_since_last < 120:
        return 10
    elif minutes_since_last < 180:
        return 15
    elif minutes_since_last < 240:
        return 20
    elif minutes_since_last < 360:
        return 25
    elif minutes_since_last < 480:
        return 30
    elif minutes_since_last < 720:
        return 60
    elif minutes_since_last < 1200:
        return 180
    else:
        return 200

def close_message_remove_popup(page):
    try:
        close_btn = page.query_selector("div[aria-label='Close']")
        if close_btn:
            close_btn.click(force=True)
    except Exception as e:
        logger.warning(f"[MessageHandler] Error closing popup: {e}")

def click_menu_option(page, row, label):
    try:
        row.hover(position={"x": 0, "y": 0})
        more_btn = row.wait_for_selector("div[aria-label='More']", timeout=1000)
        if more_btn:
            more_btn.click(force=True)
            time.sleep(0.01)
            menu_btn = page.wait_for_selector(f"div[aria-label='{label}'][role='menuitem']", timeout=1000)
            if menu_btn:
                menu_btn.click(force=True)
                time.sleep(0.01)
                return True
    except Exception as e:
        logger.info(f"[MessageHandler] Error clicking menu option '{label}'")
        close_message_remove_popup(page)
    return False

def add_reaction_to_message(page, row):
    try:
        row.hover(position={"x": 0, "y": 0})
        react_btn = row.wait_for_selector("div[aria-label='React']", timeout=1000)
        if react_btn:
            react_btn.click(force=True)
            time.sleep(0.01)
            heart = page.wait_for_selector("img[alt='❤']", timeout=1000)
            if heart:
                heart.click(force=True)
                time.sleep(0.01)
                return True
    except Exception as e:
        logger.info(f"[MessageHandler] Error adding heart reaction")
        take_error_screenshot(page,"adding_reaction")
        close_message_remove_popup(page)
    return False


def add_angry_reaction_to_message(page, row):
    try:
        row.hover(position={"x": 0, "y": 0})
        react_btn = row.wait_for_selector("div[aria-label='React']", timeout=1000)
        if react_btn:
            react_btn.click(force=True)
            time.sleep(0.01)
            angry = page.wait_for_selector("img[alt='😡']", timeout=1000)
            if angry:
                angry.click(force=True)
                time.sleep(0.01)
                return True
    except Exception as e:
        logger.info(f"[MessageHandler] Error adding angry reaction")
        take_error_screenshot(page,"adding_reaction")
        close_message_remove_popup(page)
    return False

def remove_message(page, row, sender_name):
    try:
        if click_menu_option(page, row, "Remove message"):
            confirm = page.wait_for_selector("div[aria-label='Remove']", timeout=1000)
            if confirm:
                confirm.click(force=True)
                return True
    except Exception as e:
        logger.warning(f"[MessageHandler] Error removing message from '{sender_name}': {e}")
        take_error_screenshot(page,"removing_message")
        close_message_remove_popup(page)
    return False

def unsend_message(page, row, sender_name):
    try:
        if click_menu_option(page, row, "Unsend message"):
            radio = page.wait_for_selector("input[type='radio'][value='1']", timeout=1000)
            if radio:
                radio.click(force=True)
                time.sleep(0.01)
                remove_button = page.wait_for_selector(
                    'xpath=//div[@aria-label="Remove" and @role="button"]', timeout=1000
                )
                if remove_button:
                    remove_button.click(force=True)
                    time.sleep(0.01)
                    return True
    except Exception as e:
        logger.warning(f"[MessageHandler] Error unsending message from '{sender_name}': {e}")
        take_error_screenshot(page,"unsending_message")
        close_message_remove_popup(page)
    return False

def fill_unknown_senders(messages):
    last_known_sender = None
    last_known_avatar = None
    for i in reversed(range(len(messages))):
        current_msg = messages[i]
        if current_msg["sender"] == "Unknown":
            if last_known_sender:
                current_msg["sender"] = last_known_sender
                if last_known_avatar:
                    current_msg["avatar_url"] = last_known_avatar
        else:
            last_known_sender = current_msg["sender"]
            last_known_avatar = current_msg["avatar_url"]

def extract_messages_fix_unknown_sender(page, command_queue):
    def collect_messages():
        rows_local = page.query_selector_all("div[role='row']")
        messages_local = []
        for idx, row in enumerate(rows_local):
            try:
                gridcell = row.query_selector("div[role='gridcell']")
                if not gridcell:
                    continue
                if row.get_attribute("class") is None or row.get_attribute("class") == "x9f619 x1n2onr6 x1ja2u2z":
                    continue
                
                you_sent_element = row.query_selector('span:has-text("You sent")')
                
                has_reaction = bool(row.query_selector('div[aria-label*="Like"][role="img"], div[aria-label*="Thumbs up"][role="img"]'))
                has_reaction_svg = bool(row.query_selector('svg title[id*="_r_a"]'))
                
                message_el = gridcell.query_selector("div[dir='auto']")
                message_text = message_el.inner_text().strip() if message_el else ""

                img_elements = row.query_selector_all('img[alt^=""]')
                emoji_imgs = []
                for img in img_elements:
                    try:
                        src = img.get_attribute('src')
                        if src and src.startswith('https://static.xx.fbcdn.net/images/emoji.php'):
                            emoji_imgs.append(img)
                    except:
                        pass
                
                if message_text == "":
                    if has_reaction or has_reaction_svg:
                        message_text = "reaction"
                    elif you_sent_element or emoji_imgs:
                        message_text = "emoji_or_special"
                    else:
                        aria_label = row.get_attribute("aria-label")
                        if aria_label:
                            aria_label_lower = aria_label.lower()
                            if any(word in aria_label_lower for word in ["like", "thumbs", "reaction", "emoji"]):
                                message_text = "reaction"

                if message_text == "Enter":
                    continue
                    
                avatar = row.query_selector("img.x1rg5ohu, [role='row'] img")
                row_text = row.inner_text().lower()
                contains_you_sent = "you sent" in row_text
                avatar_url = None
                if avatar:
                    sender_name = avatar.get_attribute("alt")
                    avatar_url = avatar.get_attribute("src")
                elif contains_you_sent:
                    sender_name = "You"
                else:
                    sender_name = "Unknown"
                    
                messages_local.append({
                    "row": row,
                    "sender": sender_name,
                    "message": message_text,
                    "timestamp": dt.now().isoformat(),
                    "avatar_url": avatar_url,
                    "contains_emoji": len(emoji_imgs) > 0,
                    "has_you_sent": contains_you_sent,
                    "has_reaction": has_reaction or has_reaction_svg
                })
            except Exception as e:
                logger.warning(f"[MessageHandler] Error during message extraction: {e}")
                take_error_screenshot(page, "message_extraction")
        fill_unknown_senders(messages_local)
        return messages_local

    messages = collect_messages()
    for idx, message in enumerate(messages):
        sender_name = message["sender"]
        message_text = message["message"]
        row = message["row"]
        is_command_message = message_text.startswith('/')
        page.mouse.move(0, 0)

        if sender_name == "Open photo":
            unsend_message(page, row, sender_name)

        elif sender_name == "Unknown":
            if is_command_message:
                retry_messages = collect_messages()
                for m in retry_messages:
                    if m["message"] == message_text:
                        if m["sender"] != "Unknown":
                            if is_user_spamming(sender_name):
                                if add_angry_reaction_to_message(page, row):
                                    if remove_message(page, row, sender_name):
                                        logger.warning(f"[AntiSpam] Removed spam message from {sender_name}")
                                        add_to_message_history(sender_name)
                                continue
                            if add_reaction_to_message(page, m["row"]):
                                if remove_message(page, m["row"], m["sender"]):
                                    command_queue.put(m)
                                    add_to_message_history(sender_name)
                                    update_last_message_time()
                                    logger.info(f"[MessageHandler] Message queued: '{sender_name}' - '{message_text}'")
                        break
            else:
                remove_message(page, row, sender_name)

        elif sender_name == "You":
            # Usuń reakcje, emoji i specjalne wiadomości
            if message_text == "reaction" or message["has_reaction"]:
                if unsend_message(page, row, sender_name):
                    logger.info(f"[MessageHandler] Removed reaction message from 'You'")
            elif message_text == "emoji_or_special":
                if unsend_message(page, row, sender_name):
                    logger.info(f"[MessageHandler] Removed emoji/special message from 'You'")
            elif message_text.strip() == "" and "Open photo" not in message_text:
                continue
            else:
                unsend_message(page, row, sender_name)

        elif is_command_message:
            if is_user_spamming(sender_name):
                if add_angry_reaction_to_message(page, row):
                    if remove_message(page, row, sender_name):
                        logger.warning(f"[AntiSpam] Removed spam message from {sender_name}")
                        add_to_message_history(sender_name)
                continue
            if add_reaction_to_message(page, row):
                if remove_message(page, row, sender_name):
                    command_queue.put(message)
                    add_to_message_history(sender_name)
                    update_last_message_time()
                    logger.info(f"[MessageHandler] Message queued: '{sender_name}' - '{message_text}'")

        else:
            remove_message(page, row, sender_name)

def start_monitoring_messages(command_queue):
    last_cleanup_time = None
    while True:
        try:
            auth = MessengerAuth()
            page, browser, playwright = auth.log_in_to_messenger()

            auth.remove_unwanted_aria_labels(page)
            time.sleep(5)

            if not page:
                logger.error("[MessageHandler] Failed to log in for monitoring")
                time.sleep(10)
                continue
            logger.info("[MessageHandler] Starting message monitoring")
            try:
                take_info_screenshot(page, "monitoring_ready")
            except Exception as e:
                logger.error(f"[MessageHandler] Failed to take initial screenshot: {e}")

            while True:
                try:
                    extract_messages_fix_unknown_sender(page, command_queue)
                    
                    sleep_time = get_sleep_time()
                    
                    if sleep_time != 0:
                        current_time = time.time()
                        if (sleep_time == 3 and 
                            (last_cleanup_time is None or 
                            current_time - last_cleanup_time >= 300)):
                            cleanup_temp_folder()
                            last_cleanup_time = current_time
                        
                        time.sleep(sleep_time)

                except Exception as e:
                    logger.error(f"[MessageHandler] Error in message extraction: {e}")
                    try:
                        take_error_screenshot(page, "extraction_error")
                    except:
                        pass
                    break
            logger.critical("[MessageHandler] Closing browser, will reconnect...")
            try:
                browser.close()
            except:
                pass
            try:
                playwright.stop()
            except:
                pass
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("[MessageHandler] Monitoring stopped by user")
            break
        except Exception as e:
            logger.critical(f"[MessageHandler] Unexpected error in monitoring: {e}")
            time.sleep(10)

def get_last_message_time():
    global last_message_time
    
    if last_message_time is None:
        update_last_message_time()

    return last_message_time

def cleanup_temp_folder():
    try:
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR, exist_ok=True)
            return 0
        
        deleted_count = 0
        
        all_files = []
        for root, dirs, files in os.walk(TEMP_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
        
        for file_path in all_files:
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_count += 1
            except Exception as e:
                logger.debug(f"[Cleanup] Could not delete {file_path}: {e}")
        
        for root, dirs, files in os.walk(TEMP_DIR, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                except:
                    pass
        
        if deleted_count > 0:
            logger.info(f"[Cleanup] Cleaned {deleted_count} temp files")
            
        return deleted_count
        
    except Exception as e:
        logger.error(f"[Cleanup] Error cleaning temp: {e}")
        return 0