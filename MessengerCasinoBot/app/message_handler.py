from datetime import datetime as dt
from utils import take_error_screenshot
import time
from auth import MessengerAuth
from logger import logger

last_message_time = None

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
        logger.warning(f"[MesseageHandler] Error closing popup: {e}")

def click_menu_option(page, row, label):
    try:
        row.hover(position={"x": 0, "y": 0})
        more_btn = row.wait_for_selector("div[aria-label='More']", timeout=1000)
        if more_btn:
            more_btn.click(force=True)
            menu_btn = page.wait_for_selector(f"div[aria-label='{label}'][role='menuitem']", timeout=1000)
            if menu_btn:
                menu_btn.click(force=True)
                return True
    except Exception as e:
        logger.warning(f"[MesseageHandler] Error clicking menu option '{label}': {e}")
    return False

def add_reaction_to_message(page, row):
    try:
        row.hover(position={"x": 0, "y": 0})
        react_btn = row.wait_for_selector("div[aria-label='React']", timeout=1000)
        if react_btn:
            react_btn.click(force=True)
            heart = page.wait_for_selector("img[alt='❤']", timeout=2000)
            if heart:
                heart.click(force=True)
                return True
    except Exception as e:
        logger.warning(f"[MesseageHandler] Error adding reaction: {e}")
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
        logger.warning(f"[MesseageHandler] Error removing message from '{sender_name}': {e}")
        take_error_screenshot(page,"removing_message")
        close_message_remove_popup(page)
    return False

def unsend_message(page, row, sender_name):
    try:
        if click_menu_option(page, row, "Unsend message"):
            radio = page.wait_for_selector("input[type='radio'][value='1']", timeout=1000)
            if radio:
                radio.click(force=True)
                remove_button = page.wait_for_selector(
                    'xpath=//div[@aria-label="Remove" and @role="button"]', timeout=1000
                )
                if remove_button:
                    remove_button.click(force=True)
                    return True
    except Exception as e:
        logger.warning(f"[MesseageHandler] Error unsending message from '{sender_name}': {e}")
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
                message_el = gridcell.query_selector("div[dir='auto']")
                message_text = message_el.inner_text().strip() if message_el else ""

                if message_text == "":
                    img_el = row.query_selector('img[alt="Open photo"]')
                    gif_el = row.query_selector('img[alt="GIF Image"]')
                    if img_el or gif_el:
                        message_text = "photo"

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
                    "avatar_url": avatar_url
                })
            except Exception as e:
                logger.warning(f"[MesseageHandler] Error during message extraction: {e}")
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
                            if add_reaction_to_message(page, m["row"]):
                                if remove_message(page, m["row"], m["sender"]):
                                    command_queue.put(m)
                                    update_last_message_time()
                                    logger.info(f"[MesseageHandler] Message queued: '{sender_name}' - '{message_text}'")
                        break
            else:
                remove_message(page, row, sender_name)

        elif sender_name == "You":
            if message_text.strip() == "" and "Open photo" not in message_text:
                continue
            unsend_message(page, row, sender_name)

        elif is_command_message:
            if add_reaction_to_message(page, row):
                if remove_message(page, row, sender_name):
                    command_queue.put(message)
                    update_last_message_time()
                    logger.info(f"[MesseageHandler] Message queued: '{sender_name}' - '{message_text}'")

        else:
            remove_message(page, row, sender_name)


def start_monitoring_messages(command_queue):
    while True:
        try:
            auth = MessengerAuth()
            page, browser, playwright = auth.log_in_to_messenger()

            auth.remove_unwanted_aria_labels(page)
            time.sleep(5)

            if not page:
                logger.error("[MesseageHandler] Failed to log in for monitoring")
                time.sleep(10)
                continue
            logger.info("[MesseageHandler] Starting message monitoring")
            try:
                auth._take_screenshot(page, "monitoring_ready")
            except Exception as e:
                logger.error(f"[MesseageHandler] Failed to take initial screenshot: {e}")

            last_message_time = dt.now()

            while True:
                try:
                    extract_messages_fix_unknown_sender(page, command_queue)
                    
                    sleep_time = get_sleep_time()
                    if sleep_time != 0:
                        time.sleep(sleep_time)

                except Exception as e:
                    logger.error(f"[MesseageHandler] Error in message extraction: {e}")
                    try:
                        auth._take_screenshot(page, "extraction_error")
                    except:
                        pass
                    break
            logger.critical("[MesseageHandler] Closing browser, will reconnect...")
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
            logger.info("[MesseageHandler] Monitoring stopped by user")
            break
        except Exception as e:
            logger.critical(f"[MesseageHandler] Unexpected error in monitoring: {e}")
            time.sleep(10)

def get_last_message_time():
    global last_message_time
    
    if last_message_time is None:
        update_last_message_time()

    return last_message_time