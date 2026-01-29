import time
import threading
import keyboard
from .actions import ActionManager
from .bluetooth_manager import BluetoothManager
from .config_manager import ConfigManager

# Time thresholds in seconds
LONG_PRESS_THRESHOLD = 0.5
MULTI_TAP_WINDOW = 0.4

class GestureEngine:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.actions = ActionManager()
        self.bluetooth = BluetoothManager()

        self.tap_count = 0
        self.last_tap_time = 0
        self.timer = None
        self.is_running = False

        # State for long press detection
        self.key_down_time = 0
        self.is_key_down = False
        self.hooks = []

    def start(self):
        if self.is_running:
            return

        self.is_running = True
        # Use on_press_key and on_release_key with suppress=True to block default behavior
        # 'play/pause media' is the scan code name usually.
        # We hook both to ensure we capture the full lifecycle and suppress it.

        # Note: hook_key is lower level. on_press_key is higher level.
        # on_press_key returns a hook that we can remove later.

        print("Gesture Engine Started. Listening for 'play/pause media'...")
        try:
            h1 = keyboard.on_press_key('play/pause media', self._on_key_down, suppress=True)
            h2 = keyboard.on_release_key('play/pause media', self._on_key_up, suppress=True)
            self.hooks.extend([h1, h2])
        except ValueError:
            # Fallback if key name is not found (e.g. some systems)
            # Try 'play/pause'
            try:
                h1 = keyboard.on_press_key('play/pause', self._on_key_down, suppress=True)
                h2 = keyboard.on_release_key('play/pause', self._on_key_up, suppress=True)
                self.hooks.extend([h1, h2])
            except Exception as e:
                print(f"Failed to hook key: {e}")

    def stop(self):
        if not self.is_running:
            return
        self.is_running = False
        for h in self.hooks:
            keyboard.unhook(h)
        self.hooks = []

    def _should_intercept(self):
        # Check if target device is selected and connected
        target_device = self.config.get_target_device()
        if target_device:
            return self.bluetooth.is_device_connected(target_device)
        # If no target device selected, maybe intercept always?
        # Requirement said "select specific bluetooth device to choose to apply".
        # If none selected, assume disabled or default?
        # Let's assume if no device is selected, we do NOT intercept (pass through).
        return False

    def _on_key_down(self, event):
        if not self.is_running:
            return

        # If we shouldn't intercept, we should technically forward the event?
        # With suppress=True, we swallowed it.
        # If we determine we shouldn't have intercepted, we must re-emit it.
        if not self._should_intercept():
            self._re_emit(event)
            return

        if not self.is_key_down:
            self.is_key_down = True
            self.key_down_time = time.time()

    def _on_key_up(self, event):
        if not self.is_running:
            return

        if not self._should_intercept():
            self._re_emit(event)
            return

        if self.is_key_down:
            self.is_key_down = False
            press_duration = time.time() - self.key_down_time

            if press_duration > LONG_PRESS_THRESHOLD:
                self._handle_long_press()
            else:
                self._handle_tap()

    def _re_emit(self, event):
        # Re-emit the event so the system handles it.
        # We must unhook temporarily to avoid infinite loops since we are suppressing.

        # Remove hooks
        for h in self.hooks:
            keyboard.unhook(h)
        self.hooks = []

        # Send the event
        keyboard.send(event.name, do_press=(event.event_type=='down'), do_release=(event.event_type=='up'))

        # Re-add hooks (using internal logic similar to start, but without setting is_running=True again if already true)
        # Actually, just calling start() might be complex if we are inside the callback.
        # But since 'keyboard' callbacks are often in a separate thread, it might be ok.
        # Let's verify: start() checks is_running.
        # We didn't change is_running. So start() would return immediately.
        # We need to manually re-add hooks.

        try:
            h1 = keyboard.on_press_key('play/pause media', self._on_key_down, suppress=True)
            h2 = keyboard.on_release_key('play/pause media', self._on_key_up, suppress=True)
            self.hooks.extend([h1, h2])
        except ValueError:
            try:
                h1 = keyboard.on_press_key('play/pause', self._on_key_down, suppress=True)
                h2 = keyboard.on_release_key('play/pause', self._on_key_up, suppress=True)
                self.hooks.extend([h1, h2])
            except Exception as e:
                print(f"Failed to re-hook key: {e}")

    def _handle_long_press(self):
        print("Detected: Long Press")
        action = self.config.get_gesture("long_press")
        self._execute_action(action)
        self.tap_count = 0
        if self.timer:
            self.timer.cancel()

    def _handle_tap(self):
        self.tap_count += 1

        if self.timer:
            self.timer.cancel()

        self.timer = threading.Timer(MULTI_TAP_WINDOW, self._resolve_taps)
        self.timer.start()

    def _resolve_taps(self):
        action = None
        if self.tap_count == 1:
            print("Detected: Single Tap")
            action = self.config.get_gesture("single_tap")
        elif self.tap_count == 2:
            print("Detected: Double Tap")
            action = self.config.get_gesture("double_tap")
        elif self.tap_count >= 3:
            print("Detected: Triple Tap")
            action = self.config.get_gesture("triple_tap")

        self.tap_count = 0
        self._execute_action(action)

    def _execute_action(self, action_name):
        if action_name:
            # If the action is "Play / Pause", we need to send the key.
            # But we are suppressing it!
            # So we must use a method that bypasses our suppression or unhook temporarily.
            # `actions.py` uses `pyautogui`.
            # `pyautogui` uses different injection method usually.
            self.actions.execute(action_name)
