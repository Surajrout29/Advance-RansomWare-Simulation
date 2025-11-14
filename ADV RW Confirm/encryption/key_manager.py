from Crypto.Random import get_random_bytes
import os
from config import KEY_FILE

def get_or_create_key():
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    key = get_random_bytes(32)  # AES-256
    with open(KEY_FILE, 'wb') as f:
        f.write(key)
    return key

KEY = get_or_create_key()
