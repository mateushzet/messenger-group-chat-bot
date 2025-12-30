from datetime import datetime as dt
from utils import take_error_screenshot
import time
from playwright.sync_api import sync_playwright
from auth import MessengerAuth

def log(msg):
    print(f"[{dt.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def close_message_remove_popup(page):
    try:
        close_btn = page.query_selector("div[aria-label='Close']")
        if close_btn:
            log("Closing remove popup")
            close_btn.click(force=True)
    except Exception as e:
        log(f"Error closing popup: {e}")

def click_menu_option(page, row, label):
    try:
        row.hover(position={"x": 0, "y": 0})
        log(f"Hovering over row to click menu option '{label}'")
        more_btn = row.wait_for_selector("div[aria-label='More']", timeout=1000)
        if more_btn:
            log("Clicking 'More' button")
            more_btn.click(force=True)
            menu_btn = page.wait_for_selector(f"div[aria-label='{label}'][role='menuitem']", timeout=1000)
            if menu_btn:
                log(f"Clicking menu item '{label}'")
                menu_btn.click(force=True)
                return True
    except Exception as e:
        log(f"Error clicking menu option '{label}': {e}")
    return False

def add_reaction_to_message(page, row):
    try:
        row.hover(position={"x": 0, "y": 0})
        log("Hovering to add reaction")
        react_btn = row.wait_for_selector("div[aria-label='React']", timeout=1000)
        if react_btn:
            react_btn.click(force=True)
            heart = page.wait_for_selector("img[alt='❤']", timeout=2000)
            if heart:
                heart.click(force=True)
                log("Added reaction ❤")
                return True
    except Exception as e:
        log(f"Error adding reaction: {e}")
        take_error_screenshot(page)
        close_message_remove_popup(page)
    return False

def remove_message(page, row, sender_name):
    try:
        log(f"Attempting to remove message from '{sender_name}'")
        if click_menu_option(page, row, "Remove message"):
            confirm = page.wait_for_selector("div[aria-label='Remove']", timeout=1000)
            if confirm:
                confirm.click(force=True)
                log(f"Removed message from '{sender_name}'")
                return True
    except Exception as e:
        log(f"Error removing message from '{sender_name}': {e}")
        take_error_screenshot(page)
        close_message_remove_popup(page)
    return False

def unsend_message(page, row, sender_name):
    try:
        log(f"Attempting to unsend message from '{sender_name}'")
        if click_menu_option(page, row, "Unsend message"):
            radio = page.wait_for_selector("input[type='radio'][value='1']", timeout=1000)
            if radio:
                radio.click(force=True)
                remove_button = page.wait_for_selector(
                    'xpath=//div[@aria-label="Remove" and @role="button"]', timeout=1000
                )
                if remove_button:
                    remove_button.click(force=True)
                    log(f"Unsent message from '{sender_name}'")
                    return True
    except Exception as e:
        log(f"Error unsending message from '{sender_name}': {e}")
        take_error_screenshot(page)
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
                    if img_el:
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
                log(f"Error during message extraction: {e}")
                take_error_screenshot(page)
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
            log("Unsend Open photo message")
            unsend_message(page, row, sender_name)

        elif sender_name == "Unknown":
            if is_command_message:
                retry_messages = collect_messages()
                for m in retry_messages:
                    if m["message"] == message_text:
                        if m["sender"] != "Unknown":
                            log(f"Adding reaction and removing unknown sender command message '{message_text}'")
                            if add_reaction_to_message(page, m["row"]):
                                if remove_message(page, m["row"], m["sender"]):
                                    command_queue.put(m)
                        break
            else:
                log(f"Removing message from unknown sender: '{message_text}'")
                remove_message(page, row, sender_name)

        elif sender_name == "You":
            if message_text.strip() == "" and "Open photo" not in message_text:
                continue
            unsend_message(page, row, sender_name)

        elif is_command_message:
            if add_reaction_to_message(page, row):
                if remove_message(page, row, sender_name):
                    command_queue.put(message)

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
                log("Failed to log in for monitoring")
                time.sleep(10)
                continue
            log("Starting message monitoring")
            try:
                auth._take_screenshot(page, "monitoring_ready")
            except Exception as e:
                log(f"Failed to take initial screenshot: {e}")
            while True:
                try:
                    extract_messages_fix_unknown_sender(page, command_queue)
                    time.sleep(2)
                except Exception as e:
                    log(f"Error in message extraction: {e}")
                    try:
                        auth._take_screenshot(page, "extraction_error")
                    except:
                        pass
                    break
            log("Closing browser, will reconnect...")
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
            log("Monitoring stopped by user")
            break
        except Exception as e:
            log(f"Unexpected error in monitoring: {e}")
            time.sleep(10)
