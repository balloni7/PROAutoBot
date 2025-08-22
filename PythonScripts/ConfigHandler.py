import configparser
import os


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
    'AutoCatch': {
        'sync_enabled': {'type': lambda x: True if x == "True" else False, 'default': True },
        'fs_enabled': {'type': lambda x: True if x == "True" else False , 'default':True},
        'fs_pokemon_position': {'type': str, 'default': "2"},
        'fs_move_position': {'type':str, 'default': "1"},
        'repel_enabled': {'type':lambda x: True if x == "True" else False, 'default':False},
        'ball_to_use': {'type': str, 'default': "1"}
    },
    'Advanced': {
        'scan_interval': {'type': float, 'default': 0.1},
        'move_delay': {'type': float, 'default': 0.01}
    },
    'Files': {
        'names_file': {'type': str, 'default': 'Resources/pokemon_names.txt'},
        'shiny_template': {'type': str, 'default': 'Resources/shiny_message.png'},
        'battle_template': {'type': str, 'default': 'Resources/battle_template.png'},
        'gray_action_icon': {'type':str, 'default': 'Resources/gray_action_icon.png'},
        'red_action_icon': {'type':str, 'default': 'Resources/red_action_icon.png'},
        'shiny_sound': {'type':str, 'default': 'Resources/ShinyEncounterSound.wav'},
        'wanted_sound': {'type':str, 'default': 'Resources/WantedEncounterSound.wav'}
    }
}



class ConfigHandler:
    def __init__(self, config_path='CONFIG.ini'):
        self.configParser = configparser.ConfigParser()
        self.config_path = config_path
        self.schema = CONFIG_SCHEMA
        if not os.path.exists(self.config_path):
            self.generate_default_config_file()
        else:
            self.configParser.read(config_path)

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

    def _save_config(self):
        """SAve current configurations onto a config file"""
        with open(self.config_path, 'w') as f:
            self.configParser.write(f)

    def get(self, section, option, default=None):
        """Get value with proper type conversion using schema"""
        try:
            value_type = self.schema[section][option]['type']
            raw_value = self.configParser[section][option]
            return value_type(raw_value)
        except (KeyError, ValueError):
            return default if default is not None else self.schema[section][option]['default']

    def set(self, section, option, value):
        """Set value and auto-save"""
        if section not in self.configParser:
            self.configParser[section] = {}
        self.configParser[section][option] = str(value)
        self._save_config()

    def generate_default_config_file(self):
        self.configParser.read_dict(self._generate_default_dict())
        self._save_config()




