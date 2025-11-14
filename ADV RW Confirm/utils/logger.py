import os
from datetime import datetime
from config import LOG_FILE

def log_event(event):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a', encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {event}\n")
