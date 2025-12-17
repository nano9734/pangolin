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
    CONFIG_FILE_NAME = 'pangolin.ini'

    def load(self, file_path: str, allow_missing: bool) -> configparser.ConfigParser:
        """ Loads a config file from the given file path.

        Args:
            file_path (str): File path where the config file is located.
            allow_missing (bool): If True, do not raise an error if the file is missing.

        Returns:
            configparser.ConfigParser: The loaded configuration object.

        Raises:
            FileNotFoundError: If allow_missing is False and the file does not exist.
        """
        if not os.path.exists(file_path):
            if allow_missing is False:
                raise FileNotFoundError(
                    f'Configuration file not found: "{self._CONFIG_FILE_NAME}"'
                )

        config = configparser.ConfigParser()
        config.read(file_path)

        return config
