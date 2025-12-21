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

from contextlib import closing
from websocket import create_connection
from collections import deque
from typing import Mapping
from datetime import datetime
import json

class StreamManager:
    """ WebSocket-based trade stream processor

    """
    def __init__(self, loaded_config: Mapping[str, str], wss_url: str):
        self._config: Mapping[str, str] = loaded_config
        self._wss_url: str = wss_url

        # state
        self._previous_trade_id: int | None = None
        self._cumulative_price: float = 0.0
        self._count: int = 0

        # previously processed price
        self._last_price: float | None = None

    def run(self):
        with closing(
            create_connection(self._wss_url)
        ) as conn:
            try:
                while True:
                    # receive raw message from connection
                    message = conn.recv()

                    # parse received message into JSON object
                    json_data = json.loads(message)

                    # convert data
                    trade_id = int(json_data['a'])
                    symbol = str(json_data['s'])
                    price = float(json_data['p'])
                    timestamp = int(json_data['T']) / 1000 # convert milliseconds to seconds

                    if self._last_price is None:
                        self._last_price = price

                    # add
                    self._cumulative_price += price

                    # trade count
                    self._count += 1
                    if self._count == 15:
                        # from float to int
                        self._cumulative_price = float(self._cumulative_price)

                        # count average price
                        self._avg_price = self._cumulative_price / self._count

                        # from float to int
                        self._avg_price = float(self._avg_price)

                        # get current time
                        now = datetime.now()
                        self.now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        # print
                        print(f'[{self._count}] {self.now} | avg_price: {self._cumulative_price}/{self._count} -> {self._avg_price}')

                        # reset
                        self._count = 0
                        self._cumulative_price = 0.0

            except KeyboardInterrupt:
                print("Interrupted!")
