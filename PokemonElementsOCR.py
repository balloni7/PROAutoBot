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
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
import configparser

class PokemonElementsOCR:
    def __init__(self):
        self.calibrator = VisualCalibrator()

        # Game Elements Coordinates
        self.name_region = None  # (left, top, width, height)

        # Load a list of all Pokémon names
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
                print(self._clean_name(text))
                return self._clean_name(text)
            return None

        except Exception as e:
            print(f"Detection error: {e}")
            return None

    def calibrate_name_position(self):
        """Interactive visual calibration"""
        region = self.calibrator.get_selection()
        if region:
            self.name_region = region
            print(f"\nCalibration successful! New detection Pokemon name region: {self.name_region}")
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


class CalibrationToolUI:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.detector = PokemonElementsOCR()
        self.running = True
        self._setup_menu()

        self.config.read("CONFIG.ini")

    def _setup_menu(self):
        """Define menu structure"""
        self.menu = {
            "header": self._create_header,
            "1": {"label": "Change name region", "action": self.detector.calibrate_name_position},
            "2": {"label": "Detect name", "action": self.detector.detect_pokemon_name},
            "save": {"label": "Save", "action": self._save_config},
            "exit": {"label": "Exit", "action": self._exit_tool}
        }

    def _create_header(self):
        """Generate colorful header"""
        print("\n" + "#" * 100)
        print("#" * 100)
        print(r"""
                       _           _____      _       _                         
            /\        | |         / ____|    | |     | |                        
           /  \  _   _| |_ ___   | |     __ _| |_ ___| |__   ___ _ __           
          / /\ \| | | | __/ _ \  | |    / _` | __/ __| '_ \ / _ \ '__|          
         / ____ \ |_| | || (_) | | |___| (_| | || (__| | | |  __/ |             
        /_/    \_\__,_|\__\___/   \_____\__,_|\__\___|_| |_|\___|_|             
                                                                                
                                                                                
          _____      _ _ _               _   _               _______          _ 
         / ____|    | (_) |             | | (_)             |__   __|        | |
        | |     __ _| |_| |__  _ __ __ _| |_ _  ___  _ __      | | ___   ___ | |
        | |    / _` | | | '_ \| '__/ _` | __| |/ _ \| '_ \     | |/ _ \ / _ \| |
        | |___| (_| | | | |_) | | | (_| | |_| | (_) | | | |    | | (_) | (_) | |
         \_____\__,_|_|_|_.__/|_|  \__,_|\__|_|\___/|_| |_|    |_|\___/ \___/|_|
        """)
        print("\n" + "#" * 100)
        print("#" * 100)

    def _print_menu(self):
        """Display interactive menu"""

        print("\n"*3 + "=" * 50)
        print("\nMENU:")
        for key, item in self.menu.items():
            if key != "header":
                print(f"[{key}] {item['label']}")
        print("\n" + "=" * 50)


    def _get_choice(self):
        """Get user input with validation"""
        while self.running:
            try:
                choice = input("\nSelect an option: ")

                if choice in self.menu or choice == "exit":
                    return choice
                print("Invalid option!")

            except KeyboardInterrupt:
                return "exit"

    def _exit_tool(self):
        """Clean exit handler"""
        print("\nExiting calibration tool...")
        self.running = False

    def _save_config(self):
        self.config["OCR"]["nameRegion"] = ','.join(map(str, self.detector.name_region))
        with open('CONFIG.ini', 'w') as configfile:
            self.config.write(configfile)
        print("Configuration saved successfully!")

    def run(self):
        """Main application loop"""
        self.menu["header"]()

        while self.running:
            self._print_menu()
            choice = self._get_choice()

            if choice == "exit":
                self._exit_tool()
            elif choice in self.menu:
                self.menu[choice]["action"]()
            else:
                print("Invalid selection!")



# Usage example:
if __name__ == "__main__":
    ui = CalibrationToolUI()

    try:
        ui.run()
    except Exception as e:
        print(f"Error: {str(e)}")
