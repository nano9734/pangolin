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

import os
import sqlite3

class Database:
    STOCKS_BINANCE_TABLE_SCHEMA = """
    CREATE TABLE IF NOT EXISTS stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        avg_price REAL,
        cumulative_quantity REAL,
        current_timestamp TIMESTAMP
    )
    """

    STOCKS_BINANCE_INSERT_QUERY = """
    INSERT INTO stocks (
        symbol,
        avg_price,
        cumulative_quantity,
        current_timestamp
    ) VALUES (?, ?, ?, ?)
    """

    def __init__(self, enabled_exchange_name: str, database_file_name: str):
        self.EXCHANGE_NAME = enabled_exchange_name
        self.DATABASE_FILE_NAME = database_file_name
        self.DATABASE_TABLE_NAME = 'stocks'
        self.DATABASE_EXISTS_MSG             = f'[INFO] Database file ({self.DATABASE_FILE_NAME}) exists. It will be deleted by the algorithm.'
        self.DATABASE_NOT_EXISTS_MSG         = f'[INFO] Database file ({self.DATABASE_FILE_NAME}) does not exist, nothing to delete.'
        self.DATABASE_DELETED_MSg            = f'[INFO] Database file ({self.DATABASE_FILE_NAME}) has been deleted.'
        self.DATABASE_CONNECTION_SUCCESS_MSG = f'[INFO] Connected to database file ({self.DATABASE_FILE_NAME})'
        self.TABLE_CREATED_MSG               = f"[INFO] Table '{self.DATABASE_TABLE_NAME}' has been created."
        self.STOCKS_ROWS_DELETED_MSG         = f'[INFO] All rows in the stocks table have been deleted.'
        self.COMMIT_SUCCESS_MSG              = f'[INFO] Database changes have been committed.'
        print('*** Database ***')

        if self.database_exists():
            print(self.DATABASE_EXISTS_MSG)
            self.delete_file(verbose=True)
            self.connect()
            self.create_table()
            print(self.TABLE_CREATED_MSG)
            self.conn.commit()
            print(self.COMMIT_SUCCESS_MSG)
        else:
            print(self.DATABASE_NOT_EXISTS_MSG)
        print() # Add a line break for console readability

    def database_exists(self) -> bool:
        return os.path.exists(self.DATABASE_FILE_NAME)

    def delete_file(self, verbose: bool = False) -> None:
        if os.path.exists(self.DATABASE_FILE_NAME):
            os.remove(self.DATABASE_FILE_NAME)
            if verbose:
                print(self.DATABASE_DELETED_MSG)

    def create_table(self) -> None:
        if self.EXCHANGE_NAME == 'binance':
            self.cursor.execute(self.STOCKS_BINANCE_TABLE_SCHEMA)

    def insert_row(self, symbol: str, avg_price: float, cumulative_quantity: float, current_timestamp: float) -> None:
        if self.EXCHANGE_NAME == 'binance':
            required_values = (symbol, avg_price, cumulative_quantity, current_timestamp)
            self.cursor.execute(self.STOCKS_BINANCE_INSERT_QUERY, required_values)
            self.conn.commit()
            print(self.COMMIT_SUCCESS_MSG)

    def clear_table(self) -> None:
        self.cursor.execute('DELETE FROM ' + self.DATABASE_TABLE_NAME)
        print(self.STOCKS_ROWS_DELETED_MSG)
        self.conn.commit()
        print(self.COMMIT_SUCCESS_MSG)

    def connect(self):
        self.conn = sqlite3.connect(self.DATABASE_FILE_NAME)
        self.cursor = self.conn.cursor()
        print(self.DATABASE_CONNECTION_SUCCESS_MSG)

    def close(self):
        self.conn.close()
