# SPDX-License-Identifier: GPL-2.0-or-later

import os
import sqlite3
from datetime import datetime
from dataclasses import dataclass

@dataclass(frozen=True)
class SqlFileNames:
    CREATE_BINANCE_TABLE = "create_binance_table.sql"
    INSERT_BINANCE_QUERY = "insert_binance_query.sql"

class Database:
    DATABASE_DELETED_MESSAGE = "[INFO] Database file ({}) has been deleted."
    DATABASE_CONNECTION_SUCCESS_MESSAGE = "[INFO] Connected to database file ({})."
    TABLE_CREATED_MESSAGE = '[INFO] Table "{}" has been created.'
    COMMIT_SUCCESS_MESSAGE = "[INFO] Database changes have been committed."
    CLOSE_CONNECTION_MESSAGE = "[INFO] Database connection has been closed."

    def __init__(self, sql_path:str, enabled_exchange_name:str, database_file_name: str, database_table_name: str):
        self.sql_path = sql_path
        self.enabled_exchange_name = enabled_exchange_name
        self.database_file_name = database_file_name
        self.database_table_name = database_table_name
        self.create_binance_table = self.load_sql_file(self.sql_path + SqlFileNames.CREATE_BINANCE_TABLE)
        self.insert_binance_query = self.load_sql_file(self.sql_path + SqlFileNames.INSERT_BINANCE_QUERY)
        self.table_created_message = self.TABLE_CREATED_MESSAGE.format(self.database_table_name)
        self.database_deleted_message = self.DATABASE_DELETED_MESSAGE.format(self.database_file_name)
        self.database_connection_success_message = self.DATABASE_CONNECTION_SUCCESS_MESSAGE.format(self.database_file_name)
        self.commit_success_message = self.COMMIT_SUCCESS_MESSAGE
        self.close_connection_message = self.CLOSE_CONNECTION_MESSAGE

    def connect(self) -> None:
        self.conn = sqlite3.connect(self.database_file_name)
        self.cursor = self.conn.cursor()
        print(self.database_connection_success_message)

    @property
    def database_file_exists(self) -> bool:
        return os.path.exists(self.database_file_name)

    def delete_database_file(self) -> None:
        os.remove(self.database_file_name)
        print(self.database_deleted_message)

    def create_table(self) -> None:
        if self.enabled_exchange_name == "binance":
            self.cursor.execute(self.create_binance_table)
            print(self.table_created_message)

    def save_changes(self) -> None:
        self.conn.commit()
        print(self.commit_success_message)

    def insert_row(self, symbol: str, avg_price: float, cumulative_quantity: float, current_time: float) -> None:
        required_values = (symbol, avg_price, cumulative_quantity, current_time)
        self.cursor.execute(self.insert_binance_query, required_values)

    def delete_all_stocks(self) -> None:
        self.cursor.execute('DELETE FROM ' + self.database_table_name)
        self.cursor.execute("DELETE FROM sqlite_sequence WHERE name=?", (self.database_table_name,))

    def close(self) -> None:
        self.conn.close()
        print(self.close_connection_message)

    def load_sql_file(self, file_name: str) -> str:
        with open(file_name, "r", encoding="utf-8") as sql_file:
            return sql_file.read()
