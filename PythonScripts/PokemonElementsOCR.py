import pytesseract
import cv2
import numpy as np
import pyautogui
import re
from difflib import get_close_matches

import tkinter as tk
from PIL import Image, ImageTk
import ctypes

import time
from ConfigHandler import ConfigHandler

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class PokemonElementsOCR:
    def __init__(self, config_handler=ConfigHandler(), names_file="Resources/pokemon_names.txt"):
        self.configHandler = config_handler
        self.names_file = names_file
        self.calibrator = VisualCalibrator()
        # Load a list of all Pokémon names
        self.known_pokemon = self._load_pokemon_names()
        # OCR configuration
        self.ocr_config = r'--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz- '

    def _load_pokemon_names(self):
        """Load a list of all possible Pokémon names"""
        try:
            with open(self.names_file, 'r') as f:
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
        name_region = self.configHandler.settings["OCR"]["name_region"]
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

    def calibrate_name_position(self):
        """Interactive visual calibration"""
        region = self.calibrator.get_selection()
        if region:
            self.configHandler.configParser["OCR"]["name_region"] = str(region)
            print(f"\nCalibration successful! New detection Pokemon name region: {region}")
            return True

        print("\nCalibration cancelled.")
        return False


class VisualCalibrator:
    def __init__(self):
        self.root = None
        self.canvas = None
        self.start_x = None #Anchor point for rectangle drawing
        self.start_y = None #Anchor point for rectangle drawing
        self.rect = None # Reference to dynamically update rectangle position
        self.screenshot = None
        self.darkened_screenshot = None
        self.selection_made = False #Distinguishes between successful selection and cancellation
        self.final_coords = None
        self.console_window = ctypes.windll.kernel32.GetConsoleWindow() #Holds OS reference to console window

    def _create_overlay(self):
        """Create overlay window without transparency"""
        # Minimize console before showing overlay
        self._minimize_console()
        time.sleep(0.1)

        #Initial Setup
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='black')

        # Take screenshot and darken it
        self.screenshot = pyautogui.screenshot()
        self.darkened_screenshot = self._darken_image(self.screenshot)

        # Create canvas
        self.canvas = tk.Canvas(self.root, cursor="cross", highlightthickness=0, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Display darkened screenshot
        self.tk_image = ImageTk.PhotoImage(self.darkened_screenshot)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # Add instructions
        instructions = "Click and drag to select Pokémon name area"
        self.canvas.create_text(
            self.screenshot.width / 2, 30,
            text=instructions,
            fill="white",
            font=("Arial", 16),
            anchor=tk.CENTER
        )

    def _minimize_console(self):
        """Minimize the console window"""
        try:
            ctypes.windll.user32.ShowWindow(self.console_window, 6)  # 6 = SW_MINIMIZE
        except:
            pass

    def _restore_console(self):
        """Restore and focus the console window"""
        try:
            ctypes.windll.user32.ShowWindow(self.console_window, 9)  # 9 = SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(self.console_window)
        except:
            pass

    def _darken_image(self, image, factor=0.3):
        """Darken the screenshot for overlay effect"""
        arr = np.array(image)
        arr = (arr * factor).astype(np.uint8)
        return Image.fromarray(arr)

    def _on_press(self, event):
        """Handle mouse button press"""
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y,
            self.start_x, self.start_y,
            outline='red', width=2,
            fill='',  # Start with no fill
            stipple='gray12'  # Pattern for partial transparency
        )

    def _on_drag(self, event):
        """Handle mouse drag"""
        if self.rect:
            # Update rectangle coordinates
            self.canvas.coords(
                self.rect, #select the rectangle
                self.start_x, self.start_y, #keep the starting coordinates
                event.x, event.y #dynamically change the coordinates
            )

            # Create a mask to show undarkened area inside rectangle
            self._update_selection_preview(event.x, event.y)

    def _update_selection_preview(self, end_x, end_y):
        """Update the selection preview"""
        # First remove any existing preview image
        if hasattr(self, 'preview_image'):
            self.canvas.delete(self.preview_image)

        # Crop the original screenshot to selection area
        x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
        x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)
        width, height = x2 - x1, y2 - y1

        if width > 0 and height > 0:
            cropped = self.screenshot.crop((x1, y1, x2, y2))
            preview_img = ImageTk.PhotoImage(cropped)

            # Keep reference to prevent garbage collection
            self.preview_img_ref = preview_img

            # Display the undarkened preview
            self.preview_image = self.canvas.create_image(
                x1, y1,
                image=preview_img,
                anchor=tk.NW
            )

    def _on_release(self, event):
        """Handle mouse button release - finalize selection"""
        if self.rect:
            self.final_coords = (
                min(self.start_x, event.x), #min is used to account for reverse dragging
                min(self.start_y, event.y),
                abs(event.x - self.start_x),
                abs(event.y - self.start_y)
            )
            self.selection_made = True
            self.root.quit()

    def get_selection(self):
        """Run the calibration tool and return coordinates"""
        self._create_overlay()
        self.root.mainloop()
        self.root.destroy()

        # Properly restore console window
        self._restore_console()

        if self.selection_made and self.final_coords:
            return self.final_coords
        return None
