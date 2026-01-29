import threading
import time

class GestureDetector:
    def __init__(self, config_manager, action_executor):
        self.config = config_manager
        self.executor = action_executor
        
        self.tap_count = 0
        self.timer = None
        self.lock = threading.Lock()

    def on_play_pause(self):
        with self.lock:
            self.tap_count += 1
            if self.timer:
                self.timer.cancel()
            
            # Get window from config, default to 400ms
            window = self.config.get_setting("gesture_window_ms") or 400
            self.timer = threading.Timer(window / 1000.0, self._process_taps)
            self.timer.start()

    def _process_taps(self):
        with self.lock:
            count = self.tap_count
            self.tap_count = 0
            self.timer = None

        if count == 1:
            action = self.config.get_mapping("play_pause_single")
            self.executor.execute(action)
        elif count == 2:
            action = self.config.get_mapping("play_pause_double")
            self.executor.execute(action)
        elif count >= 3:
            action = self.config.get_mapping("play_pause_triple")
            self.executor.execute(action)

    def on_next_track(self):
        action = self.config.get_mapping("next_track")
        self.executor.execute(action)

    def on_previous_track(self):
        action = self.config.get_mapping("previous_track")
        self.executor.execute(action)
