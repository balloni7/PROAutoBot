import pytesseract
import cv2
import numpy as np
import pyautogui
import re
from difflib import get_close_matches

import sys
import os
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class PokemonElementsOCR:
    def __init__(self, names_file,
                 shiny_template_path=None,
                 battle_template_path=None,
                 gray_icon_path=None,
                 red_icon_path=None):

        self.known_pokemon = self._load_pokemon_names(names_file) if names_file else None
        self.shiny_template = self._load_template(shiny_template_path) if shiny_template_path else None
        self.battle_template = self._load_template(battle_template_path) if battle_template_path else None
        self.gray_action_template = self._load_template(gray_icon_path, 1) if gray_icon_path else None
        self.red_action_template = self._load_template(red_icon_path, 1) if red_icon_path else None

        self.ocr_config = r'--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz- '


    @classmethod
    def from_names_only(cls, config_handler):
        """Factory method for names-only initialization"""
        return cls(names_file=config_handler.get("Files", "names_file"))

    @classmethod
    def from_config_handler(cls, config_handler):
        """Factory method for full initialization from config"""
        return cls(
            names_file=config_handler.get("Files", "names_file"),
            shiny_template_path=config_handler.get("Files", "shiny_template"),
            battle_template_path=config_handler.get("Files", "battle_template"),
            gray_icon_path=config_handler.get("Files", "gray_action_icon"),
            red_icon_path=config_handler.get("Files", "red_action_icon")
        )

    @staticmethod
    def _load_pokemon_names(names_file):
        """Load a list of all possible Pokémon names"""
        try:
            with open(names_file, 'r') as f:
                return [name.strip().lower() for name in f.readlines()]
        except FileNotFoundError:
            print("Warning: pokemon_names.txt not found. Using fallback list.")

    @staticmethod
    def _preprocess_image(image):
        """Enhance image for better OCR results"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Apply dilation to make text thicker
        kernel = np.ones((2, 2), np.uint8)
        processed = cv2.dilate(thresh, kernel, iterations=1)

        return processed

    def _clean_name(self, text):
        """Clean and validate the OCR result"""
        # Remove non-alphabetic characters except hyphen
        cleaned = re.sub(r'[^a-zA-Z\- ]', '', text).strip()

        # Find closest match in known Pokémon names
        matches = get_close_matches(cleaned.lower(), self.known_pokemon, n=1, cutoff=0.6)
        return matches[0].title() if matches else None

    def detect_pokemon_name(self, name_region):
        """Capture screen and detect Pokémon name"""
        try:
            # Capture name area
            screenshot = pyautogui.screenshot(region=name_region)
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # Preprocess image
            processed = self._preprocess_image(img)

            # Try OCR
            text = pytesseract.image_to_string(processed, config=self.ocr_config)

            # Clean and validate
            if text.strip():
                return self._clean_name(text)
            return None

        except Exception as e:
            print(f"Detection error: {e}")
            return None

    @staticmethod
    def _load_template(image_path, color_mode = 0):
        """ Load the templates from image """
        try:
            template = cv2.imread(image_path, color_mode)
            if template is None:
                raise FileNotFoundError
            return template
        except Exception as e:
            print(f"Error loading template image: {e}")
            sys.exit(1)

    def is_shiny_present(self):
        """Check if the shiny message is on screen"""
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

        # Template matching
        res = cv2.matchTemplate(screenshot, self.shiny_template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        loc = np.where(res >= threshold)

        return len(loc[0]) > 0

    def is_in_battle(self, threshold=0.8):
        """Check if player is in battle"""
        try:
            # Load the battle template image
            if self.battle_template is None:
                raise FileNotFoundError(f"Battle template image not found at {os.path.abspath(os.path.dirname(__file__))}")

            # Take screenshot of the game window
            screenshot = pyautogui.screenshot()
            screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

            # Perform template matching
            res = cv2.matchTemplate(screenshot_gray, self.battle_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)

            # Return True if the match confidence exceeds the threshold
            return max_val >= threshold

        except Exception as e:
            print(f"Error in battle detection: {e}")
            return False

    def is_action_ready(self):
        """
        Check which template matches better: red (busy) or gray (ready)
        Returns: True if ready (gray), False if busy (red)
        """
        # Capture current screen
        screenshot = pyautogui.screenshot()
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Match against both templates
        red_match = cv2.matchTemplate(img, self.red_action_template, cv2.TM_CCOEFF_NORMED)
        gray_match = cv2.matchTemplate(img, self.gray_action_template, cv2.TM_CCOEFF_NORMED)

        # Get best match values
        _, red_val, _, _ = cv2.minMaxLoc(red_match)
        _, gray_val, _, _ = cv2.minMaxLoc(gray_match)

        print(f"Red: {red_val:.3f}, Gray: {gray_val:.3f}")  # Debug info

        # Return state based on which matches better
        return gray_val > red_val