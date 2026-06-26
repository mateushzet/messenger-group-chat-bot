import os
import time
import uuid
from datetime import datetime as dt
from utils import take_error_screenshot
from utils import take_info_screenshot
from auth import MessengerAuth
from logger import logger

last_message_time = None
initial_load_done = False
processed_in_session = set()

BASE_DIR = os.path.dirname(__file__)
TEMP_DIR = os.path.join(BASE_DIR, "temp")
LOG_PREVIEW_LEN = 140


def _preview(text, limit=LOG_PREVIEW_LEN):
    if text is None:
        return ""
    text = str(text).replace("\n", "\\n").replace("\r", "\\r")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def _perf_ms(start):
    return round((time.perf_counter() - start) * 1000, 1)


def update_last_message_time():
    global last_message_time
    last_message_time = dt.now()
    logger.debug(f"[MessageHandler] Updated last_message_time={last_message_time.isoformat()}")


def get_sleep_time():
    global last_message_time
    
    if last_message_time is None:
        update_last_message_time()
        logger.debug("[MessageHandler] get_sleep_time: last_message_time was None -> sleep=3")
        return 3
    
    now = dt.now()
    minutes_since_last = (now - last_message_time).total_seconds() / 60
    
    if minutes_since_last < 2:
        logger.debug(f"[MessageHandler] get_sleep_time: minutes_since_last={minutes_since_last:.2f} -> sleep=0")
        return 0
    if minutes_since_last < 5:
        logger.debug(f"[MessageHandler] get_sleep_time: minutes_since_last={minutes_since_last:.2f} -> sleep=1")
        return 1
    elif minutes_since_last < 30:
        logger.debug(f"[MessageHandler] get_sleep_time: minutes_since_last={minutes_since_last:.2f} -> sleep=3")
        return 3
    elif minutes_since_last < 60:
        logger.debug(f"[MessageHandler] get_sleep_time: minutes_since_last={minutes_since_last:.2f} -> sleep=5")
        return 5
    elif minutes_since_last < 120:
        logger.debug(f"[MessageHandler] get_sleep_time: minutes_since_last={minutes_since_last:.2f} -> sleep=10")
        return 10
    elif minutes_since_last < 180:
        logger.debug(f"[MessageHandler] get_sleep_time: minutes_since_last={minutes_since_last:.2f} -> sleep=15")
        return 15
    elif minutes_since_last < 240:
        logger.debug(f"[MessageHandler] get_sleep_time: minutes_since_last={minutes_since_last:.2f} -> sleep=20")
        return 20
    elif minutes_since_last < 360:
        logger.debug(f"[MessageHandler] get_sleep_time: minutes_since_last={minutes_since_last:.2f} -> sleep=25")
        return 25
    elif minutes_since_last < 480:
        logger.debug(f"[MessageHandler] get_sleep_time: minutes_since_last={minutes_since_last:.2f} -> sleep=30")
        return 30
    elif minutes_since_last < 720:
        logger.debug(f"[MessageHandler] get_sleep_time: minutes_since_last={minutes_since_last:.2f} -> sleep=60")
        return 60
    elif minutes_since_last < 1200:
        logger.debug(f"[MessageHandler] get_sleep_time: minutes_since_last={minutes_since_last:.2f} -> sleep=180")
        return 180
    else:
        logger.debug(f"[MessageHandler] get_sleep_time: minutes_since_last={minutes_since_last:.2f} -> sleep=200")
        return 200


pending_unknown_messages = []

