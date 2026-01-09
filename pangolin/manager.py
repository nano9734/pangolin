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

# Standard library imports for running the manager
import json
import os
import sqlite3

# Retrieve the current time as a timestamp
from datetime import datetime

# Type hints for improved code readability
from typing import Mapping

# WebSocket connection utilities
from websocket import create_connection
from contextlib import closing

# Load strategy module(s)
from .strategies import GetStrategy

class StreamManager:
    DATABASE_FILE_NAME = 'pangolin.db'

    def __init__(self, loaded_config: Mapping[str, str], wss_url: str):
        """Initializes the instance for connecting to a WebSocket stream.

        Args:
            loaded_config: Configuration mapping for the exchange, such as Binance.
            wss_url: WebSocket stream URL used to connect to the exchange.
        """
        print('*** StreamManager ***')

        # Store the loaded configuration mapping
        self.loaded_config: Mapping[str, str] = loaded_config

        # Tumbling window duration (seconds) from configuration
        self.tumbling_window_seconds: int = int(self.loaded_config['tumbling_window_seconds'])

        # WebSocket server URL
        self.wss_url: str = wss_url

        # Last processed trade data
        self.last_trade_id: int = None
        self.last_timestamp_sec: int = None
        self.last_price: float = None

        # Cumulative statistics for processed trades
        self.cumulative_count: int = 0
        self.cumulative_time: float = 0.0
        self.cumulative_price: float = 0.0
        self.cumulative_quantity: float = 0.0

        # Inform that the StreamManager has been successfully initialized
        print('[INFO] StreamManager initialized successfully.')

        # Remove the database file if it exists before initializing the strategy module
        self.delete_database_file()

        # Instantiate the strategy handler for analyzing trade data, handling REST API calls, and managing execution timing
        self.get_strategy = GetStrategy()

        # Add a line break for console readability
        print()

    def delete_database_file(self):
        """Delete the database file if it exists and log the action."""
        if os.path.exists(self.DATABASE_FILE_NAME):
            print(f'[INFO] {self.DATABASE_FILE_NAME} database file exists. Deleting it...')
            os.remove(self.DATABASE_FILE_NAME)
            print(f'[INFO] {self.DATABASE_FILE_NAME} has been deleted.\n')
        else:
            print(f'[INFO] {self.DATABASE_FILE_NAME} does not exist, nothing to delete.\n')

    def run(self):
        with closing(create_connection(self.wss_url)) as conn:
            try:
                i = 0
                while True:

                    # receive message from connection
                    message = conn.recv()

                    # convert string to JSON
                    json_data = json.loads(message)

                    # prevent duplicate trades
                    trade_id = int(json_data['a'])

                    if trade_id == self.last_trade_id:
                        continue # go to the next loop

                    # store trade id as last trade id
                    self.last_trade_id = trade_id

                    # convert data
                    if json_data:
                        symbol = str(json_data['s'])
                        price = float(json_data['p'])
                        quantity = float(json_data['q'])
                        timestamp_ms = int(json_data["T"])

                    # convert milliseconds to seconds
                    if timestamp_ms:
                        timestamp_sec = timestamp_ms / 1000

                    # add last time
                    if self.last_timestamp_sec is not None:
                        time_diff = timestamp_sec - self.last_timestamp_sec
                        self.cumulative_time += time_diff
                        cumulative_time_str = round(self.cumulative_time, 3)

                    # add last price
                    if self.last_price is None:
                        self.last_price = price

                    # add price for self.cumulative_price
                    self.cumulative_price += price

                    # add quantity
                    self.cumulative_quantity += quantity

                    # format cumulative values
                    if self.cumulative_price:
                        cumulative_price_str = int(self.cumulative_price)

                    if self.cumulative_quantity:
                        cumulative_quantity_str = round(self.cumulative_quantity, 2)

                    # save last timestamp
                    self.last_timestamp_sec = timestamp_sec

                    # add cumulative_count
                    self.cumulative_count += 1

                    # test_point: cumulative_time | cumulative_count | cumulative_price | cumulative_quantity
                    #print(
                    #    f't:{self.cumulative_time} | '
                    #    f'c:{self.cumulative_count} | '
                    #    f'p:{self.cumulative_price} | '
                    #    f'q:{self.cumulative_quantity}'
                    #)

                    if self.cumulative_time > self.tumbling_window_seconds:
                        i += 1 # increment total count...

                        # print messeage
                        print(f'*** While Loop {i} ***')
                        print(f"[INFO] cumulative_time ({cumulative_time_str}s) exceeded the tumbling window duration.")

                        # create a database connection
                        db_conn = self._create_db_conn()

                        # create a cursor from the database connection
                        cursor = db_conn.cursor()

                        # create table if is needed
                        cursor.execute(
                            '''
                            CREATE TABLE IF NOT EXISTS stocks (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                symbol TEXT,
                                avg_price REAL,
                                cumulative_quantity REAL,
                                current_timestamp REAL
                            )
                            '''
                        )

                        # count average price
                        self.avg_price = self.cumulative_price / self.cumulative_count

                        # convert avg_price to integer for better output formatting
                        avg_price_str = int(self.avg_price)

                        # get current timestamp
                        now = datetime.now()
                        current_timestamp = now.timestamp()
                        current_timestamp_str = now.strftime('%Y-%m-%d %H:%M:%S')

                        # print message
                        print(
                            f'[INFO] '
                            f'{self.cumulative_count} messages | current_timestamp: {current_timestamp_str} | '
                            f'avg_price: {cumulative_price_str}/{self.cumulative_count} -> '
                            f'{self.avg_price} | '
                            f'cumulative_quantity: {cumulative_quantity_str}'
                        )

                        # Insert a row of data (PEP 249 compliant)
                        cursor.execute(
                            '''
                            INSERT INTO stocks (
                                symbol,
                                avg_price,
                                cumulative_quantity,
                                current_timestamp
                            )
                            VALUES (?, ?, ?, ?)
                            ''',
                            (
                                symbol,
                                self.avg_price,
                                self.cumulative_quantity,
                                current_timestamp,
                            ),
                        )

                        # commit the changes
                        db_conn.commit()

                        # fetch the last inserted row
                        last_row_id = (cursor.lastrowid,)
                        cursor.execute('SELECT * FROM stocks WHERE id = ?', last_row_id)
                        last_row = cursor.fetchone()

                        # print the last inserted row
                        print(f'[INFO] Database row inserted successfully: {last_row}')

                        # run strategy
                        self.get_strategy.run(
                            cursor=cursor # Sqlite3 cursor required
                        )

                        # close the database connection
                        cursor.close()

                        # reset the cumulative values for next loop
                        self.cumulative_count = 0
                        self.cumulative_time = 0.0
                        self.cumulative_price = 0.0
                        self.cumulative_quantity = 0.0

            except KeyboardInterrupt:
                print('Interrupted by user')

    def _create_db_conn(self) -> sqlite3.Connection:
        """create a Connection object.

        Returns:
            sqlite3.Connection: A connection object to the SQLite database.

        Raises:
            No need to raise here, because the validation has already been processed.
        """
        return sqlite3.connect(
            self.DATABASE_FILE_NAME
        )
