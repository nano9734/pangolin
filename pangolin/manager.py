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
""" The stream manager is a core component of this software.

It manages WebSocket stream communication, stores received data in the database,
and executes the strategy module when predefined conditions are met.

Low-level WebSocket communication is delegated to a WebSocket library, allowing
the application layer to focus on data processing.

The stream manager intentionally handles multiple responsibilities to keep the
system simple and lightweight.

No API manager is provided. The stream manager focuses on maintaining
the WebSocket receive loop.

REST API calls are intended to be handled within the strategy module. Execution
timing, including sleep control, is also managed by the strategy logic and can
be used to pause or stop the application as needed.
"""

# Standard library imports
import json
import os
import sqlite3
import time
import traceback
from datetime import datetime # Retrieve the current time as a timestamp
from typing import Mapping # Type hints for improved code readability

# WebSocket
from websocket import create_connection
from websocket import WebSocketTimeoutException
from contextlib import closing

# Strategy
from .strategies import GetStrategy

class StreamManager:
    STREAM_MANAGER_INTERRUPT_MSG = '[INFO] StreamManager interrupted by user.'
    STREAM_MANAGER_INIT_MSG = '[INFO] StreamManager initialized successfully.'
    TRADE_VALUES_RESET_MSG = '[INFO] All values related to trades have been successfully reset.'
    WAIT_FILE_DELETE_MSG = "[INFO] Trade is currently pending; the order file still exists. Waiting until it is deleted... Pausing for {} seconds."
    LOOP_PAUSED_MSG = "[INFO] Loop is currently paused..."
    ORDER_PLACE_FILE_NAME = 'order_place.json'
    ZERO_FLOAT = 0.0

    def __init__(self, loaded_config: Mapping[str, str], wss_url: str, database):
        self.TUMBLING_WINDOW_SECONDS = int(loaded_config['tumbling_window_seconds'])
        self.PAUSE_INTERVAL_SECONDS = int(loaded_config['pause_interval_seconds'])
        self.STRATEGY_INTERVAL = int(loaded_config['strategy_interval']) 
        print('*** StreamManager ***')
        self.loaded_config: Mapping[str, str] = loaded_config
        self.wss_url: str = wss_url
        self.database = database
        self.last_timestamp = time.time()
        self.reset_all_values(verbose=True)
        print() # Add a line break for console readability
        self.get_strategy = GetStrategy()

    def reset_cumulative_values(self) -> None:
        self.cumulative_count = 0
        self.cumulative_price = self.ZERO_FLOAT
        self.cumulative_quantity = self.ZERO_FLOAT

    def reset_last_values(self) -> None:
        self.last_trade_id = None
        self.last_price = None

    def reset_all_values(self, verbose: bool = False) -> None:
        self.reset_cumulative_values()
        self.reset_last_values()

        if verbose:
            print(self.TRADE_VALUES_RESET_MSG)

    def order_place_file_exist(self) -> bool:
        file_path = os.path.join('pangolin', 'data', self.ORDER_PLACE_FILE_NAME)
        return os.path.isfile(file_path)

    def run(self):
        print() # Add a line break for console readability
        self.paused = False
        self.reset_done = False
        self.timeout = 5
        self.backoff = 1
        self.max_backoff = 60
        self.loop_count = 0
        self.total_loop_count = 0

        while True: # reconnect loop
            try:
                print("[WebSocket] Connecting...")
                with closing(create_connection(self.wss_url, timeout=self.timeout)) as conn:
                    conn.settimeout(1)
                    print("[WebSocket] Connected")
                    print() # Add a line break for console readability
                    self.backoff = 1 # Reset backoff after successful connection

                    while True:  # streaming loop
                        if self.order_place_file_exist():
                            self.paused = True
                        else:
                            if self.paused: # transition point: resuming from pause
                                self.last_timestamp = time.time()
                                self.reset_all_values(verbose=True)
                                self.reset_done = True
                                self.loop_count = 0
                                self.database.clear_table()
                            self.paused = False
                            self.reset_done = False

                        if self.paused:
                            try:
                                conn.recv()
                            except WebSocketTimeoutException:
                                pass
                            except Exception as e:
                                print("[WebSocket PAUSE RECV ERROR]:", e)
                                raise

                            if not self.reset_done:
                                print(self.LOOP_PAUSED_MSG)
                                self.reset_all_values(verbose=True)
                                self.reset_done = True

                            print(self.WAIT_FILE_DELETE_MSG.format(self.PAUSE_INTERVAL_SECONDS))
                            time.sleep(self.PAUSE_INTERVAL_SECONDS)
                            continue

                        self.process_stream_data(conn)
                        time.sleep(0.05)

            except KeyboardInterrupt:
                self.database.close()
                print(self.STREAM_MANAGER_INTERRUPT_MSG)
                break

            except Exception as e:
                print("[WebSocket ERROR]:", e)
                traceback.print_exc()

            print(f"[WebSocket] Reconnecting in {self.backoff} sec...")
            time.sleep(self.backoff)
            self.backoff = min(self.max_backoff, self.backoff * 2)

    def process_stream_data(self, conn):
        try:
            message = conn.recv()
        except WebSocketTimeoutException:
            return
        except Exception as recv_e:
            print("[WebSocket RECV ERROR]:", recv_e)
            traceback.print_exc()
            raise

        try:
            json_data = json.loads(message)

            if self.is_trade_id_duplicate(trade_id=int(json_data['a'])):
                return # go to the next loop

            symbol, price, quantity, timestamp_sec = self.parse_trade_message(json_data=json_data)

            self.cumulative_count += 1
            self.cumulative_price += price
            self.cumulative_quantity += quantity

            current_timestamp = time.time()
            current_timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_timestamp))
            if current_timestamp - self.last_timestamp >= self.TUMBLING_WINDOW_SECONDS:
                self.loop_count += 1
                self.total_loop_count += 1
                self.last_timestamp += self.TUMBLING_WINDOW_SECONDS
                self.avg_price = self.cumulative_price / self.cumulative_count
                print(f'*** iteration {self.loop_count} ***')
                print(f'Received: {self.cumulative_count} messages')
                print(f'Time:     {current_timestamp_str}')
                print(f'Price:    {self.cumulative_price:.0f} / {self.cumulative_count} = {self.avg_price:.4f}')
                print(f'Quantity: {self.cumulative_quantity:.2f}')
                print() # add a line break for console readability
                self.database.insert_row(
                    symbol=symbol,
                    avg_price=self.avg_price,
                    cumulative_quantity=self.cumulative_quantity,
                    current_timestamp=current_timestamp
                )

                self.reset_cumulative_values()

                if self.loop_count % self.STRATEGY_INTERVAL == 0:
                    self.get_strategy.run(
                        cursor=self.database.cursor
                    )

        except (ValueError, KeyError, TypeError) as json_e:
            print("[JSON ERROR]:", json_e, "| message skipped")
            return

    def is_trade_id_duplicate(self, trade_id: int) -> bool:
        if trade_id == self.last_trade_id:
            return True
        self.last_trade_id = trade_id
        return False

    def parse_trade_message(self, json_data):
        symbol = str(json_data['s'])
        price = float(json_data['p'])
        quantity = float(json_data['q'])
        timestamp_ms = int(json_data["T"])
        timestamp_sec = timestamp_ms / 1000 # convert milliseconds to seconds
        return symbol, price, quantity, timestamp_sec
