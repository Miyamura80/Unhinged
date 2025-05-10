import dspy
from typing import Any
import lxml.etree as ET
from src.utils.adb_helpers import tap, parse_bounds, get_element_center, type_text, get_ui_dump

import time

class SubjectPair:
    subject_id: str
    subject_content: str | dspy.Image
    heart_button_bounds: Any

    def __init__(self, subject_id, subject_content, heart_button_bounds):
        self.subject_id = subject_id
        self.subject_content = subject_content
        self.heart_button_bounds = heart_button_bounds

class HingeAPI:
    def __init__(self, xml_path="window_dump.xml"):
        self.xml_path = xml_path
        self.subject_pairs = self._parse_subjects_and_hearts()

    def _parse_subjects_and_hearts(self):
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        subject_pairs = []

        # Collect all photo nodes and all like buttons
        photo_nodes = []
        like_buttons = []

        for node in root.iter("node"):
            content_desc = node.get("content-desc", "")
            class_name = node.get("class", "")
            bounds_str = node.get("bounds", "")

            if "photo" in content_desc:
                photo_nodes.append((node, bounds_str, content_desc))
            if class_name == "android.widget.Button" and content_desc == "Like":
                like_buttons.append((node, bounds_str))

        # For each photo, find the closest like button (by vertical distance)
        for photo_node, photo_bounds_str, photo_desc in photo_nodes:
            photo_bounds = parse_bounds(photo_bounds_str)
            if not photo_bounds:
                continue
            photo_center = get_element_center(photo_bounds)
            min_dist = float("inf")
            closest_like = None
            for like_node, like_bounds_str in like_buttons:
                like_bounds = parse_bounds(like_bounds_str)
                if not like_bounds:
                    continue
                like_center = get_element_center(like_bounds)
                # Use vertical distance as heuristic
                dist = abs(photo_center[1] - like_center[1])
                if dist < min_dist:
                    min_dist = dist
                    closest_like = like_bounds
            if closest_like:
                subject_id = f"{photo_desc}:{photo_bounds_str}"
                subject_pairs.append(SubjectPair(subject_id, photo_desc, closest_like))

        return subject_pairs

    def submit_reply(self, subject_id: str, response_text: str):
        for pair in self.subject_pairs:
            if pair.subject_id == subject_id:
                bounds = pair.heart_button_bounds
                x1, y1, x2, y2 = bounds
                # Tap the heart button (as before)
                center = get_element_center(bounds)
                tap(*center)
                time.sleep(1.5)
                # Get new UI dump after heart tap
                get_ui_dump("window_dump_after_heart.xml")
                tree = ET.parse("window_dump_after_heart.xml")
                root = tree.getroot()
                # Find the input field (EditText)
                input_field = None
                for node in root.iter("node"):
                    class_name = node.get("class", "")
                    if "EditText" in class_name:
                        input_field = node
                        break
                if input_field is not None:
                    input_bounds = parse_bounds(input_field.get("bounds"))
                    if input_bounds:
                        input_center = get_element_center(input_bounds)
                        print(f"Tapping input field at: {input_center}")
                        tap(*input_center)
                        time.sleep(0.5)
                        print(f"Typing response: {response_text}")
                        type_text(response_text)
                        return True
                    else:
                        print("Could not parse input field bounds.")
                else:
                    print("Input field not found after heart tap.")
                return False
        return False

    
    
    
