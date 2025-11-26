from datetime import datetime as dt
from utils import take_error_screenshot
import time
from playwright.sync_api import sync_playwright
from auth import MessengerAuth
from utils import Utils

def close_message_remove_popup(page):
    try:
        close_btn = page.query_selector("div[aria-label='Close']")
        if close_btn:
            close_btn.click(force=True)
    except:
        pass

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
    except:
        pass
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
        print(f"Error adding reaction: {str(e)[:200]}")
        take_error_screenshot(page)
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
        print(f"Error removing message: {str(e)[:200]}")
        take_error_screenshot(page)
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
        print(f"Error unsending message: {str(e)[:200]}")
        take_error_screenshot(page)
        close_message_remove_popup(page)
    return False

def fill_unknown_senders(messages):
    last_known_sender = None

    for i in reversed(range(len(messages))):
        if messages[i]["sender"] == "Unknown":
            if last_known_sender:
                messages[i]["sender"] = last_known_sender
        else:
            last_known_sender = messages[i]["sender"]

def extract_messages_fix_unknown_sender(page, command_queue):
    def collect_messages():
        rows_local = page.query_selector_all("div[role='row']")
        messages_local = []

        for row in rows_local:
            try:
                gridcell = row.query_selector("div[role='gridcell']")
                if not gridcell:
                    continue

                if row.get_attribute("class") == None or row.get_attribute("class") == "x9f619 x1n2onr6 x1ja2u2z":
                    continue

                message_el = gridcell.query_selector("div[dir='auto']")
                message_text = message_el.inner_text().strip() if message_el else ""

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
                print(f"Error during message extraction: {e}")
                take_error_screenshot(page)

        fill_unknown_senders(messages_local)
        return messages_local

    messages = collect_messages()

    for message in messages:
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
                        break
            else:
                remove_message(page, row, sender_name)

        elif sender_name == "You":
            unsend_message(page, row, sender_name)

        elif is_command_message:
            if add_reaction_to_message(page, row):
                if remove_message(page, row, sender_name):
                    command_queue.put(message)

        else:
            remove_message(page, row, sender_name)

def start_monitoring_messegases(command_queue):
    with sync_playwright() as p:
        auth = MessengerAuth()
        browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(viewport={"width": 1000, "height": 900}, locale="en-US")
        page = context.new_page()

        if not auth.load_cookies(context):
            print("No cookies found, login required")

        try:
            page.goto(f"https://www.messenger.com/t/{auth.threadid}", wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Loading error: {e}")
            Utils.take_error_screenshot(page)
            browser.close()
            return

        if not auth.is_logged_in(page):
            auth.accept_all_cookies(page)
            if not auth.login_with_credentials(page):
                print("Login error")
                browser.close()
                return
            auth.save_cookies(context)

        time.sleep(3)
        Utils.remove_unwanted_aria_labels(page)

        while True:
            extract_messages_fix_unknown_sender(page, command_queue)
            time.sleep(1)