# Bluetooth Earbuds Controller

A Windows application to map/remap Bluetooth button inputs (like Play/Pause) to custom system actions.

## Features

- **Gesture Recognition**: Single, Double, and Triple tap detection on the Play/Pause button.
- **Custom Remapping**: Map gestures and buttons to actions like Scroll, Volume, Track Navigation, and Lock Screen.
- **Auto-Start**: Option to start automatically with Windows.

## Installation

1.  Ensure you have Python 3.8+ installed.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

To run from source:

```bash
python run.py
```

**Note**: You may need to run as Administrator for the application to successfully intercept global media keys.

## Building the Executable

To build a standalone `.exe` file:

```bash
python build_exe.py
```

The executable will be located in the `dist/` folder.

## Troubleshooting

-   **Input Interception Failed**: Run the application/terminal as Administrator.
-   **Double Actions**: If you hear the music pause AND the custom action happens, set "Single Tap" to "None" in the settings.
