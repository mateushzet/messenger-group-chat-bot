from datetime import datetime as dt
from db import save_message_to_db
from utils import take_error_screenshot

def close_message_remove_popup(page):
    try:
        close_btn = page.query_selector("div[aria-label='Close']")
        if close_btn:
            close_btn.click(force=True)
    except:
        pass

def add_reaction_to_message(page, row):
    try:
        row.hover(position={"x": 0, "y": 0})
        react_btn = row.wait_for_selector("div[aria-label='React']", timeout=1000)
        if react_btn:
            react_btn.click(force=True)
            heart = page.wait_for_selector("div[role='menuitem'] img[alt='❤']", timeout=1000)
            if heart:
                heart.click(force=True)
                print("Heart react added")
                return True
    except Exception as e:
        print(f"[ERROR] While adding reaction: {str(e)[:200]}")
        take_error_screenshot(page)
        close_message_remove_popup(page)
    return False

def remove_message(page, row, sender_name):
    try:
        row.hover(position={"x": 0, "y": 0})
        more_btn = row.wait_for_selector("div[aria-label='More']", timeout=1000)
        if more_btn:
            more_btn.click(force=True)
            remove_btn = page.wait_for_selector("div[aria-label='Remove message'][role='menuitem']", timeout=1000)
            if remove_btn:
                remove_btn.click(force=True)
                confirm = page.wait_for_selector("div[aria-label='Remove']", timeout=1000)
                if confirm:
                    confirm.click(force=True)
                    print(f"Removed message from {sender_name}")
                    return True
    except Exception as e:
        print(f"[ERROR] While removing message: {str(e)[:200]}")
        take_error_screenshot(page)
        close_message_remove_popup(page)
    return False

def unsend_message(page, row, sender_name):
    try:
        row.hover(position={"x": 0, "y": 0})
        more_btn = row.wait_for_selector("div[aria-label='More']", timeout=1000)
        if more_btn:
            more_btn.click(force=True)
            remove_btn = page.wait_for_selector("div[aria-label='Unsend message'][role='menuitem']", timeout=1000)
            if remove_btn:
                remove_btn.click(force=True)
                radio = page.wait_for_selector("input[type='radio'][value='1']", timeout=1000)
                if radio:
                    radio.click(force=True)
                    remove_button = page.wait_for_selector('xpath=//div[@aria-label="Remove" and @role="button"]', timeout=1000)
                if remove_button:
                    remove_button.click(force=True)
                    print(f"Removed message from {sender_name}")
                    return True
    except Exception as e:
        print(f"[ERROR] While removing message: {str(e)[:200]}")
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

def extract_messages_fix_unknown_sender(page):
    rows = page.query_selector_all("div[role='row']")
    messages = []

    for row in rows:
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

            if avatar:
                sender_name = avatar.get_attribute("alt")
            elif contains_you_sent:
                sender_name = "You"
            else:
                sender_name = "Unknown"

            messages.append({
                "row": row,
                "sender": sender_name,
                "message": message_text,
                "timestamp": dt.now().isoformat()
            })

        except Exception as e:
            print(f"Error during message extraction: {e}")
            take_error_screenshot(page)

    fill_unknown_senders(messages)

    for message in messages:
        sender_name = message["sender"]
        message_text = message["message"]
        row = message["row"]
        is_command_message = message_text.startswith('/')

        page.mouse.move(0,0)

        if sender_name == "Open photo":
            print("Removing: Open photo")
            unsend_message(page, row, sender_name)
        elif sender_name == "Unknown":
            print("Removing: Unknown")
            remove_message(page, row, sender_name)
        elif sender_name == "You":
            print("Removing: You")
            unsend_message(page, row, sender_name)
        elif is_command_message:
            print("Processing command")
            if add_reaction_to_message(page, row):
                if remove_message(page, row, sender_name):
                    save_message_to_db(message)
        else:
            print("Removing: Else")
            remove_message(page, row, sender_name)