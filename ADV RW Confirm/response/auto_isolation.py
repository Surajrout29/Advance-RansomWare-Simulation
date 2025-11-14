import os
import json
import uuid
from utils.logger import log_event
from config import TARGET_DIR

def isolate_files(target_folder=TARGET_DIR, only_extensions=None, exclude_names=None):
    quarantine = os.path.join(target_folder, "quarantine")
    os.makedirs(quarantine, exist_ok=True)
    map_file = os.path.join(quarantine, "path_map.json")
    path_map = {}

    for root, _, files in os.walk(target_folder):
        for file in files:
            src = os.path.join(root, file)
            if "quarantine" in src:
                continue

            # Apply filters
            if only_extensions and not file.endswith(tuple(only_extensions)):
                continue
            if exclude_names and file in exclude_names:
                continue

            unique_name = f"{uuid.uuid4().hex}_{file}"
            dst = os.path.join(quarantine, unique_name)
            try:
                os.rename(src, dst)
                path_map[unique_name] = src
                log_event(f"File moved to quarantine: {file}")
            except Exception as e:
                log_event(f"Failed to quarantine {src} to {dst}: {e}")

    with open(map_file, 'w', encoding='utf-8') as f:
        json.dump(path_map, f, indent=2)


def unisolate_files(target_folder=TARGET_DIR):
    quarantine = os.path.join(target_folder, "quarantine")
    map_file = os.path.join(quarantine, "path_map.json")
    if not os.path.exists(map_file):
        print("No map file found.")
        return
    with open(map_file, 'r', encoding='utf-8') as f:
        path_map = json.load(f)
    for qname, orig_path in path_map.items():
        src = os.path.join(quarantine, qname)
        try:
            os.makedirs(os.path.dirname(orig_path), exist_ok=True)
            os.rename(src, orig_path)
            log_event(f"File restored from quarantine: {orig_path}")
        except Exception as e:
            log_event(f"Failed to restore {src} to {orig_path}: {e}")
    os.remove(map_file)
