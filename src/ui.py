import customtkinter as ctk
import threading
import time
import keyboard
import pynput
try:
    import inputs
except ImportError:
    inputs = None

# Import our new lightweight Raw Input Monitor
from .win_raw_input import RawInputMonitor, enumerate_devices

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
        self.geometry("600x700")
        self.resizable(False, False)

        # Tab Control
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=20)

        self.settings_tab = self.tab_view.add("Settings")
        self.debug_tab = self.tab_view.add("Input Debugger")

        # --- Settings Tab ---
        self._create_header(self.settings_tab)
        self._create_device_selection(self.settings_tab)
        self._create_gesture_settings(self.settings_tab)
        self._create_options(self.settings_tab)
        self._create_footer(self.settings_tab)

        # --- Debug Tab ---
        self._create_debug_tab(self.debug_tab)

        # Status Bar (global)
        self._create_status_bar()

        # Load initial values
        self._load_values()

        # Start status update loop
        self.after(2000, self._update_status)

        # Debug state
        self.is_debugging = False
        self.keyboard_listener = None
        self.mouse_listener = None
        self.gamepad_thread = None
        self.stop_gamepad_thread = False

        # Log Queue
        self.log_queue = []
        self.log_lock = threading.Lock()
        self.after(100, self._process_log_queue)

        # Raw Input Monitor
        self.raw_monitor = RawInputMonitor(self._queue_debug_log)

    def _create_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        icon_label = ctk.CTkLabel(header_frame, text="🎧", font=("Arial", 40))
        icon_label.pack(side="left", padx=(0, 10))

        title_label = ctk.CTkLabel(header_frame, text="Bluetooth Buds Control", font=("Arial", 20, "bold"))
        title_label.pack(side="top", anchor="w")

        desc_label = ctk.CTkLabel(header_frame, text="Remap your Bluetooth earbud gestures to system actions.", text_color="gray")
        desc_label.pack(side="top", anchor="w")

    def _create_device_selection(self, parent):
        self.device_frame = ctk.CTkFrame(parent)
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

        threading.Thread(target=self._refresh_devices, daemon=True).start()

    def _refresh_devices(self):
        devices = self.bluetooth.get_paired_devices()
        if not devices:
            devices = ["No Devices Found"]

        self.device_dropdown.configure(values=devices)

        current_target = self.config.get_target_device()
        if current_target and current_target in devices:
            self.device_var.set(current_target)
        elif devices and devices[0] != "No Devices Found":
            self.device_var.set(devices[0])

    def _create_gesture_settings(self, parent):
        self.gesture_frame = ctk.CTkFrame(parent)
        self.gesture_frame.pack(fill="x", pady=(0, 20))

        title_label = ctk.CTkLabel(self.gesture_frame, text="Gesture Settings", font=("Arial", 14, "bold"))
        title_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.single_tap_var = self._create_gesture_row(self.gesture_frame, "👆 Single Tap", "single_tap")
        self.double_tap_var = self._create_gesture_row(self.gesture_frame, "✌️ Double Tap", "double_tap")
        self.triple_tap_var = self._create_gesture_row(self.gesture_frame, "🤟 Triple Tap", "triple_tap")
        self.long_press_var = self._create_gesture_row(self.gesture_frame, "🔒 Long Press", "long_press")

    def _create_gesture_row(self, parent, label_text, config_key):
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=10, pady=5)

        label = ctk.CTkLabel(row_frame, text=label_text, width=120, anchor="w")
        label.pack(side="left")

        from .actions import ActionManager
        actions = ActionManager().get_available_actions()

        var = ctk.StringVar()
        dropdown = ctk.CTkOptionMenu(row_frame, variable=var, values=actions)
        dropdown.pack(side="right", fill="x", expand=True)

        return var

    def _create_options(self, parent):
        self.options_frame = ctk.CTkFrame(parent)
        self.options_frame.pack(fill="x", pady=(0, 20))

        title_label = ctk.CTkLabel(self.options_frame, text="Additional Options", font=("Arial", 14, "bold"))
        title_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.notif_var = ctk.BooleanVar()
        self.notif_check = ctk.CTkCheckBox(self.options_frame, text="Enable Notifications", variable=self.notif_var)
        self.notif_check.pack(anchor="w", padx=10, pady=5)

        self.start_var = ctk.BooleanVar()
        self.start_check = ctk.CTkCheckBox(self.options_frame, text="Start with Windows", variable=self.start_var)
        self.start_check.pack(anchor="w", padx=10, pady=5)

    def _create_footer(self, parent):
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x", pady=10)

        cancel_btn = ctk.CTkButton(footer_frame, text="Cancel", fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"), command=self.destroy)
        cancel_btn.pack(side="right", padx=(10, 0))

        save_btn = ctk.CTkButton(footer_frame, text="Save", command=self._on_save)
        save_btn.pack(side="right")

    def _create_debug_tab(self, parent):
        label = ctk.CTkLabel(parent, text="Press buttons on your Bluetooth device to see what input is detected.\nMonitoring: Keyboard, Mouse, Gamepads, Raw HID (Consumer Page).", text_color="gray", wraplength=500)
        label.pack(pady=10)

        # Filters
        filter_frame = ctk.CTkFrame(parent, fg_color="transparent")
        filter_frame.pack(fill="x", pady=5)

        self.log_mouse_move_var = ctk.BooleanVar(value=False)
        self.log_mouse_click_var = ctk.BooleanVar(value=True)
        self.log_kbd_var = ctk.BooleanVar(value=True)
        self.log_hid_var = ctk.BooleanVar(value=True)

        ctk.CTkCheckBox(filter_frame, text="Mouse Move", variable=self.log_mouse_move_var).pack(side="left", padx=5)
        ctk.CTkCheckBox(filter_frame, text="Mouse Click", variable=self.log_mouse_click_var).pack(side="left", padx=5)
        ctk.CTkCheckBox(filter_frame, text="Keyboard", variable=self.log_kbd_var).pack(side="left", padx=5)
        ctk.CTkCheckBox(filter_frame, text="HID/Raw", variable=self.log_hid_var).pack(side="left", padx=5)

        control_frame = ctk.CTkFrame(parent, fg_color="transparent")
        control_frame.pack(fill="x", pady=5)

        self.debug_btn = ctk.CTkButton(control_frame, text="Start Listening", command=self._toggle_debug)
        self.debug_btn.pack(pady=5)

        self.scan_btn = ctk.CTkButton(control_frame, text="Scan Input Devices", command=self._scan_devices, fg_color="teal")
        self.scan_btn.pack(pady=5)

        self.clear_debug_btn = ctk.CTkButton(control_frame, text="Clear Log", command=self._clear_debug_log, fg_color="gray")
        self.clear_debug_btn.pack(pady=5)

        self.debug_log = ctk.CTkTextbox(parent, width=500, height=350)
        self.debug_log.pack(pady=10, fill="both", expand=True)
        self.debug_log.insert("0.0", "Logs will appear here...\n")

    def _toggle_debug(self):
        if not self.is_debugging:
            self.is_debugging = True
            self.debug_btn.configure(text="Stop Listening", fg_color="red", hover_color="darkred")
            self.debug_log.insert("end", "\n--- Listening Started (All Sources) ---\n")
            self.debug_log.see("end")
            self._start_listeners()
        else:
            self.is_debugging = False
            self.debug_btn.configure(text="Start Listening", fg_color=("blue", "#1f6aa5"))
            self.debug_log.insert("end", "\n--- Listening Stopped ---\n")
            self.debug_log.see("end")
            self._stop_listeners()

    def _start_listeners(self):
        # 1. Keyboard (Pynput)
        try:
            self.keyboard_listener = pynput.keyboard.Listener(on_press=self._on_pynput_press)
            self.keyboard_listener.start()
        except Exception as e:
            self._queue_debug_log(f"Error starting keyboard listener: {e}\n")

        # 2. Mouse (Pynput)
        try:
            self.mouse_listener = pynput.mouse.Listener(on_move=self._on_pynput_move, on_click=self._on_pynput_click, on_scroll=self._on_pynput_scroll)
            self.mouse_listener.start()
        except Exception as e:
            self._queue_debug_log(f"Error starting mouse listener: {e}\n")

        # 3. Gamepad/HID (inputs)
        if inputs:
            self.stop_gamepad_thread = False
            self.gamepad_thread = threading.Thread(target=self._poll_gamepads, daemon=True)
            self.gamepad_thread.start()
        else:
            self._queue_debug_log("Warning: 'inputs' library not available.\n")

        # 4. Raw Input (Consumer/HID)
        try:
            self.raw_monitor.start()
        except Exception as e:
            self._queue_debug_log(f"Error starting Raw Input Monitor: {e}\n")

    def _stop_listeners(self):
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

        self.stop_gamepad_thread = True

        if self.raw_monitor:
            self.raw_monitor.stop()

    # --- Callbacks ---
    def _queue_debug_log(self, msg):
        with self.log_lock:
            self.log_queue.append(msg)

    def _process_log_queue(self):
        with self.log_lock:
            if self.log_queue:
                # Flush all messages
                text = "".join(self.log_queue)
                self.log_queue.clear()

                # Update UI
                self.debug_log.insert("end", text)
                self.debug_log.see("end")

                # Trim buffer if too long
                content = self.debug_log.get("1.0", "end")
                if len(content) > 50000: # Max characters
                    self.debug_log.delete("1.0", "end-10000c") # Delete oldest chars

        self.after(100, self._process_log_queue)

    def _clear_debug_log(self):
        self.debug_log.delete("1.0", "end")
        self.debug_log.insert("0.0", "Logs cleared.\n")

    def _on_pynput_press(self, key):
        if not self.log_kbd_var.get(): return
        try:
            msg = f"[Keyboard] Key: {key.char}\n"
        except AttributeError:
            msg = f"[Keyboard] Special Key: {key}\n"
        self._queue_debug_log(msg)

    def _on_pynput_move(self, x, y):
        if not self.log_mouse_move_var.get(): return
        # Limit move logging frequency? Batching handles it, but still generates string objects.
        # But user explicitly enabled it, so let it flow.
        msg = f"[Mouse] Move: ({x}, {y})\n"
        self._queue_debug_log(msg)

    def _on_pynput_click(self, x, y, button, pressed):
        if not self.log_mouse_click_var.get(): return
        if pressed:
            msg = f"[Mouse] Click: {button} at ({x}, {y})\n"
            self._queue_debug_log(msg)

    def _on_pynput_scroll(self, x, y, dx, dy):
        if not self.log_mouse_click_var.get(): return # Group scroll with click for simplicity or add separate var
        msg = f"[Mouse] Scroll: ({dx}, {dy})\n"
        self._queue_debug_log(msg)

    def _poll_gamepads(self):
        while not self.stop_gamepad_thread:
            if not self.log_hid_var.get():
                time.sleep(0.5)
                continue

            try:
                events = inputs.get_gamepad()
                for event in events:
                    if self.stop_gamepad_thread:
                        break
                    msg = f"[HID/Gamepad] Code: {event.code}, State: {event.state}, Type: {event.ev_type}\n"
                    self._queue_debug_log(msg)
            except Exception:
                time.sleep(0.1)

    def _scan_devices(self):
        self._queue_debug_log("\n--- Scanning for HID Devices ---\n")

        # Run in thread to prevent freezing
        def scan_task():
            devices = enumerate_devices()
            for dev in devices:
                self._queue_debug_log(f"{dev}\n")
            self._queue_debug_log("--- Scan Complete ---\n")

        threading.Thread(target=scan_task, daemon=True).start()

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

    def _update_status(self):
        target = self.device_var.get()
        if not target or target in ["Select Device", "Loading...", "No Devices Found"]:
            self.status_bar.configure(text="Status: No device selected")
        else:
            connected = self.bluetooth.is_device_connected(target)
            if connected:
                self.status_bar.configure(text=f"Status: Connected to {target} 🔵", text_color="green")
            else:
                self.status_bar.configure(text=f"Status: {target} Not Connected ⚪", text_color="orange")

        self.after(5000, self._update_status)
