import configparser
import os

class Config:
    CONFIG_FILE_NAME = 'pangolin.ini'

    # allowed names to prevent text input errors
    CONFIG_ALLOWED_CLASS_NAMES = ['Config', 'Database', 'APIManager', 'StreamManager']
    CONFIG_ALLOWED_EXCHANGE_NAMES = ['Binance']
    CONFIG_ALLOWED_CONFIG_KEYS = ['supported_coin_list', 'developer_mode']

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

        # Enable developer mode if configured
        self.developer_mode_enabled = False
        if config['DEFAULT']['developer_mode'] == 'yes':
            self.developer_mode_enabled = True

        # validate the sections in the given config.
        self.validate_config_sections(config)

        print('[INFO] All sections are checked and ready to go!\n')

        # instance variable factory
        for config_allowed_exchange_name in self.CONFIG_ALLOWED_EXCHANGE_NAMES:
            for config_allowed_key in config[config_allowed_exchange_name]:
                config_allowed_key_value = config[config_allowed_exchange_name][config_allowed_key]
                if self.is_allowed_config_key(config_allowed_key) == False:
                    raise ValueError(f'[ERROR] This configuration key is not allowed: {config_allowed_key}')
                else:
                    setattr(self, config_allowed_exchange_name.lower() + '_' + config_allowed_key, config_allowed_key_value)

    def validate_config_sections(self, config):
        self.validated_class_names = []
        self.validated_exchange_names = []
        for section in config.sections():
            if section in self.CONFIG_ALLOWED_CLASS_NAMES and section not in self.validated_class_names:
                self.validated_class_names.append(section)
            elif section in self.CONFIG_ALLOWED_EXCHANGE_NAMES and section not in self.validated_exchange_names:
                self.validated_exchange_names.append(section)
            else:
                raise ValueError(f"Invalid section name: {section}")

        # check validated_exchange_name exists
        if len(self.validated_exchange_names) == 0:
            raise ValueError('[ERROR] No validated exchange names found. Please check your configuration.')

    def is_allowed_config_key(self, config_key):
        if config_key in self.CONFIG_ALLOWED_CONFIG_KEYS:
            return True
        else:
            return False
