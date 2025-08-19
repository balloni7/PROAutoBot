import pyautogui
import cv2
import numpy as np
import time
import keyboard
import sys
import random

import os
from ConfigHandler import ConfigHandler
class ShinyCatcher:
    def __init__(self, config_path="CONFIG.ini"):
        self.configHandler = ConfigHandler(config_path)
        self.config_settings = self.configHandler.load()
        self.shiny_template = self._load_shiny_template()
        self.battle_template = self._load_battle_template()
        self.current_direction = self._load_starting_direction()
        self.next_switch_time = 0
        self.next_afk_time = time.time() + self._get_random_afk_interval()

    def _load_shiny_template(self):
        """Load the shiny message template image"""

        try:
            template = cv2.imread(self.config_settings["files"]["shiny_template"], 0)
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
            template = cv2.imread(self.config_settings["files"]["battle_template"], 0)
            if template is None:
                raise FileNotFoundError
            return template
        except Exception as e:
            print(f"Error loading battle template image: {e}")
            print("Please provide a 'battle_message.png' file in the same directory.")
            sys.exit(1)

    def _load_starting_direction(self):
        """Load the starting direction"""
        if self.config_settings["movement"]["starting_direction"] == "left":
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
        afk_interval = self.config_settings["movement"]["afk_interval"]
        afk_randomness = self.config_settings["movement"]["afk_randomness"]

        return random.normalvariate(afk_interval, afk_interval * afk_randomness)


    def main(self):
        """Main execution loop"""
        ntiles = self.config_settings["movement"]["ntiles"]
        afk_interval = self.config_settings["movement"]["afk_interval"]
        afk_duration = self.config_settings["movement"]["afk_duration"]
        movement_speed = self.config_settings["movement"]["movement_speed"]
        min_move_time = self.config_settings["movement"]["min_move_time"]
        afk_randomness = self.config_settings["movement"]["afk_randomness"]

        print(f"Starting shiny hunter for {ntiles} tiles...")
        print(f"AFK settings: ~{afk_interval / 60:.1f}min active, ~{afk_duration / 60:.1f}min breaks")

        # Movement configuration
        base_move_time = ntiles / movement_speed
        min_move_time = max(min_move_time, base_move_time * 0.5)
        max_move_time = base_move_time * 0.8

        self.next_afk_time = time.time() + self._get_random_afk_interval()

        try:
            while True:
                current_time = time.time()

                # AFK Check
                if current_time >= self.next_afk_time:
                    # Calculate random AFK duration (exponential distribution)
                    afk_time = min(afk_duration* 2,
                                   random.expovariate(1 / (afk_duration * (1 - afk_randomness))))

                    print(f"\n--- Going AFK for {afk_time / 60:.1f} minutes ---")
                    keyboard.release(self.current_direction)
                    time.sleep(afk_time)
                    print("--- Returning from AFK ---\n")

                    # Reset next AFK time with randomness
                    self.next_afk_time = time.time() + random.normalvariate(
                        afk_interval, afk_interval * afk_randomness)

                    # Reset movement
                    self.current_direction = 'a'
                    self.next_switch_time = time.time() + random.uniform(min_move_time, max_move_time)
                    keyboard.press(self.current_direction)

                # Shiny check
                if self.is_shiny_present():
                    print("SHINY FOUND! Stopping script.")
                    break

                # Battle handling
                if self.is_in_battle():
                    keyboard.release(self.current_direction)
                    self.run_from_battle()
                    self.next_switch_time = time.time() + random.uniform(min_move_time, max_move_time)
                    keyboard.press(self.current_direction)

                # Movement control
                if current_time >= self.next_switch_time:
                    keyboard.release(self.current_direction)
                    self.current_direction = 'd' if self.current_direction == 'a' else 'a'
                    move_duration = random.uniform(min_move_time, max_move_time)
                    self.next_switch_time = current_time + move_duration
                    keyboard.press(self.current_direction)

                # Sleep between Checks
                time.sleep(0.1)

        except KeyboardInterrupt:
            keyboard.release('a')
            keyboard.release('d')
            print("\nScript stopped by user.")

if __name__ == "__main__":
    sc = ShinyCatcher()
    sc.main()