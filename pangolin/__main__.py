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
from pangolin import StreamManager

# Parse WebSocket URL into components (scheme, netloc, path, etc.)
from urllib.parse import urlparse

# define main function
def main():
    # Create a Config object
    config = Config()

    # Load the configuration file
    loaded_config = config.load(
        file_path=config.CONFIG_FILE_NAME,
        allow_missing=False
    )

    # Create an instance of UrlFactory to generate WebSocket URL
    url_factory = UrlFactory()

    # Check if Binance is enabled in the configuration
    if loaded_config['Binance'].getboolean('is_enabled'):
        base_url = loaded_config['Binance']['base_url']
        symbol = loaded_config['Binance']['supported_coin'].lower()
        parsed_url = urlparse(base_url)

    # Generate the WebSocket URL
    wss_url = url_factory.create_wss_url(
        netloc=parsed_url.netloc,
        ticker=symbol + 'usdt'
    )

    # Initialize the StreamManager
    manager = StreamManager(
        loaded_config=loaded_config['Binance'],
        wss_url=wss_url
    )

    # Execute the manager to start the associated tasks
    manager.run()

# Execute only run as a script
if __name__ == '__main__':
    main()
