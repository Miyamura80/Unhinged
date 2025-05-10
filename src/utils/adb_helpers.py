import subprocess
import shlex

# ADB tap primitive

def tap(x, y):
    subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)], check=True)

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