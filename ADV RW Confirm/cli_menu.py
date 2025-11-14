import threading, time
from encryption.encryptor import encrypt_file
from encryption.decryptor import decrypt_file
from detection.monitor import monitor_directory
from response.auto_isolation import isolate_files, unisolate_files
from utils.file_scanner import get_target_files
from utils.drop_note import drop_ransom_note, remove_ransom_note
from config import TARGET_DIR, KEY_FILE

_stop_event = threading.Event()

def start_monitoring():
    print("[*] Starting file monitor...")
    monitor_directory(stop_event=_stop_event)  

def stop_monitoring():
    _stop_event.set()
    time.sleep(0.5)

def start_encryption():
    print("[*] Encrypting files...")
    files = get_target_files(TARGET_DIR)
    for file in files:
        encrypt_file(file)
        print(f"Encrypted: {file}")
    drop_ransom_note(TARGET_DIR)
    print("[!] Ransomware attack simulated.")

def start_decryption():
    print("[*] Decrypting files...")
    with open(KEY_FILE, 'rb') as f:
        key = f.read()
    files = get_target_files(TARGET_DIR)
    for file in files:
        decrypt_file(file, key)
        print(f"Decrypted: {file}")
    remove_ransom_note(TARGET_DIR)
    print("[✓] Files restored and ransom notes removed.")

def main():
    monitor_thread = None
    print("= Ransomware Simulation Menu =")
    while True:
        print("""
1. Start Ransomware Attack
2. Start Monitor (Detection)
3. Quarantine (Response)
4. Decrypt Files (Recovery)
5. Restore Quarantined Files
6. Stop Monitor
7. Exit
""")
        choice = input("Enter your choice: ").strip()
        try:
            if choice == '1':
                start_encryption()
            elif choice == '2':
                if not monitor_thread or not monitor_thread.is_alive():
                    monitor_thread = threading.Thread(target=start_monitoring, daemon=True)
                    monitor_thread.start()
                else:
                    print("[!] Monitor already running.")
            elif choice == '3':
                isolate_files(
                    target_folder=TARGET_DIR,
                    only_extensions=None, 
                    exclude_names={"path_map.json"}
                )
            elif choice == '4':
                start_decryption()
            elif choice == '5':
                unisolate_files()
            elif choice == '6':
                stop_monitoring()
            elif choice == '7':
                break
            else:
                print("[!] Invalid choice. Try again.")
        except Exception as e:
            print(f"[!] Operation failed: {e}")

if __name__ == "__main__":
    main()
