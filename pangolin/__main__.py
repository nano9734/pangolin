# SPDX-License-Identifier: GPL-2.0-or-later
"""Main entry point for Pangolin.

Execution:
1. Load and validate config.

Notes:
- Use Ctrl+C to terminate safely.
"""

import os
import time
import schedule
from urllib.parse import urlparse
from dataclasses import dataclass
from pangolin import Config
from pangolin import Client
from pangolin import BinanceClient
from pangolin import ClientFactory
from pangolin import Database
from pangolin import Manager

@dataclass(frozen=True)
class FileExtensions:
    JSON = ".json"
    INI = ".ini"
    DATABASE = ".db"

@dataclass(frozen=True)
class Project:
    NAME = "pangolin"
    NAME_CAP = NAME.capitalize()

@dataclass(frozen=True)
class FileNames:
    ORDER_PLACE = "order_place" + FileExtensions.JSON
    CONFIG = Project.NAME + FileExtensions.INI
    DATABASE = Project.NAME + FileExtensions.DATABASE

@dataclass(frozen=True)
class DirectoryNames:
    DATA = "data"
    STRATEGY = "strategies"
    SQL = "sql"

@dataclass(frozen=True)
class ProjectPaths:
    STRATEGY = os.path.join(Project.NAME, DirectoryNames.STRATEGY)
    ORDER_PLACE = os.path.join(Project.NAME, DirectoryNames.DATA, FileNames.ORDER_PLACE)
    SQL = os.path.join(Project.NAME, DirectoryNames.SQL) + os.sep

@dataclass(frozen=True)
class ExchangesNames:
    BINANCE = "binance"
    BINANCE_CAP = BINANCE.capitalize()

@dataclass(frozen=True)
class ClassNames:
    CONFIG = "Config"
    CLIENT = "Client"
    DATABASE = "Database"
    MANAGER = "Manager"

@dataclass(frozen=True)
class Messages:
    LEFT_SEPARATOR = "*** "
    RIGHT_SEPARATOR = " ***"
    CONFIG_HEADER = LEFT_SEPARATOR + ClassNames.CONFIG + RIGHT_SEPARATOR
    CLIENT_HEADER = LEFT_SEPARATOR + ClassNames.CLIENT + RIGHT_SEPARATOR
    DATABASE_HEADER = LEFT_SEPARATOR + ClassNames.DATABASE + RIGHT_SEPARATOR
    MANAGER_HEADER = LEFT_SEPARATOR + ClassNames.MANAGER + RIGHT_SEPARATOR

@dataclass(frozen=True)
class DatabaseTable:
    NAME = "stocks"

@dataclass(frozen=True)
class Binance:
    FUTURES_WSS_URL = "wss://fstream.binance.com"

class UrlFactory:
    @staticmethod
    def create_binance_wss_url(enabled_exchange_name:str, netloc: str, ticker: str) -> str:
        wss_url = 'wss://' + netloc + '/ws/' + ticker + '@aggTrade'
        print(f'[UrlFactory] WebSocket URL ({wss_url}) has been assembled.')
        print() # add a line break for console readability
        return wss_url

def main():
    print(Messages.CONFIG_HEADER)
    config = Config(config_file_name=FileNames.CONFIG)
    loaded_exchange_config = config.load(allow_missing=False)
    if binance_enabled(loaded_exchange_config=loaded_exchange_config):
        enabled_exchange_name = ExchangesNames.BINANCE
        enabled_exchange_name_capitalized = ExchangesNames.BINANCE_CAP
        binance_config = loaded_exchange_config[enabled_exchange_name_capitalized]
        netloc = urlparse(Binance.FUTURES_WSS_URL).netloc
        ticker = binance_config['supported_coin'].lower() + 'usdt'
        wss_url = UrlFactory.create_binance_wss_url(enabled_exchange_name=enabled_exchange_name, netloc=netloc, ticker=ticker)

    print(Messages.CLIENT_HEADER)
    client = ClientFactory.create_client(
        enabled_exchange_name=enabled_exchange_name,
        config=binance_config
    )
    client.place_order()

    print() # add a line break for console readability

    print(Messages.DATABASE_HEADER)
    database = Database(
        sql_path = ProjectPaths.SQL,
        enabled_exchange_name=enabled_exchange_name,
        database_file_name=FileNames.DATABASE,
        database_table_name=DatabaseTable.NAME
    )

    if database.database_file_exists:
        database.delete_database_file()

    database.connect()
    database.create_table()
    print() # add a line break for console readability

    print(Messages.MANAGER_HEADER)
    manager = Manager(
        enabled_exchange_name=enabled_exchange_name,
        loaded_exchange_config=loaded_exchange_config,
        wss_url=wss_url,
        database=database,
        order_place_file_path=ProjectPaths.ORDER_PLACE,
        strategy_folder_path=ProjectPaths.STRATEGY
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
    return os.path.exists(ProjectPaths.ORDER_PLACE)

def binance_enabled(loaded_exchange_config):
    return loaded_exchange_config['Binance'].getboolean('is_enabled')

if __name__ == '__main__':
    main()
