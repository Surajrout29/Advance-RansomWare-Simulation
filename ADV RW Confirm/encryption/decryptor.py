import os
from Crypto.Cipher import AES
from .key_manager import KEY
from utils.padding import unpad_data

def decrypt_file(path, key=KEY):
    with open(path, 'rb') as f:
        data = f.read()

    # Checks if file is too small
    if len(data) < 16:
        print(f"[!] Skipping {path} (too small / already decrypted)")
        return

    iv = data[:16]
    ct = data[16:]

    # Checks the ciphertext length must be multiple of 16
    if len(ct) % 16 != 0:
        print(f"[!] Skipping {path} (invalid ciphertext, maybe already decrypted)")
        return

    try:
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        pt = unpad_data(cipher.decrypt(ct))
        with open(path, 'wb') as f:
            f.write(pt)
        print(f"Decrypted: {path}")
    except Exception as e:
        print(f"[!] Skipping {path}, decryption failed: {e}")
