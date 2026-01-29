import platform
import subprocess
import shutil

class BluetoothManager:
    def __init__(self):
        self.os_type = platform.system()

    def get_paired_devices(self):
        """
        Returns a list of paired/connected Bluetooth devices.
        Returns: [str] list of device names.
        """
        if self.os_type == "Windows":
            return self._get_windows_devices()
        else:
            return self._get_mock_devices()

    def is_device_connected(self, device_name):
        """
        Checks if a specific device is connected.
        """
        if not device_name:
            return False

        if self.os_type == "Windows":
            return self._check_windows_connection(device_name)
        else:
            return self._check_mock_connection(device_name)

    def _get_windows_devices(self):
        try:
            # PowerShell command to get Bluetooth devices that are paired and active (Status=OK)
            # This avoids command injection by not including user input in the command.
            cmd = 'Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -eq "OK"} | Select-Object -ExpandProperty FriendlyName'

            # Use shell=False is generally safer, but here we invoke powershell directly.
            # We are not passing user input to the command string.
            result = subprocess.run(
                ["powershell", "-Command", cmd],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                print(f"PowerShell error: {result.stderr}")
                return []

            devices = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            return sorted(list(set(devices)))
        except Exception as e:
            print(f"Error getting Bluetooth devices: {e}")
            return []

    def _check_windows_connection(self, device_name):
        # Implementation: Fetch all active devices and check if the target is in the list.
        # This effectively avoids any command injection since we don't pass device_name to the shell.
        active_devices = self._get_windows_devices()
        return device_name in active_devices

    def _get_mock_devices(self):
        # Mock devices for development/Linux environment
        return ["Galaxy Buds Pro", "AirPods", "Sony WH-1000XM4", "Logitech MX Master"]

    def _check_mock_connection(self, device_name):
        # Mock logic: Always say yes for testing
        return True
