import pyautogui
import platform
import time
import sys

# Define OS check
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import ctypes

class ActionExecutor:
    def __init__(self):
        self.actions = {
            "none": self.do_nothing,
            "play_pause": self.media_play_pause,
            "next_track": self.media_next,
            "previous_track": self.media_prev,
            "volume_up": self.volume_up,
            "volume_down": self.volume_down,
            "volume_mute": self.volume_mute,
            "scroll_up": self.scroll_up,
            "scroll_down": self.scroll_down,
            "alt_tab": self.alt_tab,
            "switch_desktop_next": self.switch_desktop_next,
            "switch_desktop_prev": self.switch_desktop_prev,
            "lock_screen": self.lock_screen,
        }
        
        # Configure pyautogui to be a bit faster? Default is usually fine.
        # pyautogui.PAUSE = 0.1 

    def execute(self, action_name):
        if action_name in self.actions:
            print(f"Executing action: {action_name}")
            try:
                self.actions[action_name]()
            except Exception as e:
                print(f"Error executing {action_name}: {e}")
        else:
            print(f"Unknown action: {action_name}")

    def do_nothing(self):
        pass

    def media_play_pause(self):
        pyautogui.press("playpause")

    def media_next(self):
        pyautogui.press("nexttrack")

    def media_prev(self):
        pyautogui.press("prevtrack")

    def volume_up(self):
        pyautogui.press("volumeup")

    def volume_down(self):
        pyautogui.press("volumedown")

    def volume_mute(self):
        pyautogui.press("volumemute")

    def scroll_up(self):
        pyautogui.scroll(200)

    def scroll_down(self):
        pyautogui.scroll(-200)

    def alt_tab(self):
        # Using hotkey for alt+tab
        # Note: In some cases, simple 'alt' + 'tab' press just switches to the last window immediately
        # which is usually desired behavior for a quick gesture.
        pyautogui.hotkey('alt', 'tab')

    def switch_desktop_next(self):
        # Windows 10/11: Ctrl + Win + Right Arrow
        pyautogui.hotkey('ctrl', 'win', 'right')

    def switch_desktop_prev(self):
        # Windows 10/11: Ctrl + Win + Left Arrow
        pyautogui.hotkey('ctrl', 'win', 'left')

    def lock_screen(self):
        if IS_WINDOWS:
            try:
                ctypes.windll.user32.LockWorkStation()
            except Exception as e:
                print(f"Failed to lock screen: {e}")
        else:
            print("Lock screen is only supported on Windows.")
