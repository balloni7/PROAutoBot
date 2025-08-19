from PokemonElementsOCR import PokemonElementsOCR
from ConfigHandler import ConfigHandler


class CalibrationToolUI:
    def __init__(self, config_path="CONFIG.ini"):
        self.configHandler = ConfigHandler(config_path)
        self.detector = PokemonElementsOCR(config_handler=self.configHandler)
        self.running = True
        self._setup_menu()

    def _setup_menu(self):
        """Define menu structure"""
        self.menu = {
            "header": self._create_header,
            "1": {"label": "Change name region", "action": self.detector.calibrate_name_position},
            "2": {"label": "Detect name", "action": lambda: print(self.detector.detect_pokemon_name())},
            "save": {"label": "Save", "action": self._save_config},
            "exit": {"label": "Exit", "action": self._exit_tool}
        }

    @staticmethod
    def _create_header():
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

        print("\n" * 3 + "=" * 50)
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
        self.configHandler.save_config()
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