def fill_unknown_senders(messages):
    global USER_NAME_CACHE, pending_unknown_messages
    
    name_mapping = {}
    for msg in messages:
        sender = msg.get("sender")
        avatar_url = msg.get("avatar_url")
        
        if sender and avatar_url and sender != "You" and sender != "Unknown":
            if " " in sender:
                first_name = sender.split()[0]
                name_mapping[first_name] = sender
                name_mapping[sender] = sender
    
    next_known_sender = None
    next_known_avatar = None
    
    for i in range(len(messages) - 1, -1, -1):
        current_msg = messages[i]
        sender = current_msg.get("sender")
        
        if sender == "Unknown":
            if next_known_sender:
                current_msg["sender"] = next_known_sender
                if next_known_avatar:
                    current_msg["avatar_url"] = next_known_avatar
                logger.debug(f"[MessageHandler] Filled Unknown sender with NEXT: {next_known_sender}")
        else:
            next_known_sender = current_msg["sender"]
            next_known_avatar = current_msg.get("avatar_url")
            
            if pending_unknown_messages:
                for pending_msg in pending_unknown_messages:
                    if pending_msg.get("sender") == "Unknown":
                        pending_msg["sender"] = next_known_sender
                        if next_known_avatar:
                            pending_msg["avatar_url"] = next_known_avatar
                        logger.debug(f"[MessageHandler] Filled pending Unknown with: {next_known_sender}")
                pending_unknown_messages.clear()
    
    for msg in messages:
        sender = msg.get("sender")
        if sender and sender != "You" and sender != "Unknown":
            if " " not in sender:
                if sender in name_mapping:
                    old_name = sender
                    msg["sender"] = name_mapping[sender]
                    logger.debug(f"[MessageHandler] Normalized name: '{old_name}' -> '{msg['sender']}'")
                else:
                    for full_name in name_mapping.values():
                        if full_name.startswith(sender + " "):
                            old_name = sender
                            msg["sender"] = full_name
                            name_mapping[sender] = full_name
                            logger.debug(f"[MessageHandler] Normalized name (found): '{old_name}' -> '{msg['sender']}'")
                            break
    
    for i in range(len(messages) - 1):
        current_msg = messages[i]
        next_msg = messages[i+1]
        
        current_sender = current_msg.get("sender")
        next_sender = next_msg.get("sender")
        
        if current_sender and next_sender:
            if current_sender != "You" and next_sender != "You":
                if " " not in current_sender and " " in next_sender:
                    if next_sender.startswith(current_sender + " "):
                        old_name = current_sender
                        current_msg["sender"] = next_sender
                        current_msg["avatar_url"] = next_msg.get("avatar_url")
                        logger.debug(f"[MessageHandler] Fixed name from next message: '{old_name}' -> '{current_msg['sender']}'")
    
    unknown_after = sum(1 for m in messages if m.get("sender") == "Unknown")
    short_names = sum(1 for m in messages if m.get("sender") and " " not in m.get("sender") and m.get("sender") not in ["You", "Unknown"])
    
    if short_names > 0:
        logger.debug(f"[MessageHandler] fill_unknown_senders: short_names={short_names}, unknown={unknown_after}")
    
    return unknown_after


