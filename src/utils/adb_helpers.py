import subprocess
import shlex
import pathlib
import time
import random
import os

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

def get_ui_dump(dump_number=0):
    """Dumps UI hierarchy from device and pulls it locally to a numbered file in window_dump folder."""
    # Create window_dump directory if it doesn't exist
    dump_dir = "window_dump"
    os.makedirs(dump_dir, exist_ok=True)
    
    time.sleep(0.5)
    remote_path = "/sdcard/window_dump.xml"
    local_path = os.path.join(dump_dir, f"window_dump_{dump_number}.xml")
    
    subprocess.run(["adb", "shell", "uiautomator", "dump", "--compressed", remote_path], check=True)
    subprocess.run(["adb", "pull", remote_path, local_path], check=True)
    print(f"UI hierarchy saved to: {local_path}")
    return local_path

def screenshot(output_path: str) -> bool:
    """Take a screenshot and save it to the specified path."""
    if not output_path:
        print("Error: No output path provided for screenshot")
        return False
        
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Take screenshot on device
        remote_path = "/sdcard/temp_screenshot.png"
        subprocess.run(["adb", "shell", "screencap", "-p", remote_path], check=True, capture_output=True)
        
        # Pull screenshot to local machine
        subprocess.run(["adb", "pull", remote_path, output_path], check=True, capture_output=True)
        
        # Clean up remote file
        subprocess.run(["adb", "shell", "rm", remote_path], check=True, capture_output=True)
        
        # Verify the file exists and is not empty
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        else:
            print(f"Error: Screenshot file not created or empty at {output_path}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error running adb command: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error taking screenshot: {e}")
        return False 