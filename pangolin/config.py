# SPDX-License-Identifier: GPL-2.0-or-later

import configparser
from pathlib import Path

class Config:
    LOAD_SUCCESS_MESSAGE = "[INFO] Pangolin configuration file ({}) loaded."
    FILE_NOT_FOUND_MESSAGE = "[INFO] Configuration file ({}) not found."

    def __init__(self, config_file_name: str, allow_missing: bool):
        self.config_file_name = config_file_name
        self.allow_missing = allow_missing
        self.config_path = Path(config_file_name)
        self.config = configparser.ConfigParser()

    def loads(self) -> configparser.ConfigParser:
        if not self.config_path.exists():
            if not self.allow_missing:
                raise FileNotFoundError(self.FILE_NOT_FOUND_MESSAGE.format(self.config_path))
            else:
                print(f"[WARN] Configuration file ({self.config_path}) is missing, proceeding with defaults.")
        else:
            self.config.read(self.config_path)
            print(self.LOAD_SUCCESS_MESSAGE.format(self.config_path))
            return self.config

    def display_message(self, message):
        print() # add a line break for console readability 
        print(message)
