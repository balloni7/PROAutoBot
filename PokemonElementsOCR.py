import pytesseract
import cv2
import numpy as np
import pyautogui
import re
from difflib import get_close_matches

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class PokemonElementsOCR:
    def __init__(self):
        # Configure these coordinates to match the name position in your game
        self.name_region = (0, 0, 0, 0)  # (left, top, width, height)

        # Load known Pokémon names
        self.known_pokemon = self._load_pokemon_names()

        # OCR configuration
        self.ocr_config = r'--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz- '

    def _load_pokemon_names(self):
        """Load a list of all possible Pokémon names"""
        try:
            with open('pokemon_names.txt', 'r') as f:
                return [name.strip().lower() for name in f.readlines()]
        except FileNotFoundError:
            print("Warning: pokemon_names.txt not found. Using fallback list.")

    def _preprocess_image(self, image):
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

    def detect_pokemon_name(self):
        """Capture screen and detect Pokémon name"""
        try:
            # Capture name area
            screenshot = pyautogui.screenshot(region=self.name_region)
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

    def calibrate_name_position(self):
        """Helper to find the name position"""
        print("Move your mouse to the top-left of the Pokémon name and press Enter")
        input()
        x1, y1 = pyautogui.position()

        print("Move to the bottom-right and press Enter")
        input()
        x2, y2 = pyautogui.position()

        self.name_region = (x1, y1, x2 - x1, y2 - y1)
        print(f"New detection region set: {self.name_region}")


if __name__ == '__main__':
    poke = PokemonElementsOCR()
