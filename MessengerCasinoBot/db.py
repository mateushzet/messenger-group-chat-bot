import sqlite3

def save_message_to_db(message_data):
    try:
        conn = sqlite3.connect("mydatabase.db", timeout=5)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO commands (sender, message, created_at)
            VALUES (?, ?, ?)
        """, (message_data['sender'], message_data['message'], message_data['timestamp']))

        conn.commit()
        conn.close()

        print("[DB] Message saved to database.")
    except Exception as e:
        print(f"[DB] ERROR saving to database: {e}")