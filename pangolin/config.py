import configparser
import os

class Config:
    CONFIG_FILE_NAME = 'pangolin.ini'
    CONFIG_ALLOWED_CLASS_NAMES = ['Config', 'Database', 'APIManager','StreamManager']
    CONFIG_ALLOWED_EXCHANGE_NAMES = ['Binance']
    CONFIG_ALLOWED_VALUE_NAMES = []

    def __init__(self):
        print('*** Config ***')

        # check if the configuration file exists
        if not os.path.exists(self.CONFIG_FILE_NAME):
            raise FileNotFoundError(f"Configuration file not found: '{self.CONFIG_FILE_NAME}'")
        else:
            print(f"[INFO] Pangolin found configuration file: '{self.CONFIG_FILE_NAME}'")

        # prepare to read configuration file
        print(f'[INFO] Reading configuration from \'{self.CONFIG_FILE_NAME}\'...')

        # create a ConfigParser instance
        config = configparser.ConfigParser()
        config.read(self.CONFIG_FILE_NAME)

        # check if the config is valid
        self.check_config_validity(config)

        # generate instance variables
        for config_allowed_exchange_name in self.CONFIG_ALLOWED_EXCHANGE_NAMES:
            for config_allowed_key in config[config_allowed_exchange_name]:
                config_allowed_key_value = config[config_allowed_exchange_name][config_allowed_key]
                setattr(self, config_allowed_exchange_name.lower() + '_' + config_allowed_key, config_allowed_key_value)

    def check_config_validity(self, config):
        self.validated_class_names = []
        self.validated_exchange_names = []
        for section in config.sections():
            if section in self.CONFIG_ALLOWED_CLASS_NAMES and section not in self.validated_class_names:
                self.validated_class_names.append(section)
            elif section in self.CONFIG_ALLOWED_EXCHANGE_NAMES and section not in self.validated_exchange_names:
                self.validated_exchange_names.append(section)
            else:
                raise ValueError(f"Invalid section name: {section}")

        print('[INFO] All sections are checked and ready to go!\n')
