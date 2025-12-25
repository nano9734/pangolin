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
# along with this program; if not, see <https://www.gnu.org/licenses/>
"""
This module automatically imports strategy modules.
This module creates an instance of its class.
This module passes the database cursor to each strategy instance.
"""

from pathlib import Path
import os
import sys
import importlib

class GetStrategy:
    STRATEGY_DIR = Path('pangolin/strategies')

    def __init__(self):
        print('*** GetStrategy ***')

        # all strategy paths
        self._strategy_paths = list(
            self.STRATEGY_DIR.glob('*.py')
        )

        # check and validate strategy count
        strategy_count = len(self._strategy_paths) - 1
        if strategy_count > 0:
            print(f'[INFO] {strategy_count} strategy module(s) detected and ready to load.')
        else:
            raise ValueError('[ERROR] No strategy modules found! Please add at least one strategy.')

    def run(self, cursor):
        self.strategies = []
        for strategy_path in self._strategy_paths:
            if strategy_path.stem != '__init__':
                # convert snake_case file name to PascalCase class name
                module_name = ''.join(
                    word.capitalize()
                    for word in strategy_path.stem.split('_')
                )

                # import the module and create an instance
                instance = self._import_from_path(
                    module_name,
                    strategy_path,
                    cursor # database cursor
                )

                if instance:
                    self.strategies.append(instance)

    def _import_from_path(self, module_name, strategy_path, cursor):
        """
        Dynamically import a strategy module and instantiate its class.

        Args:
            module_name (str): The PascalCase name of the class to import.
            strategy_path (Path): The path to the .py file containing the strategy.
            cursor: A database cursor to be passed to the strategy instance.

        Returns:
            instance of the strategy class if it exists, else None.

        Workflow:
            1. Load the module from the given file path.
            2. Check if the module contains a class matching `module_name`.
            3. If the class exists, create an instance of it, passing `cursor` to its constructor.
            4. Return the instance, or None if class is missing.

        Notes:
            - Each strategy class is expected to accept `cursor` in its __init__.
            - The module file name (snake_case) is converted to PascalCase for the class.
            - This allows adding new strategy files without modifying the main code.
        """
        spec = importlib.util.spec_from_file_location(
            module_name,
            strategy_path,
        )

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # if the class exists in the module, create an instance
        if hasattr(module, module_name):
            cls = getattr(module, module_name)
            instance = cls(cursor)
            return instance
        return None
