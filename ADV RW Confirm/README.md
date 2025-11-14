                            ADVANCED RANSOMWARE SIMULATION
                     Attack | Detection | Quarantine | Recovery
                              Fully Safe • Academic Only
                            Educational Cybersecurity Project

Overview :-
This project is a fully safe and controlled ransomware simulation developed for academic and research purposes. It demonstrates the complete lifecycle of ransomware, including:
    Attack Simulation (AES encryption + ransom note drop).
    Detection & Logging (real-time monitoring).
    Response & Quarantine System.
    File Recovery & Decryption.
    Realistic Ransomware GUI Lock Screen.
    Simulation of Fake payment processing, countdown timer, and webcam feed.
The system is designed strictly for educational use, allowing students and cybersecurity learners to understand the behaviour of ransomware without any real harm to system files.

Features:-
1) Attack Simulation:
AES encryption in CBC mode
Randomized .srjcrypt encrypted file names
Ransom note dropped automatically
Realistic attack patterns and behaviour

2) Detection & Monitoring:
Real-time file monitoring
Logs suspicious modifications
Timestamped logs stored in logs.txt

3) Response & Quarantine:
Affected or suspicious files are isolated
Maintains a path_map.json for restoration
Safe isolation without file loss

4) Decryption & Recovery:
AES key stored in key.bin
Decrypts and restores files to original names
Cleans ransom notes after recovery

5) Advanced GUI Lock Screen:
Full-screen ransomware-style interface
Countdown timer for data destruction
Live webcam feed (real-time simulated/actual)
Threat level indicators, system monitors, activity logs
FAke BTC payment simulation + QR code
“I HAVE PAID” button triggers decryption

6) Safe & Academic:
Operates only inside user-selected folders
No harmful actions performed on the system
Fully reversible encryption process

7) Tech Stack:
Programming Language
Python Latest Version

Cryptography
PyCryptodome (AES encryption/decryption)
PKCS7 padding

GUI & Visuals
Tkinter
Pillow (PIL)
OpenCV (for webcam support)

System Utilities
OS module
JSON & UUID
Threading & Time
Shutil

Development Tools
Visual Studio Code
GitHub
PyInstaller (optional for packaging)

                * Install Required Dependencies *
pip install -r requirements.txt

                * Run the Program *
CLI Mode:
python main.py

GUI Ransomware Simulation:
python gui_app.py

                    Usage Guide:-
CLI Menu Includes:
Start Ransomware Attack
Start Monitoring
Quarantine Files
Decrypt Files
Restore from Quarantine
Stop Monitor

GUI Includes:
Select target folder
Files automatically encrypted
Countdown begins
Live webcam feed
BTC payment simulation

                    *System Operations Workflow*
1) Attack Phase
Encrypt files
Rename files
Drop ransom note

2) Detection Phase
Monitor directory
Log suspicious changes

3) Response Phase
Quarantine isolated files
Maintain path mapping

4) Recovery Phase
Decrypt files
Restore original names
Remove ransom notes

                            !! Disclaimer !!

This project is strictly for educational and research purposes.
It must never be used on real systems, networks, or unauthorized devices.

*Author*
Suraj Sarat Rout
B.Sc Computer Science
K.M.C College, Khopoli