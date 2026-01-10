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
    DATABASE_FILE_NAME = 'pangolin.db'
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
    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name
        print('*** Database ***')
        if self.database_exists():
            print(f'Database exists: {self.DATABASE_FILE_NAME}')
            self.delete_file(verbose=True)

            self.conn = sqlite3.connect(self.DATABASE_FILE_NAME)
            self.cursor = self.conn.cursor()
            self.create_table()
            self.conn.commit()
            # Add a line break for console readability
            print()

    def database_exists(self) -> bool:
        return os.path.exists(self.DATABASE_FILE_NAME)

    def delete_file(self, verbose: bool = False) -> None:
        if os.path.exists(self.DATABASE_FILE_NAME):
            os.remove(self.DATABASE_FILE_NAME)
            if verbose:
                print(f"Database file '{self.DATABASE_FILE_NAME}' has been deleted.")
        else:
            if verbose:
                print(f"Database file '{self.DATABASE_FILE_NAME}' does not exist, nothing to delete.")

    def create_table(self) -> None:
        if self.exchange_name == 'binance':
            self.cursor.execute(self.STOCKS_BINANCE_TABLE_SCHEMA)

    def insert_row(self, symbol: str, avg_price: float, cumulative_quantity: float, current_timestamp: float) -> None:
        if self.exchange_name == 'binance':
            required_values = (symbol, avg_price, cumulative_quantity, current_timestamp)
            self.cursor.execute(self.STOCKS_BINANCE_INSERT_QUERY, required_values)
            self.conn.commit()

    def clear_table(self) -> None:
        self.cursor.execute("DELETE FROM stocks")
        self.conn.commit()
        print("[INFO] All rows in the stocks table have been deleted.")

    def open(self):
        self.conn = sqlite3.connect("pangolin.db")
        self.cursor = self.conn.cursor()

    def close(self):
        print('database is closed')
        self.conn.close()
