import os
import time
from config import TARGET_DIR, TARGET_EXTENSIONS
from utils.logger import log_event

def monitor_directory():
    file_states = {}
    while True:
        try:
            for root, _, files in os.walk(TARGET_DIR):
                for file in files:
                    if not file.endswith(tuple(TARGET_EXTENSIONS)):
                        continue
                    path = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(path)
                        if path not in file_states:
                            file_states[path] = mtime
                        elif file_states[path] != mtime:
                            log_event(f"ALERT: Suspicious modification: {path}")
                            file_states[path] = mtime
                    except Exception as e:
                        log_event(f"Error monitoring {path}: {e}")
                        continue
        except Exception as e:
            log_event(f"Top-level monitor error: {e}")
        time.sleep(2)
