import configparser
import os

class Config:
    """ Config class for parsing configuration files """
    def __init__(self, file_name):
        print('*** Config Class ***')

        # check if the configuration file exists
        if not os.path.exists(file_name):
            raise FileNotFoundError(f"Configuration file not found: '{file_path}'")

        # create a ConfigParser instance and read the configuration file
        config = configparser.ConfigParser()
        config.read(file_name)

        # allowed keys in [DEFAULT]
        allowed_config_keys = ['allowed_class_names', 'allowed_value_names']

        # parsing [DEFAULT] section for allowed keys
        for allowed_config_key in allowed_config_keys:
            allowed_config_value = config['DEFAULT'][allowed_config_key]
            setattr(self, allowed_config_key, [])
            if ',' in allowed_config_value:
                allowed_config_values = allowed_config_value.lower().split(',')
                for value in allowed_config_values:
                    getattr(self, allowed_config_key).append(value.strip())
            else:
                getattr(self, allowed_config_key).append(allowed_config_value.strip())

        # add config values as attributes for allowed classes, skipping disallowed keys
        for allowed_class_name in self.allowed_class_names:
            for config_section in config.sections():
                if allowed_class_name == config_section:
                    for config_key in config[allowed_class_name]:
                        if config_key not in allowed_config_keys:
                            config_value = config[allowed_class_name][config_key]
                            setattr(self, allowed_class_name + '_' + config_key, config_value)
