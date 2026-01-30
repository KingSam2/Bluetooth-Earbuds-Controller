import ctypes
from ctypes import wintypes
import threading
import time
import platform

# Only valid on Windows
if platform.system() != "Windows":
    # Mock class for non-Windows environments
    class RawInputMonitor:
        def __init__(self, callback):
            self.callback = callback
            self.running = False
        def start(self):
            self.running = True
            threading.Thread(target=self._mock_loop, daemon=True).start()
        def stop(self):
            self.running = False
        def _mock_loop(self):
            while self.running:
                time.sleep(1)

    def enumerate_devices():
        return ["Mock Device 1", "Mock Device 2 (Bluetooth)"]

else:
    # Windows Implementation
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # Constants
    WM_INPUT = 0x00FF
    RIM_TYPEMOUSE = 0
    RIM_TYPEKEYBOARD = 1
    RIM_TYPEHID = 2
    RIDEV_INPUTSINK = 0x00000100
    RID_INPUT = 0x10000003
    RIDI_DEVICENAME = 0x20000007

    # Usage Pages
    HID_USAGE_PAGE_GENERIC = 0x01
    HID_USAGE_GENERIC_MOUSE = 0x02
    HID_USAGE_GENERIC_JOYSTICK = 0x04
    HID_USAGE_GENERIC_GAMEPAD = 0x05
    HID_USAGE_GENERIC_KEYBOARD = 0x06

    HID_USAGE_PAGE_CONSUMER = 0x0C
    HID_USAGE_CONSUMER_CONTROL = 0x01

    # --- Structure Definitions ---
    WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

    class WNDCLASS(ctypes.Structure):
        _fields_ = [
            ("style", wintypes.UINT),
            ("lpfnWndProc", WNDPROC),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HINSTANCE),
            ("hIcon", wintypes.HICON),
            ("hCursor", wintypes.HICON),
            ("hbrBackground", wintypes.HBRUSH),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR)
        ]

    class RAWINPUTDEVICE(ctypes.Structure):
        _fields_ = [
            ("usUsagePage", wintypes.USHORT),
            ("usUsage", wintypes.USHORT),
            ("dwFlags", wintypes.DWORD),
            ("hwndTarget", wintypes.HWND),
        ]

    class RAWINPUTDEVICELIST(ctypes.Structure):
        _fields_ = [
            ("hDevice", wintypes.HANDLE),
            ("dwType", wintypes.DWORD),
        ]

    class RAWINPUTHEADER(ctypes.Structure):
        _fields_ = [
            ("dwType", wintypes.DWORD),
            ("dwSize", wintypes.DWORD),
            ("hDevice", wintypes.HANDLE),
            ("wParam", wintypes.WPARAM),
        ]

    class RAWHID(ctypes.Structure):
        _fields_ = [
            ("dwSizeHid", wintypes.DWORD),
            ("dwCount", wintypes.DWORD),
            ("bRawData", wintypes.BYTE * 1), # Variable size
        ]

    class RAWKEYBOARD(ctypes.Structure):
        _fields_ = [
            ("MakeCode", wintypes.USHORT),
            ("Flags", wintypes.USHORT),
            ("Reserved", wintypes.USHORT),
            ("VKey", wintypes.USHORT),
            ("Message", wintypes.UINT),
            ("ExtraInformation", wintypes.ULONG),
        ]

    class RAWMOUSE(ctypes.Structure):
        _fields_ = [
            ("usFlags", wintypes.USHORT),
            ("ulButtons", wintypes.ULONG),
            ("ulRawButtons", wintypes.ULONG),
            ("lLastX", wintypes.LONG),
            ("lLastY", wintypes.LONG),
            ("ulExtraInformation", wintypes.ULONG),
        ]

    class RAWINPUT_HID(ctypes.Structure):
        _fields_ = [
            ("header", RAWINPUTHEADER),
            ("hid", RAWHID),
        ]

    class RAWINPUT_KBD(ctypes.Structure):
        _fields_ = [
            ("header", RAWINPUTHEADER),
            ("data", RAWKEYBOARD),
        ]

    def enumerate_devices():
        """Returns a list of connected Input Device names."""
        ui_list = []

        # 1. Get Device Count
        count = ctypes.c_uint(0)
        if user32.GetRawInputDeviceList(None, ctypes.byref(count), ctypes.sizeof(RAWINPUTDEVICELIST)) != 0:
            return ["Error: Failed to get device count."]

        if count.value == 0:
            return ["No devices found."]

        # 2. Get Device List
        devices = (RAWINPUTDEVICELIST * count.value)()
        if user32.GetRawInputDeviceList(devices, ctypes.byref(count), ctypes.sizeof(RAWINPUTDEVICELIST)) == -1:
             return ["Error: Failed to get device list."]

        # 3. Iterate and Get Names
        for i in range(count.value):
            hDevice = devices[i].hDevice
            dwType = devices[i].dwType # 0=MOUSE, 1=KBD, 2=HID

            # Get Name Length
            name_len = ctypes.c_uint(0)
            user32.GetRawInputDeviceInfoW(hDevice, RIDI_DEVICENAME, None, ctypes.byref(name_len))

            if name_len.value > 0:
                name_buffer = ctypes.create_unicode_buffer(name_len.value)
                user32.GetRawInputDeviceInfoW(hDevice, RIDI_DEVICENAME, name_buffer, ctypes.byref(name_len))
                name = name_buffer.value

                type_str = "UNKNOWN"
                if dwType == RIM_TYPEMOUSE: type_str = "MOUSE"
                elif dwType == RIM_TYPEKEYBOARD: type_str = "KEYBOARD"
                elif dwType == RIM_TYPEHID: type_str = "HID"

                # Filter out generic system devices if too noisy? No, user needs to see everything.
                ui_list.append(f"[{type_str}] {name}")

        return ui_list

    class RawInputMonitor:
        def __init__(self, callback):
            self.callback = callback
            self.thread = None
            self.hwnd = None
            self.running = False

        def start(self):
            if self.running: return
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()

        def stop(self):
            self.running = False
            if self.hwnd:
                user32.PostMessageW(self.hwnd, 0x0012, 0, 0) # WM_QUIT

        def _run_loop(self):
            # 1. Create Message-Only Window
            wc = WNDCLASS()
            wc.lpfnWndProc = WNDPROC(self._wnd_proc)
            wc.lpszClassName = "RawInputMonitorClass"
            wc.hInstance = kernel32.GetModuleHandleW(None)

            atom = user32.RegisterClassW(ctypes.byref(wc))
            if not atom:
                self.callback(f"[System] Failed to register window class: {kernel32.GetLastError()}")
                return

            self.hwnd = user32.CreateWindowExW(0, wc.lpszClassName, "HiddenRawInput", 0, 0, 0, 0, 0, 0, 0, 0, 0)
            if not self.hwnd:
                self.callback(f"[System] Failed to create hidden window: {kernel32.GetLastError()}")
                return

            # 2. Register Raw Input Devices
            # We want Generic Keyboard (1,6) and Consumer Control (12,1)
            devices = (RAWINPUTDEVICE * 2)(
                RAWINPUTDEVICE(HID_USAGE_PAGE_GENERIC, HID_USAGE_GENERIC_KEYBOARD, RIDEV_INPUTSINK, self.hwnd),
                RAWINPUTDEVICE(HID_USAGE_PAGE_CONSUMER, HID_USAGE_CONSUMER_CONTROL, RIDEV_INPUTSINK, self.hwnd)
            )

            if not user32.RegisterRawInputDevices(devices, 2, ctypes.sizeof(RAWINPUTDEVICE)):
                self.callback(f"[System] Failed to register Raw Input: {kernel32.GetLastError()}")

            self.callback("[System] Raw Input Monitor Started (Page 0x01 & 0x0C).")

            # 3. Message Loop
            msg = wintypes.MSG()
            while self.running and user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

            user32.DestroyWindow(self.hwnd)
            user32.UnregisterClassW(wc.lpszClassName, wc.hInstance)
            self.callback("[System] Raw Input Monitor Stopped.")

        def _wnd_proc(self, hwnd, msg, wparam, lparam):
            if msg == WM_INPUT:
                self._handle_raw_input(lparam)
                return user32.DefWindowProcW(hwnd, msg, wparam, lparam)
            elif msg == 0x0012: # WM_QUIT
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        def _handle_raw_input(self, hrawinput):
            # Get Header first to determine size
            header = RAWINPUTHEADER()
            size = ctypes.c_uint(ctypes.sizeof(header))

            dwSize = ctypes.c_uint(0)
            if user32.GetRawInputData(hrawinput, RID_INPUT, None, ctypes.byref(dwSize), ctypes.sizeof(RAWINPUTHEADER)) != 0:
                return

            # Allocate buffer
            buffer = ctypes.create_string_buffer(dwSize.value)
            if user32.GetRawInputData(hrawinput, RID_INPUT, buffer, ctypes.byref(dwSize), ctypes.sizeof(RAWINPUTHEADER)) != dwSize.value:
                return

            # Cast to generic raw input struct (header matches)
            raw = ctypes.cast(buffer, ctypes.POINTER(RAWINPUT_KBD)).contents

            msg = ""
            if raw.header.dwType == RIM_TYPEKEYBOARD:
                kbd = raw.data
                msg = f"[Raw Keyboard] MakeCode: {kbd.MakeCode}, VKey: {kbd.VKey}, Message: {kbd.Message}"

            elif raw.header.dwType == RIM_TYPEHID:
                raw_hid = ctypes.cast(buffer, ctypes.POINTER(RAWINPUT_HID)).contents
                count = raw_hid.hid.dwCount
                size_hid = raw_hid.hid.dwSizeHid
                total_bytes = count * size_hid

                # Get pointer to byte array
                base_addr = ctypes.addressof(raw_hid.hid) + ctypes.sizeof(ctypes.c_ulong) * 2

                data_bytes = (ctypes.c_byte * total_bytes).from_address(base_addr)
                hex_str = " ".join([f"{b:02X}" for b in data_bytes])

                msg = f"[Raw HID/Consumer] Count: {count}, Size: {size_hid}, Data: {hex_str}"

            if msg:
                self.callback(f"{msg}\n")
