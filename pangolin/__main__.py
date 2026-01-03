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
""" Main entry point for running Pangolin

This allows running the service with: python3 -m pangolin
"""

from pangolin import Config
from pangolin import UrlFactory
from pangolin import StreamManager

from urllib.parse import urlparse

# define main function
def main():
    config = Config()
    loaded_config = config.load(
        file_path=config.CONFIG_FILE_NAME,
        allow_missing=False
    )

    # url factory ?
    url_factory = UrlFactory()

    if loaded_config['Binance'].getboolean('is_enabled'):
        base_url = loaded_config['Binance']['base_url']
        symbol = loaded_config['Binance']['supported_coin'].lower()
        parsed_url = urlparse(base_url)

        wss_url = url_factory.create_wss_url(
            netloc=parsed_url.netloc,
            ticker=symbol + 'usdt'
        )

        manager = StreamManager(
            loaded_config=loaded_config['Binance'],
            wss_url=wss_url
        )
    else:
        manager = None

    if manager is not None:
        manager.run()

# execute only run as a script
if __name__ == '__main__':
    main()
