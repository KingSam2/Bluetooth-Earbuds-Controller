import keyboard
import platform
import sys

# Try to import pyautogui, but don't crash if no display is found (headless/linux test env)
try:
    import pyautogui
except (ImportError, KeyError):
    pyautogui = None

class ActionManager:
    def __init__(self):
        self.os_type = platform.system()

    def execute(self, action_name):
        print(f"Executing action: {action_name}")

        if pyautogui is None:
            print("Warning: pyautogui not available (headless environment?)")

        if action_name == "Play / Pause":
            if pyautogui: pyautogui.press("playpause")

        elif action_name == "Scroll Down":
            # Scroll down
            if pyautogui: pyautogui.scroll(-500)

        elif action_name == "Alt + Tab":
            # Quick Alt-Tab
            with keyboard.pressed('alt'):
                keyboard.press_and_release('tab')

        elif action_name == "Switch Desktop":
            # Windows: Ctrl + Win + Left/Right
            # For this, let's toggle to the right
            keyboard.send('ctrl+windows+right')

        elif action_name == "Volume Up":
            if pyautogui: pyautogui.press("volumeup")

        elif action_name == "Volume Down":
            if pyautogui: pyautogui.press("volumedown")

        elif action_name == "Next Track":
            if pyautogui: pyautogui.press("nexttrack")

        elif action_name == "Previous Track":
            if pyautogui: pyautogui.press("prevtrack")

        elif action_name == "Lock Screen":
            # Windows + L
            keyboard.send('windows+l')

        elif action_name == "None":
            pass

        else:
            print(f"Unknown action: {action_name}")

    def get_available_actions(self):
        return [
            "None",
            "Play / Pause",
            "Scroll Down",
            "Alt + Tab",
            "Switch Desktop",
            "Volume Up",
            "Volume Down",
            "Next Track",
            "Previous Track",
            "Lock Screen"
        ]