def extract_messages_fix_unknown_sender(page, command_queue):
    global initial_load_done, processed_in_session, pending_unknown_messages
    
    cycle_id = uuid.uuid4().hex[:8]
    cycle_start = time.perf_counter()
    logger.debug(f"[MessageHandler] cycle_start id={cycle_id}")

    def collect_messages():
        collect_start = time.perf_counter()
        
        def parse_sender_and_message_from_aria(aria_label):
            if not aria_label:
                return None, None

            aria = aria_label.strip()
            if aria.lower().startswith("at "):
                parts = aria.split(",", 1)
                if len(parts) == 2:
                    rest = parts[1].strip()
                    if ": " in rest:
                        sender, msg = rest.split(": ", 1)
                        return sender.strip(), msg.strip()
                    if ":" in rest:
                        sender, msg = rest.split(":", 1)
                        return sender.strip(), msg.strip()
                    return rest.strip(), ""

            if " by " in aria:
                after_by = aria.split(" by ", 1)[1].strip()
                if ": " in after_by:
                    sender, msg = after_by.split(": ", 1)
                    return sender.strip(), msg.strip()
                if ":" in after_by:
                    sender, msg = after_by.split(":", 1)
                    return sender.strip(), msg.strip()
                return after_by.strip(), ""

            if ": " in aria:
                head, msg = aria.rsplit(": ", 1)
                if "," in head:
                    sender = head.split(",")[-1].strip()
                    return sender, msg.strip()
                return None, msg.strip()

            return None, None

        rows_local = page.query_selector_all(
            "div[data-scope='messages_table'][aria-roledescription='message'][aria-label]"
        )
        if not rows_local:
            rows_local = page.query_selector_all("div[role='row']")
        if not rows_local:
            rows_local = page.query_selector_all("[role='article'][aria-label]")
        
        logger.debug(f"[MessageHandler] collect_messages id={cycle_id}: rows_found={len(rows_local)}")
        messages_local = []
        
        for idx, row in enumerate(rows_local):
            try:
                data_message_id = row.get_attribute("data-message-id")
                
                gridcell = row.query_selector("div[role='gridcell']") or row

                if row.get_attribute("class") == "x9f619 x1n2onr6 x1ja2u2z":
                    continue
                
                you_sent_element = row.query_selector('span:has-text("You sent")')
                
                message_el = (
                    gridcell.query_selector("[data-lexical-editor='true']")
                    or gridcell.query_selector("div[dir='auto']")
                )
                message_text = message_el.inner_text().strip() if message_el else ""

                if message_text == "":
                    if row.query_selector("a[href*='/messenger_media/?attachment_id='], a[href*='messenger_media'][role='link']"):
                        message_text = "media_attachment"
                    elif row.query_selector("img[alt='GIF Image']"):
                        message_text = "gif_attachment"

                if message_text == "":
                    aria_label = row.get_attribute("aria-label")
                    if aria_label and any(word in aria_label.lower() for word in ["like", "thumbs", "reaction", "emoji"]):
                        message_text = "reaction"

                if message_text == "Enter":
                    continue
                    
                avatar = row.query_selector("img.x1rg5ohu, [role='row'] img")
                row_text = row.inner_text().lower()
                aria_label = row.get_attribute("aria-label") or ""
                aria_label_lower = aria_label.lower()
                contains_you_sent = (
                    bool(you_sent_element)
                    or ("you sent" in row_text)
                    or ("you sent" in aria_label_lower)
                )
                avatar_url = None
                
                if contains_you_sent:
                    sender_name = "You"
                elif avatar:
                    sender_name = avatar.get_attribute("alt")
                    avatar_url = avatar.get_attribute("src")
                else:
                    sender_name = "Unknown"
                    if message_text == "":
                        parsed_sender, parsed_msg = parse_sender_and_message_from_aria(aria_label)
                        if parsed_msg:
                            message_text = parsed_msg
                    
                messages_local.append({
                    "sender": sender_name,
                    "message": message_text,
                    "avatar_url": avatar_url,
                    "has_you_sent": contains_you_sent,
                    "data_message_id": data_message_id,
                })
            except Exception as e:
                logger.warning(f"[MessageHandler] Error during message extraction: {e}")
                take_error_screenshot(page, "message_extraction")
        
        unknown_before = sum(1 for m in messages_local if m.get("sender") == "Unknown")
        unknown_after = fill_unknown_senders(messages_local)
        
        for msg in messages_local:
            if msg.get("sender") == "Unknown" and msg.get("data_message_id"):
                if not any(p.get("data_message_id") == msg.get("data_message_id") for p in pending_unknown_messages):
                    pending_unknown_messages.append(msg)
                    logger.debug(f"[MessageHandler] Added to pending Unknown: ID={msg.get('data_message_id')}")
        
        commands = sum(1 for m in messages_local if str(m.get("message", "")).startswith("/"))
        
        if messages_local:
            logger.debug(
                f"[MessageHandler] collect_done id={cycle_id}: messages={len(messages_local)}, "
                f"commands={commands}, unknown_before={unknown_before}, unknown_after={unknown_after}, "
                f"pending_total={len(pending_unknown_messages)}, ms={_perf_ms(collect_start)}"
            )
        else:
            logger.debug(f"[MessageHandler] collect_done id={cycle_id}: messages=0, ms={_perf_ms(collect_start)}")
        
        return messages_local

    messages = collect_messages()
    if not messages:
        logger.debug(f"[MessageHandler] cycle_end id={cycle_id} messages=0 ms={_perf_ms(cycle_start)}")
        return

    if not initial_load_done:
        for message in messages:
            if message.get("data_message_id"):
                processed_in_session.add(message.get("data_message_id"))
        initial_load_done = True
        logger.info(f"[MessageHandler] Initial load: added {len(processed_in_session)} existing message IDs as processed")
        logger.debug(f"[MessageHandler] cycle_end id={cycle_id} initial load complete, no processing")
        return

    logger.debug(f"[MessageHandler] process_messages id={cycle_id}: start count={len(messages)}")
    
    for idx, message in enumerate(messages):
        sender_name = message["sender"]
        message_text = message["message"]
        data_message_id = message.get("data_message_id")
        
        if sender_name == "Unknown":
            logger.debug(f"[MessageHandler] msg id={cycle_id} idx={idx}: SKIPPING Unknown message, waiting for sender: '{_preview(message_text)}' (ID: {data_message_id})")
            continue

        if data_message_id and data_message_id in processed_in_session:
            logger.debug(f"[MessageHandler] msg id={cycle_id} idx={idx}: skipping already processed message {data_message_id}")
            continue

        is_command_message = message_text.startswith('/')
        page.mouse.move(0, 0)

        logger.debug(
            f"[MessageHandler] msg id={cycle_id} idx={idx} sender='{sender_name}' "
            f"command={is_command_message} you_sent={message.get('has_you_sent')} "
            f"text='{_preview(message_text)}'"
        )

        if is_command_message and sender_name != "You" and not message.get("has_you_sent"):
            if data_message_id and data_message_id not in processed_in_session:
                logger.info(f"[MessageHandler] Command queued: '{sender_name}' - '{message_text}' (ID: {data_message_id})")
                command_queue.put(message)
                processed_in_session.add(data_message_id)
                update_last_message_time()
            elif not data_message_id:
                logger.warning(f"[MessageHandler] Command without data-message-id, cannot track: '{message_text}'")
        else:
            if is_command_message and (sender_name == "You" or message.get("has_you_sent")):
                logger.debug(f"[MessageHandler] msg id={cycle_id} idx={idx}: ignoring command from self")
            else:
                logger.debug(f"[MessageHandler] msg id={cycle_id} idx={idx}: ignoring non-command message from '{sender_name}'")

    logger.debug(f"[MessageHandler] cycle_end id={cycle_id} messages={len(messages)} ms={_perf_ms(cycle_start)}")


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
            logger.debug(f"[Cleanup] Cleaned {deleted_count} temp files")
            
        return deleted_count
        
    except Exception as e:
        logger.error(f"[Cleanup] Error cleaning temp: {e}")
        return 0


