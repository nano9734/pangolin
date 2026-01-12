# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <https://www.gnu.org/licenses/>.
"""The main config file for Pangolin

Pangolin provides a controlled interface
to ensure configuration integrity and to prevent
invalid or unexpected configuration values
from being applied at runtime.
"""

import configparser
import os
import sys

class Config:
    def __init__(self, config_file_name: str, config_section_header_name: str):
        self.CONFIG_SECTION_HEADER_NAME = config_section_header_name 
        self.CONFIG_FILE_NAME = config_file_name
        self.CONFIG_LOAD_SUCCESS_MSG = f'[INFO] Pangolin configuration file ({self.CONFIG_FILE_NAME}) loaded.'
        self.CONFIG_FILE_NOT_FOUND_MSG = '[INFO] Configuration file not found:' + self.CONFIG_FILE_NAME

    def load(self, allow_missing: bool) -> configparser.ConfigParser:
        print(self.CONFIG_SECTION_HEADER_NAME)
        if not os.path.exists(self.CONFIG_FILE_NAME):
            if not allow_missing:
                raise FileNotFoundError(self.CONFIG_FILE_NOT_FOUND_MSG)

        config = configparser.ConfigParser()
        config.read(self.CONFIG_FILE_NAME, encoding='utf-8')

        print(self.CONFIG_LOAD_SUCCESS_MSG)
        print() # add a line break for console readability

        return config
