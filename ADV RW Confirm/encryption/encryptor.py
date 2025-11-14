from Crypto.Cipher import AES
import os
from .key_manager import KEY
from utils.padding import pad_data

def encrypt_file(path):
    with open(path, 'rb') as f:
        data = f.read()
    cipher = AES.new(KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad_data(data))
    with open(path, 'wb') as f:
        f.write(cipher.iv + ct_bytes)
