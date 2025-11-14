from Crypto.Util.Padding import pad, unpad

BLOCK_SIZE = 16  # AES block size

def pad_data(data: bytes) -> bytes:
    return pad(data, BLOCK_SIZE)

def unpad_data(data: bytes) -> bytes:
    return unpad(data, BLOCK_SIZE)
