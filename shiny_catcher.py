import pyautogui
import cv2
import numpy as np
import time
import keyboard
import sys
import random

import os
import configparser

class ShinyCatcher:
    def __init__(self, config_path="CONFIG.ini"):
        self.config = self._load_config(config_path)
        self.shiny_template = self._load_shiny_template()
        self.battle_template = self._load_battle_template()
        self.current_direction = self._load_starting_direction()
        self.next_switch_time = 0
        self.next_afk_time = time.time() + self._get_random_afk_interval()


    def _load_config(self,config_path):
        """Load and parse configuration file"""
        config = configparser.ConfigParser()
        config.read(config_path)

        try:
            return {
                'movement': {
                    'ntiles': config.getint('Movement', 'ntiles'),
                    'afk_interval': config.getfloat('Movement', 'afk_interval'),
                    'afk_duration': config.getfloat('Movement', 'afk_duration'),
                    'afk_randomness': config.getfloat('Movement', 'afk_randomness'),
                    'speed': config.getfloat('Movement', 'speed'),
                    'min_move_time': config.getfloat('Movement', 'min_move_time'),
                    'starting_direction': config.get('Movement', 'starting_direction')
                },
                'ocr': {
                    'name_region': tuple(map(int, config.get('OCR', 'name_region').split(','))),
                    'shiny_threshold': config.getfloat('OCR', 'shiny_threshold'),
                    'battle_threshold': config.getfloat('OCR', 'battle_threshold')
                },
                'advanced': {
                    'scan_interval': config.getfloat('Advanced', 'scan_interval'),
                    'move_delay': config.getfloat('Advanced', 'move_delay')
                },
                'files':{
                    'shiny_template': config.get('Files', 'shiny_template'),
                    'battle_template': config.get('Files', 'battle_template')
                }
            }
        except (ValueError, configparser.Error) as e:
            print(f"Error reading config: {e}")
            raise



    def _load_shiny_template(self):
        """Load the shiny message template image"""
        try:
            template = cv2.imread(self.config["files"]["shiny_template"], 0)
            if template is None:
                raise FileNotFoundError
            return template
        except Exception as e:
            print(f"Error loading shiny template image: {e}")
            print("Please provide a 'shiny_message.png' file in the same directory.")
            sys.exit(1)

    def _load_battle_template(self):
        """Load the shiny message template image"""
        try:
            template = cv2.imread(self.config["files"]["battle_template"], 0)
            if template is None:
                raise FileNotFoundError
            return template
        except Exception as e:
            print(f"Error loading battle template image: {e}")
            print("Please provide a 'battle_message.png' file in the same directory.")
            sys.exit(1)

    def _load_starting_direction(self):
        """Load the starting direction"""
        if self.config["movement"]["starting_dirction"] == "left":
            return "a"
        else:
            return "d"

    def is_shiny_present(self):
        """Check if the shiny message is on screen"""
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

        # Template matching
        res = cv2.matchTemplate(screenshot, self.shiny_template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        loc = np.where(res >= threshold)

        return len(loc[0]) > 0


    def run_from_battle(self):
        """Runs from battle"""
        keyboard.press('4')
        time.sleep(0.1)
        keyboard.release('4')


    def move_character(self, direction):
        """Move the character left or right"""
        keyboard.press(direction)
        time.sleep(0.01)  # Short movement duration
        keyboard.release(direction)


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

    def _get_random_afk_interval(self):
        """Calculate random AFK interval"""
        cfg = self.config['movement']
        return random.normalvariate(cfg['afk_interval'], cfg['afk_interval'] * cfg['afk_randomness'])


    def main(self):
        """Main execution loop"""
        movement = self.config["movement"]
        files = self.config["files"]

        print(f"Starting shiny hunter for {movement["ntiles"]} tiles...")
        print(f"AFK settings: ~{movement["afk_interval"] / 60:.1f}min active, ~{movement["afk_duration"] / 60:.1f}min breaks")

        # Movement configuration
        base_move_time = movement["ntiles"] / movement["movement_speed"]
        min_move_time = max(movement["min_movement_time"], base_move_time * 0.5)
        max_move_time = base_move_time * 0.8

        self.next_afk_time = time.time() + self._get_random_afk_interval()

        try:
            while True:
                current_time = time.time()

                # AFK Check
                if current_time >= next_afk_time:
                    # Calculate random AFK duration (exponential distribution)
                    afk_time = min(movement["afk_duration"] * 2,
                                   random.expovariate(1 / (movement["afk_duration"] * (1 - movement["afk_randomness"]))))

                    print(f"\n--- Going AFK for {afk_time / 60:.1f} minutes ---")
                    keyboard.release(current_direction)
                    time.sleep(afk_time)
                    print("--- Returning from AFK ---\n")

                    # Reset next AFK time with randomness
                    next_afk_time = time.time() + random.normalvariate(
                        movement["afk_interval"], movement["afk_interval"] * movement["afk_randomness"])

                    # Reset movement
                    current_direction = 'a'
                    next_switch_time = time.time() + random.uniform(min_move_time, max_move_time)
                    keyboard.press(current_direction)

                # Shiny check
                if self.is_shiny_present():
                    print("SHINY FOUND! Stopping script.")
                    break

                # Battle handling
                if self.is_in_battle():
                    keyboard.release(current_direction)
                    self.run_from_battle()
                    next_switch_time = time.time() + random.uniform(min_move_time, max_move_time)
                    keyboard.press(current_direction)

                # Movement control
                if current_time >= next_switch_time:
                    keyboard.release(current_direction)
                    current_direction = 'd' if current_direction == 'a' else 'a'
                    move_duration = random.uniform(min_move_time, max_move_time)
                    next_switch_time = current_time + move_duration
                    keyboard.press(current_direction)

                # Sleep between Checks
                time.sleep(0.1)

        except KeyboardInterrupt:
            keyboard.release('a')
            keyboard.release('d')
            print("\nScript stopped by user.")

if __name__ == "__main__":
    sc = ShinyCatcher()
    sc.main()

    #Falta testar