import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "gestures": {
        "single_tap": "Play / Pause",
        "double_tap": "Scroll Down",
        "triple_tap": "Alt + Tab",
        "long_press": "Switch Desktop"
    },
    "options": {
        "notifications": True,
        "start_with_windows": False
    },
    "target_device": None
}

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return DEFAULT_CONFIG.copy()

        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

    def get_gesture(self, gesture_type):
        return self.config.get("gestures", {}).get(gesture_type)

    def set_gesture(self, gesture_type, action):
        if "gestures" not in self.config:
            self.config["gestures"] = {}
        self.config["gestures"][gesture_type] = action

    def get_option(self, option_name):
        return self.config.get("options", {}).get(option_name)

    def set_option(self, option_name, value):
        if "options" not in self.config:
            self.config["options"] = {}
        self.config["options"][option_name] = value

    def get_target_device(self):
        return self.config.get("target_device")

    def set_target_device(self, device_name):
        self.config["target_device"] = device_name
