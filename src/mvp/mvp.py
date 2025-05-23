#!/usr/bin/env python3
import subprocess
import time
import shlex
import pathlib
import xml.etree.ElementTree as ET
import re
import os

# Ensure adb command exists
try:
    subprocess.run(["adb", "--version"], check=True, capture_output=True)
except (FileNotFoundError, subprocess.CalledProcessError) as e:
    print(f"Error: 'adb' command not found or not working. Please ensure it's installed and in your PATH. {e}")
    exit(1)


def adb(*cmd, **kw):
    """thin wrapper – raises if adb exits non-zero"""
    try:
        # Default to capturing output to avoid printing unnecessary adb info, unless stdout/stderr specified
        kw.setdefault("capture_output", True)
        kw.setdefault("text", True) # Decode output as text
        # print(f"Running: adb {' '.join(map(str, cmd))}") # Optional: Debug print
        result = subprocess.run(["adb", *map(str, cmd)], check=True, **kw)
        # print(f"Result: {result.stdout or result.stderr}") # Optional: Debug print
        return result
    except FileNotFoundError:
        print("Error: 'adb' command not found. Please ensure it's installed and in your PATH.")
        raise
    except subprocess.CalledProcessError as e:
        print(f"Error running adb command: {' '.join(map(str, cmd))}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
        raise # Re-raise the exception after printing details

# ---------- primitives ---------- #
def swipe(x1, y1, x2, y2, ms=300):
    adb("shell", "input", "swipe", x1, y1, x2, y2, ms)

def tap(x, y):
    adb("shell", "input", "tap", x, y)

def type_text(txt):
    # Ensure text is properly quoted for the shell, replace space with %s for adb input text
    quoted_text = shlex.quote(txt).replace(' ', '%s')
    adb("shell", "input", "text", quoted_text)

def screenshot(path="screen.png"):
    # Ensure the directory exists
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    # Use adb exec-out for binary data
    adb("exec-out", "screencap", "-p", stdout=pathlib.Path(path).open("wb"), capture_output=False, text=False)
    print(f"Screenshot saved to: {pathlib.Path(path).resolve()}")

def get_ui_dump(local_path="window_dump.xml"):
    """Dumps UI hierarchy from device and pulls it locally."""
    # Add a small delay before dumping UI, just in case.
    time.sleep(0.5)
    remote_path = "/sdcard/window_dump.xml"
    # Dump UI Hierarchy
    adb("shell", "uiautomator", "dump", "--compressed", remote_path)
    # Pull the file
    adb("pull", remote_path, local_path)
    # Optional: Remove the file from device after pulling
    # adb("shell", "rm", remote_path)
    print(f"UI hierarchy saved to: {local_path}")

# ---------- XML Parsing Helpers ---------- #
def parse_bounds(bounds_str):
    """Parses bounds string '[x1,y1][x2,y2]' into (x1, y1, x2, y2)."""
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

def find_element(root, attribute, value_pattern, clickable_only=False):
    """Finds the first element matching an attribute pattern."""
    for element in root.iter('node'):
        attr_value = element.get(attribute)
        if attr_value and re.search(value_pattern, attr_value):
            if clickable_only and element.get('clickable') != 'true':
                continue
            return element
    return None

def find_photo_element(root):
    """Attempts to find the main photo element based on content-desc or size."""
    print("Searching for photo element...")
    # Try finding based on content-desc containing 'photo' (less strict)
    photo_element = find_element(root, 'content-desc', r'photo', clickable_only=False) # Changed regex, removed clickable_only=True just in case
    if photo_element is not None: # Explicit check
        print(f"Found element by content-desc 'photo': {photo_element.get('content-desc')}, bounds: {photo_element.get('bounds')}")
        return photo_element
    else:
        print("Did not find element with 'photo' in content-desc.")

    # Fallback: Look for large view elements (potential photo container)
    print("Falling back to searching for large View elements...")
    screen_width = 1080 # Assuming 1080p screen, adjust if necessary
    min_photo_width = screen_width * 0.7 # Example threshold

    potential_candidates = []
    for element in root.iter('node'):
        bounds_str = element.get('bounds')
        class_name = element.get('class')
        if not bounds_str or not class_name:
            continue

        # Print some info about potential views
        # if class_name == 'android.view.View':
        #     print(f"  Checking View element: bounds={bounds_str}")

        bounds = parse_bounds(bounds_str)
        if not bounds:
            continue

        x1, y1, x2, y2 = bounds
        width = x2 - x1
        height = y2 - y1

        # Check if it's a large element, likely a photo container
        if width > min_photo_width and height > width * 0.5 and class_name == 'android.view.View':
             print(f"  Found potential large View element: bounds={bounds_str}, width={width}, height={height}")
             potential_candidates.append(element)
             # Maybe return the first one found? Or the largest? For now, let's just take the first.
             # This heuristic might need refinement. Consider position, clickability etc.
             print("Returning first large View element as potential photo.")
             return element

    print("Did not find any suitable large View elements as a fallback.")
    return None # No suitable element found

def get_tap_coords_for_next_photo(bounds):
    """Calculates tap coordinates on the right side to advance photos."""
    if bounds:
        x1, y1, x2, y2 = bounds
        # Tap near the right edge, vertically centered
        tap_x = x1 + int((x2 - x1) * 0.9) # 90% across the width
        tap_y = (y1 + y2) // 2
        return tap_x, tap_y
    return None

def find_parent(root, element):
    """Finds the parent element of a given element in the tree."""
    for parent in root.iter():
        for child in parent:
            if child is element:
                return parent
    return None

def find_all_elements(root, attribute, value_pattern, clickable_only=False):
    """Finds all elements matching an attribute pattern."""
    found_elements = []
    for element in root.iter('node'):
        attr_value = element.get(attribute)
        if attr_value and re.search(value_pattern, attr_value):
            if clickable_only and element.get('clickable') != 'true':
                continue
            found_elements.append(element)
    return found_elements

def find_all_photo_elements(root):
    """Attempts to find all photo elements based on content-desc."""
    print("Searching for all photo elements...")
    # Find elements based on content-desc containing 'photo'
    photo_elements = find_all_elements(root, 'content-desc', r'photo', clickable_only=False)
    if photo_elements:
        print(f"Found {len(photo_elements)} element(s) with 'photo' in content-desc.")
        # Optionally, print details of found elements for debugging
        # for elem in photo_elements:
        #     print(f"  - content-desc: {elem.get('content-desc')}, bounds: {elem.get('bounds')}")
    else:
        print("Did not find any elements with 'photo' in content-desc.")
    return photo_elements

# ---------- Photo Scraping Workflow ---------- #
def capture_profile_photos(output_dir="profile_photos"):
    """Cycles through photos on the current profile by scrolling vertically and captures screenshots."""
    os.makedirs(output_dir, exist_ok=True)
    screenshot_index = 1
    processed_photo_bounds = set() # Use bounds string as ID
    no_new_photos_streak = 0
    max_scrolls_without_new = 3 # Stop after 3 scrolls reveal nothing new

    print("Starting photo capture process with vertical scrolling...")

    while no_new_photos_streak < max_scrolls_without_new:
        print(f"\nProcessing screen state (scroll attempt {no_new_photos_streak + 1})...")
        # 1. Get current UI state
        dump_file = "window_dump.xml"
        try:
            get_ui_dump(dump_file)
            tree = ET.parse(dump_file)
            root = tree.getroot()
        except Exception as e:
            print(f"An unexpected error occurred during UI dump/parse: {e}. Stopping.")
            break

        # 2. Find all potential photo elements visible
        visible_photos = find_all_photo_elements(root)
        if not visible_photos:
            print("No photo elements found on this screen.")
            # If we never found any photos at all, maybe break early?
            if not processed_photo_bounds:
                 print("No photos found initially. Ensure you are on a profile screen. Stopping.")
                 break
        
        new_photos_found_this_iteration = False
        # 3. Process and screenshot new photos
        for photo_element in visible_photos:
            bounds_str = photo_element.get("bounds")
            if not bounds_str:
                print(f"Skipping element with no bounds: {photo_element.get('content-desc')}")
                continue

            if bounds_str not in processed_photo_bounds:
                print(f"Found new photo: bounds={bounds_str}, content-desc={photo_element.get('content-desc')}")
                processed_photo_bounds.add(bounds_str)
                new_photos_found_this_iteration = True

                screenshot_path = os.path.join(output_dir, f"photo_{screenshot_index}.png")
                
                # Option 1: Screenshot whole screen (simpler)
                screenshot(screenshot_path)
                print(f"  Screenshot {screenshot_index} saved (full screen)." )
                
                # Option 2: Crop screenshot to bounds (more complex, needs image lib like Pillow)
                # bounds = parse_bounds(bounds_str)
                # if bounds: 
                #    # full_screenshot_path = "temp_fullscreen.png"
                #    # screenshot(full_screenshot_path)
                #    # crop_image(full_screenshot_path, screenshot_path, bounds) # Requires Pillow
                #    # print(f"  Screenshot {screenshot_index} saved (cropped to {bounds}).")
                #    # os.remove(full_screenshot_path)
                #    # For now, stick to full screen:
                #    screenshot(screenshot_path)
                #    print(f"  Screenshot {screenshot_index} saved (full screen - cropping not implemented).")
                # else:
                #    print("  Could not parse bounds for cropping.")

                screenshot_index += 1
            # else:
                # print(f"Skipping already processed photo: bounds={bounds_str}")

        # 4. Check if we should continue scrolling
        if new_photos_found_this_iteration:
            no_new_photos_streak = 0 # Reset streak
        else:
            print("No new photos found on this screen.")
            no_new_photos_streak += 1
            if no_new_photos_streak >= max_scrolls_without_new:
                print(f"No new photos found for {max_scrolls_without_new} consecutive scrolls. Stopping.")
                break

        # 5. Perform vertical scroll down
        # Get screen dimensions (assuming 1080x2400 for now, ideally get dynamically)
        screen_width = 1080
        screen_height = 2400
        scroll_x = screen_width // 2
        scroll_y_start = int(screen_height * 0.8) # Start scroll from 80% down
        scroll_y_end = int(screen_height * 0.2)   # Scroll up to 20%
        scroll_duration_ms = 500 # Slightly longer for smoother scroll

        print(f"Scrolling down: Swiping from ({scroll_x}, {scroll_y_start}) to ({scroll_x}, {scroll_y_end})")
        swipe(scroll_x, scroll_y_start, scroll_x, scroll_y_end, scroll_duration_ms)

        # 6. Wait for UI to settle after scroll
        time.sleep(2.5)

    total_photos = screenshot_index - 1
    print(f"\nPhoto capture finished. {total_photos} photos saved in '{output_dir}'.")


# ---------- Main Execution ---------- #
if __name__ == "__main__":
    # Example usage:
    # swipe(540, 1600, 540, 400) # scroll up on a 1080×1920 display
    # time.sleep(0.5)
    # tap(540, 960) # tap centre of screen
    # type_text("hello world")
    # screenshot("shot.png")
    # print("done →", pathlib.Path("shot.png").resolve())

    # Run the photo capturing workflow
    capture_profile_photos()