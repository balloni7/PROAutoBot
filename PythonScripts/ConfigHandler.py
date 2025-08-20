import configparser
import os
from email.policy import default

CONFIG_SCHEMA = {
    'Movement': {
        'ntiles': {'type': int, 'default': 15},
        'afk_interval': {'type': float, 'default': 3600},
        'afk_duration': {'type': float, 'default': 300},
        'afk_randomness': {'type': float, 'default': 0.3},
        'movement_speed': {'type': float, 'default': 7.5},
        'min_move_time': {'type': float, 'default': 0.1},
        'starting_direction': {'type': str, 'default': 'left'}
    },
    'OCR': {
        'name_region': {
            'type': lambda x: tuple(map(int, x.strip("()").split(','))),
            'default': (0, 0, 300, 100)
        },
        'shiny_threshold': {'type': float, 'default': 0.8},
        'battle_threshold': {'type': float, 'default': 0.8},
        'wanted_pokemon': {
            'type': lambda x: tuple(map(str, x.strip("()").replace(" ","").split(','))),
            'default': ()
        }
    },
    'Advanced': {
        'scan_interval': {'type': float, 'default': 0.1},
        'move_delay': {'type': float, 'default': 0.01}
    },
    'Files': {
        'shiny_template': {'type': str, 'default': 'Resources/shiny_message.png'},
        'battle_template': {'type': str, 'default': 'Resources/battle_template.png'},
        'shiny_sound': {'type':str, 'default': 'Resources/ShinyEncounterSound.wav'},
        'wanted_sound': {'type':str, 'default': 'Resources/WantedEncounterSound.wav'}
    }
}



class ConfigHandler:
    def __init__(self, config_path='CONFIG.ini'):
        self.configParser = configparser.ConfigParser()
        self.config_path = config_path
        self.schema = CONFIG_SCHEMA
        self.settings = self._load()

    def _load(self):
        """Load or create config with automatic validation"""

        # Create default if missing
        if not os.path.exists(self.config_path):
            self.configParser.read_dict(self._generate_default_dict())
            self.save_config()
        else:
            try:
                self.configParser.read(self.config_path)
            except (ValueError, configparser.Error) as e:
                print(f"Error reading config: {e}")
                raise

            if not self._validate():
                self.configParser.read_dict(self._generate_default_dict())
                self.save_config()

        return self._parse()

    def _generate_default_dict(self):
        """Generate dict with default values from schema"""

        # Use a dictionary comprehension to iterate the schema dict
        default_dict = {
            section: {
                key: str(val['default'])
                for key, val in settings.items()
            }
            for section, settings in self.schema.items()
        }

        return default_dict

    def _parse(self):
        """Convert ConfigParser to final format using schema returning a dictionary with all settings"""

        # Use the Schema to convert the values (strings) into its correct datatypes
        parsed = {}
        for section, settings in self.schema.items():
            parsed[section] = {
                key: settings[key]['type'](self.configParser[section][key])
                for key in settings
            }
        return parsed

    def _validate(self):
        """
        Validate config against schema
        Weak validation, just checks if all the sections and settings exist, not their values, nor extra sections
        """
        try:
            return all(
                section in self.configParser and
                all(key in self.configParser[section] for key in settings)
                for section, settings in self.schema.items()
            )
        except (KeyError, AttributeError):
            return False

    def save_config(self):
        """SAve current configurations onto a config file"""
        with open(self.config_path, 'w') as f:
            self.configParser.write(f)

    def generate_default_config_file(self):
        self.configParser.read_dict(self._generate_default_dict())
        self.save_config()
