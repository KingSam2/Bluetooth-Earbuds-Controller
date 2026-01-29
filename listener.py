import keyboard
import threading
import time

class InputListener:
    def __init__(self, gesture_detector):
        self.detector = gesture_detector
        self.running = False
        self.hooks = []

    def start(self):
        if self.running:
            return
        
        self.running = True
        print("Starting listener...")
        
        try:
            # We use add_hotkey or on_press_key.
            # 'play/pause media' is the standard name in keyboard lib for the media key.
            # 'next track', 'previous track'
            
            # Note: The `keyboard` library might throw errors if it can't access hooks (needs sudo on Linux, admin on Windows)
            # We catch this in the main app, but here we just try to register.
            
            self.hooks.append(keyboard.on_press_key("play/pause media", self._on_play_pause, suppress=False))
            self.hooks.append(keyboard.on_press_key("next track", self._on_next_track, suppress=False))
            self.hooks.append(keyboard.on_press_key("previous track", self._on_previous_track, suppress=False))
            
            print("Listener started successfully.")
            
        except ImportError:
             print("Keyboard library not found or failed to load backend.")
        except Exception as e:
            print(f"Failed to start listener: {e}")
            self.running = False

    def stop(self):
        if not self.running:
            return
        
        print("Stopping listener...")
        try:
            # Remove all hooks
            keyboard.unhook_all()
            self.hooks = []
        except Exception as e:
            print(f"Error stopping listener: {e}")
            
        self.running = False

    def _on_play_pause(self, event):
        # event is a keyboard.KeyboardEvent
        # We only care about key down (on_press_key handles this)
        self.detector.on_play_pause()

    def _on_next_track(self, event):
        self.detector.on_next_track()

    def _on_previous_track(self, event):
        self.detector.on_previous_track()
