import sys
import ctypes
import platform
import threading
import time

from src.config import ConfigManager
from src.action_executor import ActionExecutor
from src.gesture_detector import GestureDetector
from src.listener import InputListener
from src.gui import BluetoothMapperApp

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    # Check for admin rights on Windows
    if platform.system() == "Windows":
        if not is_admin():
            print("WARNING: This application typically requires Administrator privileges to intercept global media keys.")
    
    print("Initializing components...")
    
    # 1. Config
    config_manager = ConfigManager()
    
    # 2. Action Executor
    action_executor = ActionExecutor()
    
    # 3. Gesture Detector
    gesture_detector = GestureDetector(config_manager, action_executor)
    
    # 4. Input Listener
    listener = InputListener(gesture_detector)
    
    # Start the listener
    listener.start()
    
    # 5. GUI
    print("Launching GUI...")
    try:
        app = BluetoothMapperApp(config_manager, listener)
        
        # Handle window close event to ensure clean shutdown
        def on_closing():
            print("Closing application...")
            listener.stop()
            app.destroy()
            sys.exit(0)

        app.protocol("WM_DELETE_WINDOW", on_closing)
        app.mainloop()
        
    except Exception as e:
        print(f"Error running GUI: {e}")
        print("Attempting to stop listener...")
        listener.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()
