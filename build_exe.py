import PyInstaller.__main__
import customtkinter
import os
import platform

# Determine separator for add-data
# On Windows it is ';', on Linux/Unix it is ':'
SEP = ';' if platform.system() == "Windows" else ':'

# Get customtkinter path to include its assets
ctk_path = os.path.dirname(customtkinter.__file__)

print(f"Building executable...")
print(f"Including customtkinter from: {ctk_path}")

PyInstaller.__main__.run([
    'run.py',
    '--name=BluetoothMapper',
    '--onefile',
    '--windowed',
    '--clean',
    f'--add-data={ctk_path}{SEP}customtkinter',
    '--log-level=INFO'
])
