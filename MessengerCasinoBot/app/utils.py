from playwright.sync_api import Page
import datetime

class Utils:
    @staticmethod
    def remove_unwanted_aria_labels(page: Page):
        aria_labels_to_remove = [
            "Inbox switcher",
            "Chats",
            "Marketplace",
            "Requests",
            "Archive",
            "Settings, help and more",
            "Expand inbox sidebar",
            "New message",
            "Close",
            "Fix now",
            "Start a voice call",
            "Start a video call",
            "Conversation information",
            "Details and actions",
            "Send a voice clip",
            "Choose a sticker",
            "Choose a GIF",
            "Choose an emoji",
            "Send a like",
            "Profile",
            "Unmute notifications",
            "Search",
            "Chat info",
            "Customize chat",
            "Media & files",
            "Thread composer",
        ]

        classes_to_remove = [
            "some-class-to-remove",
            "x1ey2m1c",
        ]

        js_labels = ','.join([f'"{label}"' for label in aria_labels_to_remove])
        js_classes = ','.join([f'"{cls}"' for cls in classes_to_remove])

        page.evaluate(f"""
            (() => {{
                const labels = [{js_labels}];
                const classes = [{js_classes}];

                const elements = document.querySelectorAll('[aria-label]');
                elements.forEach(el => {{
                    const label = el.getAttribute('aria-label');
                    if (!label) return;

                    for (const target of labels) {{
                        if (label === target || label.startsWith(target)) {{
                            el.remove();
                            break;
                        }}
                    }}
                }});

                classes.forEach(cls => {{
                    document.querySelectorAll(`div.${{cls}}`).forEach(el => el.remove());
                }});
            }})();
        """)

def take_error_screenshot(page):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"error_{timestamp}.png"
    page.screenshot(path=filename)