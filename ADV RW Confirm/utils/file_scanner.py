import os
from config import TARGET_EXTENSIONS

def get_target_files(directory):
    targets = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(tuple(ext.lower() for ext in TARGET_EXTENSIONS)):
                targets.append(os.path.join(root, file))
    return targets