def start_monitoring_messages(command_queue):
    global initial_load_done, processed_in_session
    
    last_cleanup_time = None
    last_hourly_screenshot_time = None
    initial_load_done = False
    processed_in_session = set()
    
    while True:
        try:
            auth = MessengerAuth()
            logger.info("[MessageHandler] Logging in to Messenger for monitoring...")
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
                    click_go_to_recent_button(page)

                    extract_messages_fix_unknown_sender(page, command_queue)
                    
                    sleep_time = get_sleep_time()
                    logger.debug(f"[MessageHandler] loop_sleep sleep_time={sleep_time}")

                    now_ts = time.time()
                    if last_hourly_screenshot_time is None or (now_ts - last_hourly_screenshot_time) >= 3600:
                        try:
                            take_info_screenshot(page, "hourly_monitoring")
                            last_hourly_screenshot_time = now_ts
                            logger.info("[MessageHandler] Hourly screenshot saved")
                        except Exception as e:
                            logger.warning(f"[MessageHandler] Hourly screenshot failed: {e}")
                    
                    if sleep_time != 0:
                        current_time = time.time()
                        if (sleep_time == 3 and 
                            (last_cleanup_time is None or 
                            current_time - last_cleanup_time >= 300)):
                            cleanup_start = time.perf_counter()
                            cleanup_temp_folder()
                            last_cleanup_time = current_time
                            logger.debug(f"[Cleanup] cycle_cleanup ms={_perf_ms(cleanup_start)}")
                        
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

def click_go_to_recent_button(page):
    """Kliknij przycisk 'Go to most recent message' jeśli istnieje"""
    try:
        recent_button = page.query_selector('div[aria-label="Go to most recent message"][role="button"]')
        
        if recent_button:
            logger.info("[MessageHandler] Found 'Go to most recent message' button, clicking...")
            recent_button.click()
            time.sleep(1)
            return True
        else:
            logger.debug("[MessageHandler] 'Go to most recent message' button not found")
            return False
            
    except Exception as e:
        logger.warning(f"[MessageHandler] Error clicking go to recent button: {e}")
        return False