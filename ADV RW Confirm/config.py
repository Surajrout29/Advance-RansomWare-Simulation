import os

TARGET_EXTENSIONS = ['.txt', '.exe', '.com', '.bat', '.cmd', '.ink', '.docx', 
                     '.dot', '.dotx', '.xlsx', '.xls', '.ppt', '.pptx', '.pdf', 
                     '.zip', '.rar', '.tar', '.7z', '.mp3', '.wav', '.acc', '.wma', 
                     '.mp4', '.mkv', '.mov', '.gif', '.jpeg', '.psd', '.ai', 'svg','.avif', 
                     '.jpg', '.png', '.webp', '.iso', '.img', '.vhd', '.sys', '.inf', 
                     '.ini', '.tmp', '.bak', '.html', '.css', '.js', '.json',
                     '.db', '.sqlite', '.mdb', '.accdb', '.xml', '.log', '.msi', 
                     '.msp', '.dat', '.pub', '.eml', '.msg', '.scr', '.vob', '.wpl',
                     '.c','.cpp', '.java', '.py', '.cs', '.mdf', '.ldf', '.torrent', 
                     '.obj', '.stl', '.3ds', '.fon', '.ttf', '.otf', '.xps', '.key', '.bin','.pyc']
TARGET_DIR = "test_files"
RANSOM_NOTE = os.path.join("ransom_note", "note.txt")
LOG_FILE = os.path.join("utils", "logs.txt")
KEY_FILE = os.path.join("encryption", "key.bin")
