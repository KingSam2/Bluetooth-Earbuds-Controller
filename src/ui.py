import customtkinter as ctk
import threading
import time
from .config_manager import ConfigManager
from .bluetooth_manager import BluetoothManager

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class BluetoothBudsControlApp(ctk.CTk):
    def __init__(self, config_manager, bluetooth_manager, gesture_engine, on_save_callback=None):
        super().__init__()

        self.config = config_manager
        self.bluetooth = bluetooth_manager
        self.gesture_engine = gesture_engine
        self.on_save_callback = on_save_callback

        self.title("Bluetooth Buds Control")
        self.geometry("600x650")
        self.resizable(False, False)

        # Main layout container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        self._create_header()

        # Device Selection
        self._create_device_selection()

        # Gesture Settings
        self._create_gesture_settings()

        # Additional Options
        self._create_options()

        # Footer / Buttons
        self._create_footer()

        # Status Bar
        self._create_status_bar()

        # Load initial values
        self._load_values()

        # Start status update loop
        self.after(2000, self._update_status)

    def _create_header(self):
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        # Icon placeholder (Text for now)
        icon_label = ctk.CTkLabel(header_frame, text="🎧", font=("Arial", 40))
        icon_label.pack(side="left", padx=(0, 10))

        title_label = ctk.CTkLabel(header_frame, text="Bluetooth Buds Control", font=("Arial", 20, "bold"))
        title_label.pack(side="top", anchor="w")

        desc_label = ctk.CTkLabel(header_frame, text="Remap your Bluetooth earbud gestures to system actions.", text_color="gray")
        desc_label.pack(side="top", anchor="w")

    def _create_device_selection(self):
        self.device_frame = ctk.CTkFrame(self.main_frame)
        self.device_frame.pack(fill="x", pady=(0, 20))

        label = ctk.CTkLabel(self.device_frame, text="Target Bluetooth Device", font=("Arial", 14, "bold"))
        label.pack(anchor="w", padx=10, pady=(10, 5))

        self.device_var = ctk.StringVar(value="Select Device")
        self.device_dropdown = ctk.CTkOptionMenu(
            self.device_frame,
            variable=self.device_var,
            values=["Loading..."]
        )
        self.device_dropdown.pack(fill="x", padx=10, pady=(0, 10))

        # Populate devices in background
        threading.Thread(target=self._refresh_devices, daemon=True).start()

    def _refresh_devices(self):
        devices = self.bluetooth.get_paired_devices()
        if not devices:
            devices = ["No Devices Found"]

        self.device_dropdown.configure(values=devices)

        # Set current selection if exists in list
        current_target = self.config.get_target_device()
        if current_target and current_target in devices:
            self.device_var.set(current_target)
        elif devices and devices[0] != "No Devices Found":
            self.device_var.set(devices[0])

    def _create_gesture_settings(self):
        self.gesture_frame = ctk.CTkFrame(self.main_frame)
        self.gesture_frame.pack(fill="x", pady=(0, 20))

        title_label = ctk.CTkLabel(self.gesture_frame, text="Gesture Settings", font=("Arial", 14, "bold"))
        title_label.pack(anchor="w", padx=10, pady=(10, 5))

        # Rows
        self.single_tap_var = self._create_gesture_row("👆 Single Tap", "single_tap")
        self.double_tap_var = self._create_gesture_row("✌️ Double Tap", "double_tap")
        self.triple_tap_var = self._create_gesture_row("🤟 Triple Tap", "triple_tap")
        self.long_press_var = self._create_gesture_row("🔒 Long Press", "long_press")

    def _create_gesture_row(self, label_text, config_key):
        row_frame = ctk.CTkFrame(self.gesture_frame, fg_color="transparent")
        row_frame.pack(fill="x", padx=10, pady=5)

        label = ctk.CTkLabel(row_frame, text=label_text, width=120, anchor="w")
        label.pack(side="left")

        # Get available actions from actions.py? Hardcoded for UI simplicity or fetched.
        from .actions import ActionManager
        actions = ActionManager().get_available_actions()

        var = ctk.StringVar()
        dropdown = ctk.CTkOptionMenu(row_frame, variable=var, values=actions)
        dropdown.pack(side="right", fill="x", expand=True)

        return var

    def _create_options(self):
        self.options_frame = ctk.CTkFrame(self.main_frame)
        self.options_frame.pack(fill="x", pady=(0, 20))

        title_label = ctk.CTkLabel(self.options_frame, text="Additional Options", font=("Arial", 14, "bold"))
        title_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.notif_var = ctk.BooleanVar()
        self.notif_check = ctk.CTkCheckBox(self.options_frame, text="Enable Notifications", variable=self.notif_var)
        self.notif_check.pack(anchor="w", padx=10, pady=5)

        self.start_var = ctk.BooleanVar()
        self.start_check = ctk.CTkCheckBox(self.options_frame, text="Start with Windows", variable=self.start_var)
        self.start_check.pack(anchor="w", padx=10, pady=5)

    def _create_footer(self):
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=10)

        cancel_btn = ctk.CTkButton(footer_frame, text="Cancel", fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"), command=self.destroy)
        cancel_btn.pack(side="right", padx=(10, 0))

        save_btn = ctk.CTkButton(footer_frame, text="Save", command=self._on_save)
        save_btn.pack(side="right")

    def _create_status_bar(self):
        self.status_bar = ctk.CTkLabel(self, text="Status: Checking...", anchor="w", fg_color=("gray90", "gray20"), padx=10)
        self.status_bar.pack(fill="x", side="bottom")

    def _load_values(self):
        self.single_tap_var.set(self.config.get_gesture("single_tap") or "None")
        self.double_tap_var.set(self.config.get_gesture("double_tap") or "None")
        self.triple_tap_var.set(self.config.get_gesture("triple_tap") or "None")
        self.long_press_var.set(self.config.get_gesture("long_press") or "None")

        self.notif_var.set(self.config.get_option("notifications"))
        self.start_var.set(self.config.get_option("start_with_windows"))

    def _on_save(self):
        # Save to config
        self.config.set_gesture("single_tap", self.single_tap_var.get())
        self.config.set_gesture("double_tap", self.double_tap_var.get())
        self.config.set_gesture("triple_tap", self.triple_tap_var.get())
        self.config.set_gesture("long_press", self.long_press_var.get())

        self.config.set_option("notifications", self.notif_var.get())
        self.config.set_option("start_with_windows", self.start_var.get())

        selected_device = self.device_var.get()
        if selected_device != "Select Device" and selected_device != "No Devices Found" and selected_device != "Loading...":
            self.config.set_target_device(selected_device)

        self.config.save_config()
        print("Configuration saved.")

        if self.on_save_callback:
            self.on_save_callback()

        # Just hide window instead of destroy if we want it to run in tray?
        # For now, let's assume minimizing or just keeping it open.
        # But usually 'Save' might close the config window if it's a settings dialog.
        # Since this is the main window, we probably just want to save.
        pass

    def _update_status(self):
        target = self.device_var.get()
        if not target or target in ["Select Device", "Loading...", "No Devices Found"]:
            self.status_bar.configure(text="Status: No device selected")
        else:
            # Check connection
            connected = self.bluetooth.is_device_connected(target)
            if connected:
                self.status_bar.configure(text=f"Status: Connected to {target} 🔵", text_color="green")
            else:
                self.status_bar.configure(text=f"Status: {target} Not Connected ⚪", text_color="orange")

        self.after(5000, self._update_status)
