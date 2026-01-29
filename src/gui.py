import customtkinter as ctk
import platform
import sys
import threading
from PIL import Image

# Check for Windows
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import winreg

class BluetoothMapperApp(ctk.CTk):
    def __init__(self, config_manager, listener):
        super().__init__()

        self.config = config_manager
        self.listener = listener

        self.title("Bluetooth Earbuds Controller")
        self.geometry("500x550")
        self.resizable(False, False)

        # Set theme
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.action_options = [
            "none", "play_pause", "next_track", "previous_track", 
            "volume_up", "volume_down", "volume_mute", 
            "scroll_up", "scroll_down", 
            "alt_tab", "switch_desktop_next", "switch_desktop_prev", 
            "lock_screen"
        ]

        self.create_widgets()
        self.load_settings()

    def create_widgets(self):
        # Title
        self.label_title = ctk.CTkLabel(self, text="Bluetooth Gestures", font=("Roboto", 24, "bold"))
        self.label_title.pack(pady=20)

        # Main Frame
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Play/Pause Gestures Section
        self.create_dropdown_row(self.frame, "Single Tap (Play/Pause):", "play_pause_single", 0)
        self.create_dropdown_row(self.frame, "Double Tap (Play/Pause):", "play_pause_double", 1)
        self.create_dropdown_row(self.frame, "Triple Tap (Play/Pause):", "play_pause_triple", 2)

        # Separator or Space
        ctk.CTkLabel(self.frame, text="Other Buttons", font=("Roboto", 16, "bold")).grid(row=3, column=0, sticky="w", padx=20, pady=(20, 10))

        # Other Buttons Section
        self.create_dropdown_row(self.frame, "Next Track Button:", "next_track", 4)
        self.create_dropdown_row(self.frame, "Previous Track Button:", "previous_track", 5)

        # Settings Section
        self.frame_settings = ctk.CTkFrame(self)
        self.frame_settings.pack(pady=20, padx=20, fill="x")

        self.var_start_windows = ctk.BooleanVar()
        self.check_start_windows = ctk.CTkCheckBox(
            self.frame_settings, 
            text="Start with Windows", 
            variable=self.var_start_windows,
            command=self.toggle_start_with_windows
        )
        self.check_start_windows.pack(pady=10, padx=20, side="left")
        
        if not IS_WINDOWS:
            self.check_start_windows.configure(state="disabled", text="Start with Windows (Win only)")

        # Status Label
        self.label_status = ctk.CTkLabel(self, text="Status: Running", text_color="green")
        self.label_status.pack(pady=10)

    def create_dropdown_row(self, parent, label_text, config_key, row_idx):
        label = ctk.CTkLabel(parent, text=label_text, font=("Roboto", 14))
        label.grid(row=row_idx, column=0, sticky="w", padx=20, pady=10)

        # Use a callback factory to capture the key
        def callback(choice):
            self.update_mapping(config_key, choice)

        dropdown = ctk.CTkOptionMenu(
            parent, 
            values=self.action_options,
            command=callback
        )
        dropdown.grid(row=row_idx, column=1, padx=20, pady=10)
        
        # Store reference to set value later
        setattr(self, f"dropdown_{config_key}", dropdown)

    def load_settings(self):
        # Load mappings to dropdowns
        mappings = ["play_pause_single", "play_pause_double", "play_pause_triple", "next_track", "previous_track"]
        for key in mappings:
            val = self.config.get_mapping(key)
            if val not in self.action_options:
                val = "none"
            getattr(self, f"dropdown_{key}").set(val)

        # Load Checkbox
        if IS_WINDOWS:
            self.var_start_windows.set(self.check_registry_startup())
        else:
             self.var_start_windows.set(self.config.get_setting("start_with_windows"))

    def update_mapping(self, key, action):
        print(f"Updating {key} to {action}")
        self.config.set_mapping(key, action)

    def toggle_start_with_windows(self):
        enabled = self.var_start_windows.get()
        self.config.set_setting("start_with_windows", enabled)
        
        if IS_WINDOWS:
            self.set_registry_startup(enabled)

    def check_registry_startup(self):
        if not IS_WINDOWS: return False
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "BluetoothEarbudsController")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Error checking registry: {e}")
            return False

    def set_registry_startup(self, enable):
        if not IS_WINDOWS: return
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "BluetoothEarbudsController"
        exe_path = sys.executable # This points to python.exe or the frozen exe
        
        # If running as script, we might want to point to python w/ script, but usually this feature is for the compiled exe.
        # If frozen (PyInstaller), sys.executable is the exe.
        # If script, sys.argv[0] is the script.
        
        if not getattr(sys, 'frozen', False):
             # Development mode: Don't mess with registry preferably, or point to python + script
             # For safety in this prototype, I'll log it but not actually write if not frozen, 
             # unless the user really wants it. 
             # But let's just write the python command for now for completeness.
             pass 

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enable:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{sys.executable}"')
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Error setting registry: {e}")

    def on_closing(self):
        self.listener.stop()
        self.destroy()

if __name__ == "__main__":
    # Mock dependencies for UI testing if run directly
    from src.config import ConfigManager
    # Mock listener
    listener = type('obj', (object,), {'stop': lambda: None})
    app = BluetoothMapperApp(ConfigManager(), listener)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
