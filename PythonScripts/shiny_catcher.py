import pyautogui
import cv2
import numpy as np
import time
import keyboard
import sys
import random

import os
from ConfigHandler import ConfigHandler

import json
import csv
from datetime import datetime
from collections import defaultdict

from PokemonElementsOCR import PokemonElementsOCR
class ShinyCatcher:
    def __init__(self, config_path="CONFIG.ini"):
        self.configHandler = ConfigHandler(config_path)
        self.config_settings = self.configHandler.settings
        self.encounterCounter = EncounterCounter()
        self.shiny_template = self._load_shiny_template()
        self.battle_template = self._load_battle_template()
        self.current_direction = self._load_starting_direction()
        self.next_switch_time = 0
        self.next_afk_time = time.time() + self._get_random_afk_interval()

    def _load_shiny_template(self):
        """Load the shiny message template image"""

        try:
            template = cv2.imread(self.config_settings["Files"]["shiny_template"], 0)
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
            template = cv2.imread(self.config_settings["Files"]["battle_template"], 0)
            if template is None:
                raise FileNotFoundError
            return template
        except Exception as e:
            print(f"Error loading battle template image: {e}")
            print("Please provide a 'battle_message.png' file in the same directory.")
            sys.exit(1)

    def _load_starting_direction(self):
        """Load the starting direction"""
        if self.config_settings["Movement"]["starting_direction"] == "left":
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
        afk_interval = self.config_settings["Movement"]["afk_interval"]
        afk_randomness = self.config_settings["Movement"]["afk_randomness"]

        return random.normalvariate(afk_interval, afk_interval * afk_randomness)

    def _cleanup(self):
        """Clean up resources and save logs"""
        keyboard.release('a')
        keyboard.release('d')

        # Save encounter data
        self.encounterCounter.display_stats()
        self.encounterCounter.save_to_json()
        self.encounterCounter.save_to_csv()



    def main(self):
        """Main execution loop"""
        ntiles = self.config_settings["Movement"]["ntiles"]
        afk_interval = self.config_settings["Movement"]["afk_interval"]
        afk_duration = self.config_settings["Movement"]["afk_duration"]
        movement_speed = self.config_settings["Movement"]["movement_speed"]
        min_move_time = self.config_settings["Movement"]["min_move_time"]
        afk_randomness = self.config_settings["Movement"]["afk_randomness"]

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
                    self.encounterCounter.record_encounter()
                    keyboard.release(self.current_direction)
                    self.run_from_battle()
                    time.sleep(2)
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
            self._cleanup()
            print("\nScript stopped by user.")


class EncounterCounter:
    def __init__(self, save_path='EncounterLogs'):
        self.elementsOCR = PokemonElementsOCR()
        self.encounters = defaultdict(int)  # {pokemon_name: count}
        self.total_encounters = 0
        self.start_time = datetime.now()
        self.save_path = save_path

        # Create save directory if it doesn't exist
        os.makedirs(save_path, exist_ok=True)

    def record_encounter(self):
        """Record a new Pokémon encounter"""
        pokemon_name = self.elementsOCR.detect_pokemon_name()
        if pokemon_name:  # Only record if we got a valid name
            self.encounters[pokemon_name] += 1
            self.total_encounters += 1
            print(f"Encounter #{self.total_encounters}: {pokemon_name}")

    def get_stats(self):
        """Get current encounter statistics"""
        return {
            'total': self.total_encounters,
            'by_pokemon': dict(self.encounters),
            'session_duration': str(datetime.now() - self.start_time),
            'start_time': self.start_time.isoformat()
        }

    def save_to_json(self):
        """Save encounters to JSON file"""
        filename = f"{self.save_path}/encounters_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        data = self.get_stats()

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved {self.total_encounters} encounters to {filename}")
        return filename

    def save_to_csv(self):
        """Save encounters to CSV file"""
        filename = f"{self.save_path}/encounters_{self.start_time.strftime('%Y%m%d_%H%M%S')}.csv"

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Pokemon', 'Count', 'Percentage'])

            for pokemon, count in sorted(self.encounters.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / self.total_encounters * 100) if self.total_encounters > 0 else 0
                writer.writerow([pokemon, count, f"{percentage:.1f}%"])

            writer.writerow([])
            writer.writerow(['Total', self.total_encounters, '100%'])
            writer.writerow(['Session Start', self.start_time.strftime('%Y-%m-%d %H:%M:%S'), ''])
            writer.writerow(['Session Duration', str(datetime.now() - self.start_time), ''])

        print(f"Saved {self.total_encounters} encounters to {filename}")
        return filename

    def display_stats(self):
        """Display current statistics to console"""
        print(f"\n=== ENCOUNTER STATISTICS ===")
        print(f"Total encounters: {self.total_encounters}")
        print(f"Session duration: {datetime.now() - self.start_time}")
        print("\nBy Pokémon:")
        for pokemon, count in sorted(self.encounters.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / self.total_encounters * 100) if self.total_encounters > 0 else 0
            print(f"  {pokemon}: {count} ({percentage:.1f}%)")



if __name__ == "__main__":
    sc = ShinyCatcher()
    sc.main()