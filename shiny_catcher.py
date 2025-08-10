import pyautogui
import cv2
import numpy as np
import time
import keyboard
import sys
import random
import argparse


# Configuration
SHINY_MESSAGE_IMAGE = 'shiny_message.png'  # You'll need to provide this

def load_shiny_template():
    """Load the shiny message template image"""
    try:
        template = cv2.imread(SHINY_MESSAGE_IMAGE, 0)
        if template is None:
            raise FileNotFoundError
        return template
    except Exception as e:
        print(f"Error loading shiny template image: {e}")
        print("Please provide a 'shiny_message.png' file in the same directory.")
        sys.exit(1)


def is_shiny_present(template):
    """Check if the shiny message is on screen"""
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

    # Template matching
    res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where(res >= threshold)

    return len(loc[0]) > 0


def run_from_battle():
    """Runs from battle"""
    keyboard.press('4')
    time.sleep(0.1)
    keyboard.release('4')


def move_character(direction):
    """Move the character left or right"""
    keyboard.press(direction)
    time.sleep(0.01)  # Short movement duration
    keyboard.release(direction)


def is_in_battle(battle_template_path='battle_template.png', threshold=0.8):
    """Check if player is in battle"""

    try:
        # Load the battle template image
        battle_template = cv2.imread(battle_template_path, 0)
        if battle_template is None:
            raise FileNotFoundError(f"Battle template image not found at {battle_template_path}")

        # Take screenshot of the game window
        screenshot = pyautogui.screenshot()
        screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

        # Perform template matching
        res = cv2.matchTemplate(screenshot_gray, battle_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)

        # Return True if the match confidence exceeds the threshold
        return max_val >= threshold

    except Exception as e:
        print(f"Error in battle detection: {e}")
        return False


def main(nTiles, afk_interval=600, afk_duration=180,
         afk_randomness=0.2, movement_speed=7.5):
    """Main function with AFK timer

    Args:
        nTiles: Number of tiles in movement area
        afk_interval: Base time between AFK periods (seconds)
        afk_duration: Base AFK duration (seconds)
        afk_randomness: Percentage variation for timers (0-1)
        movement_speed: Tiles per second
    """
    print(f"Starting shiny hunter for {nTiles} tiles...")
    print(f"AFK settings: ~{afk_interval / 60:.1f}min active, ~{afk_duration / 60:.1f}min breaks")

    # Load templates
    shiny_template = load_shiny_template()

    # Movement configuration
    MIN_MOVE_TIME = 0.1
    base_move_time = nTiles / movement_speed
    min_move_time = max(MIN_MOVE_TIME, base_move_time * 0.5)
    max_move_time = base_move_time * 0.8

    # AFK timing (using normal distribution for intervals)
    next_afk_time = time.time() + random.normalvariate(afk_interval, afk_interval * afk_randomness)
    current_direction = 'a'
    next_switch_time = 0

    try:
        while True:
            current_time = time.time()

            # AFK Check
            if current_time >= next_afk_time:
                # Calculate random AFK duration (exponential distribution)
                afk_time = min(afk_duration * 2,
                               random.expovariate(1 / (afk_duration * (1 - afk_randomness))))

                print(f"\n--- Going AFK for {afk_time / 60:.1f} minutes ---")
                keyboard.release(current_direction)
                time.sleep(afk_time)
                print("--- Returning from AFK ---\n")

                # Reset next AFK time with randomness
                next_afk_time = time.time() + random.normalvariate(
                    afk_interval, afk_interval * afk_randomness)

                # Reset movement
                current_direction = 'a'
                next_switch_time = time.time() + random.uniform(min_move_time, max_move_time)
                keyboard.press(current_direction)

            # Shiny check
            if is_shiny_present(shiny_template):
                print("SHINY FOUND! Stopping script.")
                break

            # Battle handling
            if is_in_battle():
                keyboard.release(current_direction)
                run_from_battle()
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
    # Set up argument parser for cmd
    parser = argparse.ArgumentParser(description='PRO Shiny Hunter with AFK Timer')
    parser.add_argument('-n', '--ntiles', type=int, required=True,
                        help='Number of tiles in movement area')
    parser.add_argument('-aI', '--afkInterval', type=float, default=600,
                        help='Base time between AFK periods in seconds (default: 600)')
    parser.add_argument('-aD','--afkDuration', type=float, default=180,
                        help='Base AFK duration in seconds (default: 180)')
    parser.add_argument('-aR','--afkRandomness', type=float, default=0.2,
                        help='Randomness factor (0-1) for AFK timers (default: 0.2)')
    parser.add_argument('-s','--speed', type=float, default=7.5,
                        help='Movement speed in tiles/sec (default: 7.5)')

    args = parser.parse_args()
    main(
        nTiles=args.ntiles,
        afk_interval=args.afkInterval,
        afk_duration=args.afkDuration,
        afk_randomness=args.afkRandomness,
        movement_speed=args.speed)

    #Execution Example in cmd
    #python shiny_catcher.py -n 10 -aI 60