"""The main config file for Pangolin

Pangolin provides a controlled interface
to ensure configuration integrity and to prevent
invalid or unexpected configuration values
from being applied at runtime.
"""

import configparser
import os

class Config:
    def __init__(self, config_file_name: str):
        self.config_file_name = config_file_name
        self.config_load_success_message = f"[INFO] Pangolin configuration file ({self.config_file_name}) loaded."
        self.config_file_not_found_message = f"[INFO] Configuration file ({self.config_file_name}) not found."

    def load(self, allow_missing: bool) -> configparser.ConfigParser:
        if not os.path.exists(self.config_file_name):
            if not allow_missing:
                raise FileNotFoundError(self.config_file_not_found_message)

        config = configparser.ConfigParser()
        config.read(self.config_file_name, encoding="utf-8")

        print(self.config_load_success_message + "\n")

        return config

    def print_message(self, message):
        print(message)
