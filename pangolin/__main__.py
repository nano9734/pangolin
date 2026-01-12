# SPDX-License-Identifier: GPL-2.0-or-later
"""Main entry point for Pangolin.

Execution:
1. Load and validate config.

Notes:
- Use Ctrl+C to terminate safely.
"""

import os
from urllib.parse import urlparse

import schedule
import time

from pangolin import Config
from pangolin import Database
from pangolin import Manager

PROJECT_NAME = "pangolin"
PROJECT_NAME_CAP = PROJECT_NAME.capitalize()
DATA_FOLDER_NAME = "data"
SQL_FOLDER_NAME = "sql"
ORDER_PLACE_FILE_NAME = "order_place.json"
ORDER_PLACE_FILE_PATH = os.path.join(PROJECT_NAME, DATA_FOLDER_NAME, ORDER_PLACE_FILE_NAME)
CONFIG_FILE_NAME = "pangolin.ini"
DATABASE_FILE_NAME = "pangolin.db"
DATABASE_TABLE_NAME = "stocks"
BINANCE_EXCHANGE_NAME = "binance"
BINANCE_EXCHANGE_NAME_CAP = BINANCE_EXCHANGE_NAME.capitalize()
SEPARATOR = "***"
CONFIG_SECTION_HEADER_NAME = f'{SEPARATOR} Config {SEPARATOR}'
DATABASE_SECTION_HEADER_NAME = f'{SEPARATOR} Database {SEPARATOR}'
MANAGER_SECTION_HEADER_NAME = f'{SEPARATOR} Manager {SEPARATOR}'

class UrlFactory:
    CREATE_WSS_URL_SUCCESS_MSG = '[UrlFactory] WebSocket URL ({}) has been assembled.'

    def create_binance_wss_url(self, enabled_exchange_name:str, netloc: str, ticker: str) -> str:
        wss_url = 'wss://' + netloc + '/ws/' + ticker + '@aggTrade'
        print(self.CREATE_WSS_URL_SUCCESS_MSG.format(wss_url))
        return wss_url

def main():
    config = Config(config_file_name=CONFIG_FILE_NAME, config_section_header_name=CONFIG_SECTION_HEADER_NAME)
    loaded_exchange_config = config.load(allow_missing=False)

    if is_binance_enabled(loaded_exchange_config=loaded_exchange_config):
        enabled_exchange_name = BINANCE_EXCHANGE_NAME
        enabled_exchange_name_capitalized = BINANCE_EXCHANGE_NAME_CAP
        netloc = urlparse(loaded_exchange_config[enabled_exchange_name_capitalized]['wss_url']).netloc
        ticker = loaded_exchange_config[enabled_exchange_name_capitalized]['supported_coin'].lower() + 'usdt'
        wss_url = UrlFactory().create_binance_wss_url(enabled_exchange_name=enabled_exchange_name, netloc=netloc, ticker=ticker)
        print() # add a line break for console readability

    print(DATABASE_SECTION_HEADER_NAME)
    database = Database(
        project_name=PROJECT_NAME,
        sql_folder_name=SQL_FOLDER_NAME,
        enabled_exchange_name=enabled_exchange_name,
        database_file_name=DATABASE_FILE_NAME,
        database_table_name=DATABASE_TABLE_NAME
    )

    if database.database_file_exists:
        database.delete_database_file()

    database.connect()
    database.create_table()
    print() # add a line break for console readability

    print(MANAGER_SECTION_HEADER_NAME)
    manager = Manager(
        enabled_exchange_name=enabled_exchange_name,
        loaded_exchange_config=loaded_exchange_config,
        wss_url=wss_url,
        database=database,
        order_place_file_path=ORDER_PLACE_FILE_PATH
    )

    if not order_place_file_exists():
        manager.run()

        if order_place_file_exists():
            schedule.every(10).seconds.do(job)
            while True:
                schedule.run_pending()
                time.sleep(1)
    else:
        raise FileExistsError(f"The file ({ORDER_PLACE_FILE_PATH})already existed at the start")

def job():
    print("test job")

def order_place_file_exists() -> bool:
    return os.path.exists(ORDER_PLACE_FILE_PATH)

def is_binance_enabled(loaded_exchange_config):
    return loaded_exchange_config['Binance'].getboolean('is_enabled')

if __name__ == '__main__':
    main()
