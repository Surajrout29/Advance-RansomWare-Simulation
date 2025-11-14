import os

def main():
    print("""
========= Ransomware Simulation =========
1. Launch CLI Menu
2. Launch GUI App
3. Exit
""")
    choice = input("Choose an option: ")
    if choice == '1':
        os.system("python cli_menu.py")
    elif choice == '2':
        os.system("python gui_app.py")
    else:
        print("Exiting...")

if __name__ == "__main__":
    main()
