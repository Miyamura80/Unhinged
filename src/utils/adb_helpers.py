import subprocess
import shlex
import pathlib
import time
import random

# ADB tap primitive

def tap(x, y):
    subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)], check=True)

# ADB type text primitive (human-like typing)

def type_text(txt):
    for char in txt:
        # Use adb to type each character
        quoted_char = shlex.quote(char).replace(' ', '%s')
        subprocess.run(["adb", "shell", "input", "text", quoted_char], check=True)
        # Sleep a random time between 0.05 and 0.25 seconds
        time.sleep(random.uniform(0.05, 0.25))
    # Press BACK to close the keyboard
    subprocess.run(["adb", "shell", "input", "keyevent", "4"], check=True)

# XML bounds parsing

def parse_bounds(bounds_str):
    """Parses bounds string '[x1,y1][x2,y2]' into (x1, y1, x2, y2)."""
    import re
    match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
    if match:
        return tuple(map(int, match.groups()))
    return None

def get_element_center(bounds):
    """Calculates the center (x, y) of a bounds tuple."""
    if bounds:
        x1, y1, x2, y2 = bounds
        return (x1 + x2) // 2, (y1 + y2) // 2
    return None

def get_ui_dump(local_path="window_dump.xml"):
    """Dumps UI hierarchy from device and pulls it locally."""
    time.sleep(0.5)
    remote_path = "/sdcard/window_dump.xml"
    subprocess.run(["adb", "shell", "uiautomator", "dump", "--compressed", remote_path], check=True)
    subprocess.run(["adb", "pull", remote_path, local_path], check=True)
    print(f"UI hierarchy saved to: {local_path}") 