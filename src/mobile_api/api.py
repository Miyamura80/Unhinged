import dspy
from typing import Any, Optional
import lxml.etree as ET
from src.utils.adb_helpers import tap, parse_bounds, get_element_center, type_text, get_ui_dump, screenshot
from PIL import Image
import os
import time
from datetime import datetime

class ProfileInfo:
    """Class to hold profile information that is unique to the current page."""
    name: str
    age: Optional[int]
    location: Optional[str]
    university: Optional[str]
    hometown: Optional[str]
    relationship_type: Optional[str]
    gender: Optional[str]
    height: Optional[str]
    job: Optional[str]
    religion: Optional[str]
    politics: Optional[str]
    prompts: list[str]  # Store prompts and their responses

    def __init__(self):
        self.name = ""
        self.age = None
        self.location = None
        self.university = None
        self.hometown = None
        self.relationship_type = None
        self.gender = None
        self.height = None
        self.job = None
        self.religion = None
        self.politics = None
        self.prompts = []

    def __str__(self):
        info_parts = []
        if self.name:
            info_parts.append(f"Name: {self.name}")
        if self.age:
            info_parts.append(f"Age: {self.age}")
        if self.height:
            info_parts.append(f"Height: {self.height}")
        if self.location:
            info_parts.append(f"Location: {self.location}")
        if self.job:
            info_parts.append(f"Job: {self.job}")
        if self.university:
            info_parts.append(f"University: {self.university}")
        if self.hometown:
            info_parts.append(f"Hometown: {self.hometown}")
        if self.relationship_type:
            info_parts.append(f"Looking for: {self.relationship_type}")
        if self.gender:
            info_parts.append(f"Gender: {self.gender}")
        if self.religion:
            info_parts.append(f"Religion: {self.religion}")
        if self.politics:
            info_parts.append(f"Politics: {self.politics}")
        if self.prompts:
            info_parts.append("\nPrompts:")
            for prompt in self.prompts:
                info_parts.append(f"- {prompt}")
        return "\n".join(info_parts) if info_parts else "No profile information available"

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
        self.profile_info = ProfileInfo()  # Initialize empty profile
        self._update_profile_info()  # First update
        self.subject_pairs = self._parse_subjects_and_hearts()

    def _update_profile_info(self) -> None:
        """Update profile information from the UI hierarchy, preserving existing values."""
        tree = ET.parse(self.xml_path)
        root = tree.getroot()

        # First pass: collect all text nodes and their relationships
        text_nodes = []
        for node in root.iter("node"):
            text = node.get("text", "").strip()
            content_desc = node.get("content-desc", "").strip()
            bounds = node.get("bounds", "")
            
            if text or content_desc:
                text_nodes.append((node, text, content_desc, bounds))

        # Second pass: analyze text nodes for profile information
        for node, text, content_desc, bounds in text_nodes:
            # Extract name (usually in a TextView near the top)
            if text and not text.lower() in ["more", "like", "skip"] and not text.isdigit():
                # Check if this is likely a name (not a prompt or response)
                parent = node.getparent()
                if parent is not None:
                    parent_class = parent.get("class", "")
                    if "TextView" in parent_class and not any(prompt in text.lower() for prompt in ["looking for", "relationship"]):
                        self.profile_info.name = text

            # Extract gender (usually in a TextView)
            if text.lower() in ["he", "she", "they", "woman", "man"]:
                self.profile_info.gender = text.lower()

            # Extract prompts and responses by looking at the UI structure
            # First, find all TextViews that might be prompt starters
            if node.get("class") == "android.widget.TextView" and node.get("text"):
                text = node.get("text", "").strip()
                if text and text.lower() not in ["more", "like", "skip"]:
                    # Check if this is a prompt starter
                    first_text = text.lower()
                    if any(phrase in first_text for phrase in [
                        "dating me is like",
                        "i won't shut up about",
                        "i go crazy for",
                        "my simple pleasures",
                        "my most controversial opinion",
                        "i bet you can't",
                        "we'll get along if",
                        "the way to win me over is",
                        "unusual skills"
                    ]):
                        # Found a prompt starter, look for the response in siblings
                        parent = node.getparent()
                        if parent is not None:
                            # Look for the response TextView
                            for sibling in parent:
                                if sibling.get("class") == "android.widget.TextView" and sibling != node:
                                    response = sibling.get("text", "").strip()
                                    if response:
                                        prompt = f"{text} | {response}"
                                        if prompt not in self.profile_info.prompts:
                                            self.profile_info.prompts.append(prompt)
                                        break

        # Additional pass to find information in specific UI elements
        for node in root.iter("node"):
            if node.get("class") == "android.view.View":
                # Look for the profile info container
                for child in node:
                    if child.get("class") == "android.view.View":
                        # Get the label (content-desc) from the first child
                        for label_node in child:
                            if label_node.get("class") == "android.view.View":
                                label = label_node.get("content-desc", "").lower()
                                # Get the value from the TextView that follows
                                for value_node in child:
                                    if value_node.get("class") == "android.widget.TextView":
                                        value = value_node.get("text", "").strip()
                                        if value:  # Only process if we have a value
                                            if "age" in label and value.isdigit():
                                                self.profile_info.age = int(value)
                                            elif "height" in label:
                                                self.profile_info.height = value
                                            elif "location" in label:
                                                self.profile_info.location = value
                                            elif "job" in label:
                                                self.profile_info.job = value
                                            elif "college or university" in label:
                                                self.profile_info.university = value
                                            elif "home town" in label:
                                                self.profile_info.hometown = value
                                            elif "dating intentions" in label:
                                                self.profile_info.relationship_type = value
                                            elif "religion" in label:
                                                self.profile_info.religion = value
                                            elif "politics" in label:
                                                self.profile_info.politics = value

        # Debug print to see what we found
        print("\nDebug - Found profile info:")
        print(f"Age: {self.profile_info.age}")
        print(f"Height: {self.profile_info.height}")
        print(f"Location: {self.profile_info.location}")
        print(f"Job: {self.profile_info.job}")
        print(f"University: {self.profile_info.university}")

    def _extract_profile_info(self) -> ProfileInfo:
        """Extract profile information from the UI hierarchy."""
        self._update_profile_info()
        return self.profile_info

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

    def get_profile_info(self) -> ProfileInfo:
        """Returns the profile information for the current page."""
        return self.profile_info

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

    
    
    
