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
"""Main Entry Point for Running Pangolin.
This file (__main__.py) initializes components required before running the software,
including configuration loading (Config), WebSocket URL generation (UrlFactory),
and Manager (StreamManager) that handles real-time trade data and strategy module(s).

Execution flow:
1. Load and validate the configuration file using Config.
2. Generate the WebSocket URL for the specified trading pair using UrlFactory.
3. Initialize StreamManager and start the infinite loop by calling `run()`.

Additional Notes:
- API calls are not handled in this module or in StreamManager.
  They should be managed within the strategy module.
- Terminate the program safely using Ctrl + C.
"""

# Load Pangolin components
from pangolin import Config
from pangolin import UrlFactory
from pangolin import Database
from pangolin import Client
from pangolin import StreamManager

from urllib.parse import urlparse
import os

# -----------------------------
# Project and data paths
# -----------------------------
PROJECT_NAME = 'pangolin'
DATA_FOLDER_NAME = 'data'

# -----------------------------
# Order placement file
# -----------------------------
ORDER_PLACE_FILE_NAME = 'order_place.json'
ORDER_PLACE_FILE_PATH = os.path.join(PROJECT_NAME, DATA_FOLDER_NAME, ORDER_PLACE_FILE_NAME)

# -----------------------------
# Configuration file
# -----------------------------
CONFIG_FILE_NAME = 'pangolin.ini'

# -----------------------------
# Database file
# -----------------------------
DATABASE_FILE_NAME = 'pangolin.db'

# -----------------------------
# Exchange identifiers
# -----------------------------
BINANCE_EXCHANGE_NAME = 'binance'
BINANCE_EXCHANGE_NAME_CAPITALIZED = BINANCE_EXCHANGE_NAME.capitalize()

def main():
    config = Config(config_file_name=CONFIG_FILE_NAME)
    loaded_config = config.load(allow_missing=False)
    url_factory = UrlFactory()

    if binance_enabled(loaded_config):
        enabled_exchange_name = BINANCE_EXCHANGE_NAME
        enabled_exchange_name_capitalized = BINANCE_EXCHANGE_NAME_CAPITALIZED
        netloc = urlparse(loaded_config[enabled_exchange_name_capitalized]['wss_url']).netloc
        ticker = loaded_config[enabled_exchange_name_capitalized]['supported_coin'].lower() + 'usdt'
        database = Database(enabled_exchange_name, database_file_name=DATABASE_FILE_NAME)
        wss_url = url_factory.create_wss_url(enabled_exchange_name=enabled_exchange_name, netloc=netloc, ticker=ticker)

    client = Client(enabled_exchange_name=enabled_exchange_name, order_place_file_name=ORDER_PLACE_FILE_NAME)
    loaded_exchange_config = loaded_config[enabled_exchange_name_capitalized]
    manager = StreamManager(
        enabled_exchange_name=enabled_exchange_name,
        loaded_exchange_config=loaded_exchange_config,
        database=database,
        wss_url=wss_url,
        order_place_file_name=ORDER_PLACE_FILE_NAME
    )

    manager.run()

def binance_enabled(config):
    return config['Binance'].getboolean('is_enabled')

# execute only run as a script
if __name__ == '__main__':
    main()
