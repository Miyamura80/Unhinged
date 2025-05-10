import dspy
from typing import Any, Optional
import lxml.etree as ET
from src.utils.adb_helpers import tap, parse_bounds, get_element_center, type_text, get_ui_dump, screenshot
from PIL import Image
import os
import time
from datetime import datetime

class SubjectPair:
    subject_id: str
    subject_content: str | dspy.Image
    heart_button_bounds: Any
    bounds: tuple  # Store the bounds for screenshot purposes

    def __init__(self, subject_id, subject_content, heart_button_bounds, bounds):
        self.subject_id = subject_id
        self.subject_content = subject_content
        self.heart_button_bounds = heart_button_bounds
        self.bounds = bounds

    def __str__(self):
        if isinstance(self.subject_content, dspy.Image):
            return f"[Image] {self.subject_id}"
        return f"[Text] {self.subject_content}"

class HingeAPI:
    def __init__(self, xml_path="window_dump.xml"):
        self.xml_path = xml_path
        self.subject_pairs = self._parse_subjects_and_hearts()

    def _parse_subjects_and_hearts(self):
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        subject_pairs = []

        # First, find all view containers that might be cards
        card_containers = []
        for node in root.iter("node"):
            class_name = node.get("class", "")
            if (class_name == "android.view.View" and 
                "bounds" in node.attrib):
                card_containers.append(node)

        # For each card container, extract its content
        for card in card_containers:
            card_bounds = parse_bounds(card.get("bounds"))
            if not card_bounds:
                continue

            # Find all text nodes within this card
            card_texts = []
            for text_node in card.iter("node"):
                text = text_node.get("text", "").strip()
                if text:
                    card_texts.append(text)

            # Find photo nodes within this card
            photo_nodes = []
            for photo_node in card.iter("node"):
                content_desc = photo_node.get("content-desc", "").lower()
                if "photo" in content_desc or "image" in content_desc:
                    photo_bounds = parse_bounds(photo_node.get("bounds"))
                    if photo_bounds:
                        photo_nodes.append((photo_node, content_desc, photo_bounds))

            # Find the closest like button to this card
            card_center = get_element_center(card_bounds)
            min_dist = float("inf")
            closest_like = None

            for node in root.iter("node"):
                if (node.get("class") == "android.widget.Button" and 
                    node.get("content-desc") == "Like"):
                    like_bounds = parse_bounds(node.get("bounds"))
                    if like_bounds:
                        like_center = get_element_center(like_bounds)
                        dist = abs(card_center[1] - like_center[1])
                        if dist < min_dist:
                            min_dist = dist
                            closest_like = like_bounds

            # Create subject pairs for both text and photos
            if card_texts:
                text_content = " | ".join(card_texts)
                subject_id = f"text:{card_bounds}"
                subject_pairs.append(SubjectPair(subject_id, text_content, closest_like, card_bounds))

            for photo_node, photo_desc, photo_bounds in photo_nodes:
                subject_id = f"{photo_desc}:{photo_bounds}"
                subject_pairs.append(SubjectPair(subject_id, photo_desc, closest_like, photo_bounds))

        return subject_pairs

    def get_all_subjects(self):
        """Returns a list of all subjects with their content."""
        return [(str(pair), pair.subject_content, pair.bounds) for pair in self.subject_pairs]

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

    def capture_subject_photo(self, subject_pair: SubjectPair, output_dir: str = "photo_dump") -> Optional[str]:
        """Capture and save a photo of the subject."""
        if not subject_pair.bounds:
            print("No bounds available for photo capture")
            return None
            
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Take full screenshot
            temp_screenshot = os.path.join(output_dir, "temp_screenshot.png")
            if not screenshot(temp_screenshot):
                print("Failed to take screenshot")
                return None
                
            # Crop to subject bounds
            with Image.open(temp_screenshot) as img:
                x1, y1, x2, y2 = subject_pair.bounds
                cropped = img.crop((x1, y1, x2, y2))
                
                # Generate output filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"photo_{timestamp}.png"
                output_path = os.path.join(output_dir, output_filename)
                
                # Save cropped image
                cropped.save(output_path)
                
            # Clean up temp file
            if os.path.exists(temp_screenshot):
                os.remove(temp_screenshot)
                
            return output_path
            
        except Exception as e:
            print(f"Error capturing photo: {e}")
            return None

    
    
    
