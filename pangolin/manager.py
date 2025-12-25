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
"""
this module uses strategy files to decide short/long trades.
this module connects to an SQLite3 database.
"""

# standard library to run manager
import json
import os
import sqlite3

# to get current time with timestamp
from datetime import datetime

# for better type hints...
from typing import Mapping

# short-lived WebSocket using 'with' statement
from websocket import create_connection
from contextlib import closing

# load Pangolin local module(s)
from .strategies import GetStrategy

class StreamManager:
    # database_file_path = pangolin/pangolin.db
    DATABASE_FILE_NAME = 'pangolin.db'

    def __init__(
        self,
        loaded_config: Mapping[str, str],
        wss_url: str
    ):
        """ initializes the instance for connecting websocket stream.

        Args:
            loaded_config:
            wss_url:
        """

        # create an instance of GetStrategy()
        self.get_strategy = GetStrategy()

        # create an instance of Config()
        self.loaded_config = loaded_config

        # wss_url is created from UrlFactory()
        self.wss_url = wss_url

        # initialize last_values
        self.last_trade_id = None
        self.last_timestamp_sec = None
        self.last_price = None

        # initialize cumulative_values
        self.cumulative_count: int = 0
        self.cumulative_time: float = 0.0
        self.cumulative_price: float = 0.0
        self.cumulative_quantity: float = 0.0

    def run(self):
        with closing(
            create_connection(
                self.wss_url
            )
        ) as conn:
            try:
                if os.path.exists(self.DATABASE_FILE_NAME):
                    print(f'{self.DATABASE_FILE_NAME} exists')
                    os.remove(self.DATABASE_FILE_NAME)

                    if not os.path.exists(self.DATABASE_FILE_NAME):
                        print(f'{self.DATABASE_FILE_NAME} has been deleted')

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

                    # add last price
                    if self.last_price is None:
                        self.last_price = price

                    # add price
                    self.cumulative_price += price

                    # add quantity
                    self.cumulative_quantity += quantity

                    # save last timestamp
                    self.last_timestamp_sec = timestamp_sec

                    # add cumulative_count
                    self.cumulative_count += 1

                    # test_point (real-time): cumulative_time | cumulative_count | cumulative_price | cumulative_quantity
                    print(f'{self.cumulative_time} | {self.cumulative_count} | {self.cumulative_price} | {self.cumulative_quantity}')

                    if self.cumulative_time > 10:
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
                                timestamp REAL
                            )
                            '''
                        )

                        # count average price
                        self.avg_price = self.cumulative_price / self.cumulative_count

                        # get current timestamp
                        now = datetime.now()
                        current_timestamp = now.timestamp()
                        current_timestamp_str = now.strftime('%Y-%m-%d %H:%M:%S')

                        # print messeage
                        print(f'[{self.cumulative_count}] {current_timestamp_str} | '
                              f'avg_price: {self.cumulative_price}/{self.cumulative_count} -> {self.avg_price}')

                        # insert a row of data (PEP 249 compliant)
                        cursor.execute(
                            '''
                            INSERT INTO stocks (symbol, avg_price, timestamp)
                            VALUES (?, ?, ?)
                            ''',
                            (symbol, self.avg_price, current_timestamp)
                        )

                        # commit the changes
                        db_conn.commit()

                        # fetch the last inserted row
                        last_row_id = (cursor.lastrowid,)
                        cursor.execute('SELECT * FROM stocks WHERE id = ?', last_row_id)
                        last_row = cursor.fetchone()

                        # print the last inserted row
                        print(f'  ╰─> Last inserted row: {last_row}')

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
                print("Interrupted by user")

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
