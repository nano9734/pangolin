import configparser
import os

class Config:
    def __init__(self, file_name):
        # check if the configuration exists
        if not os.path.exists(file_name):
            raise FileNotFoundError(f"Configuration file not found: '{file_path}'")

        # create a ConfigParser instance
        config = configparser.ConfigParser()
        config.read(file_name)

        # allowed keys in [DEFAULT]
        self.allowed_config_keys = ['allowed_class_names', 'allowed_value_names']

        # parse the [DEFAULT] section for each allowed key
        for allowed_config_key in self.allowed_config_keys:
            allowed_config_value = config['DEFAULT'][allowed_config_key]
            setattr(self, allowed_config_key, [])
            if ',' in allowed_config_value:
                allowed_config_values = allowed_config_value.lower().split(',')
                for value in allowed_config_values:
                    getattr(self, allowed_config_key).append(value.strip())
            else:
                getattr(self, allowed_config_key).append(allowed_config_value.strip())

        # add allowed config values as object attributes
        for allowed_class_name in self.allowed_class_names:
            for config_section in config.sections():
                if allowed_class_name == config_section:
                    for config_key in config[allowed_class_name]:
                        if config_key not in self.allowed_config_keys:
                            config_value = config[allowed_class_name][config_key]
                            setattr(self, allowed_class_name + '_' + config_key, config_value)
