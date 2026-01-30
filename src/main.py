import threading
import sys
import multiprocessing
from .config_manager import ConfigManager
from .bluetooth_manager import BluetoothManager
from .gesture_engine import GestureEngine
from .ui import BluetoothBudsControlApp

def main():
    # PyInstaller boilerplate for Windows multiprocessing support
    multiprocessing.freeze_support()

    # Redirect stdout/stderr to file for debugging in windowed mode
    if sys.stdout is None or sys.stderr is None or not sys.stdout.isatty():
        sys.stdout = open("debug.log", "w")
        sys.stderr = sys.stdout

    print("Starting Bluetooth Buds Control...")

    # Initialize Managers
    config = ConfigManager()
    bluetooth = BluetoothManager()

    # Initialize Logic
    gesture_engine = GestureEngine(config)

    # Start Gesture Engine
    # Note: keyboard.hook() is non-blocking, but we need to ensure it persists.
    # The UI mainloop will keep the process alive.
    gesture_engine.start()

    # Initialize UI
    app = BluetoothBudsControlApp(config, bluetooth, gesture_engine)

    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        gesture_engine.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()
