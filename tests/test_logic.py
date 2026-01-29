import unittest
import time
import sys
from unittest.mock import MagicMock, patch

# Mock modules that might not exist or work in headless
sys.modules['keyboard'] = MagicMock()
sys.modules['pyautogui'] = MagicMock()
sys.modules['customtkinter'] = MagicMock()

from src.gesture_engine import GestureEngine
from src.config_manager import ConfigManager
from src.bluetooth_manager import BluetoothManager

class TestGestureEngine(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock(spec=ConfigManager)
        # Setup default actions
        self.config.get_gesture.side_effect = lambda x: f"Action_{x}"
        self.config.get_target_device.return_value = "TestDevice"

        # Mock BluetoothManager
        self.bluetooth_patcher = patch('src.gesture_engine.BluetoothManager')
        self.mock_bluetooth = self.bluetooth_patcher.start().return_value
        self.mock_bluetooth.is_device_connected.return_value = True

        # Mock ActionManager
        self.action_patcher = patch('src.gesture_engine.ActionManager')
        self.mock_actions = self.action_patcher.start().return_value

        self.engine = GestureEngine(self.config)
        self.engine.is_running = True # Force running

    def tearDown(self):
        self.bluetooth_patcher.stop()
        self.action_patcher.stop()
        if self.engine.timer:
            self.engine.timer.cancel()

    def simulate_tap(self):
        # Key Down
        event_down = MagicMock()
        event_down.event_type = "down"

        from src.gesture_engine import keyboard
        # Note: In new implementation we don't check event_type in the callback
        # because the callback IS specifically for down or up.
        # But we pass the event object.

        self.engine._on_key_down(event_down)

        time.sleep(0.05) # Short press

        # Key Up
        event_up = MagicMock()
        event_up.event_type = "up"
        self.engine._on_key_up(event_up)

    def test_single_tap(self):
        print("\nTesting Single Tap...")
        self.simulate_tap()

        # Wait for timer to expire
        time.sleep(0.5)

        self.mock_actions.execute.assert_called_with("Action_single_tap")

    def test_double_tap(self):
        print("\nTesting Double Tap...")
        self.simulate_tap()
        time.sleep(0.1) # Wait less than timeout
        self.simulate_tap()

        # Wait for timer to expire
        time.sleep(0.5)

        self.mock_actions.execute.assert_called_with("Action_double_tap")

    def test_triple_tap(self):
        print("\nTesting Triple Tap...")
        self.simulate_tap()
        time.sleep(0.1)
        self.simulate_tap()
        time.sleep(0.1)
        self.simulate_tap()

        # Wait for timer to expire
        time.sleep(0.5)

        self.mock_actions.execute.assert_called_with("Action_triple_tap")

    def test_device_not_connected(self):
        print("\nTesting Device Not Connected...")
        self.mock_bluetooth.is_device_connected.return_value = False

        self.simulate_tap()
        time.sleep(0.5)

        self.mock_actions.execute.assert_not_called()

if __name__ == '__main__':
    unittest.main()
