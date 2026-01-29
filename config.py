import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "mappings": {
        "play_pause_single": "none",
        "play_pause_double": "next_track",
        "play_pause_triple": "previous_track",
        "next_track": "next_track",
        "previous_track": "previous_track"
    },
    "settings": {
        "start_with_windows": False,
        "gesture_window_ms": 400
    }
}

class ConfigManager:
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            return DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_file, 'r') as f:
                loaded_config = json.load(f)
                # Ensure all default keys exist in the loaded config (migration/integrity)
                for key, value in DEFAULT_CONFIG.items():
                    if key not in loaded_config:
                        loaded_config[key] = value
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey not in loaded_config[key]:
                                loaded_config[key][subkey] = subvalue
                return loaded_config
        except (json.JSONDecodeError, IOError):
            return DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")

    def get_mapping(self, gesture):
        return self.config["mappings"].get(gesture, "none")

    def set_mapping(self, gesture, action):
        self.config["mappings"][gesture] = action
        self.save_config()

    def get_setting(self, setting_name):
        return self.config["settings"].get(setting_name)

    def set_setting(self, setting_name, value):
        self.config["settings"][setting_name] = value
        self.save_config()
