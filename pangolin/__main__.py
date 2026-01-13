# SPDX-License-Identifier: GPL-2.0-or-later
"""Main entry point for running Pangolin.

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

@dataclass(frozen=True)
class FileNames:
    ORDER_PLACE = "order_place" + FileExtensions.JSON
    RESPONSE = "response" + FileExtensions.JSON
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
    RESPONSE = os.path.join(Project.NAME, DirectoryNames.DATA, FileNames.RESPONSE)
    SQL = os.path.join(Project.NAME, DirectoryNames.SQL) + os.sep

@dataclass(frozen=True)
class ExchangesNames:
    BINANCE = "binance"

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
    def create_binance_wss_url(enabled_exchange_name:str, net_loc: str, ticker: str) -> str:
        wss_url = 'wss://' + net_loc + '/ws/' + ticker + '@aggTrade'
        print(f'[UrlFactory] WebSocket URL ({wss_url}) has been assembled.')
        print() # add a line break for console readability
        return wss_url

def main():
    config = Config(config_file_name=FileNames.CONFIG)
    config.print_message(Messages.CONFIG_HEADER)
    loaded_exchange_config = config.load(allow_missing=False)
    file_check = FileCheck()

    if binance_enabled(loaded_exchange_config=loaded_exchange_config):
        # Set the enabled exchange
        enabled_exchange_name = ExchangesNames.BINANCE

        # Retrieve Binance configuration
        binance_config = loaded_exchange_config[enabled_exchange_name.capitalize()]

        # Extract the network location (net_loc) from the URL
        # The term "net_loc" was used in RFC 1808 but is now deprecated
        # Reference: https://datatracker.ietf.org/doc
        net_loc = urlparse(Binance.FUTURES_WSS_URL).netloc

        # Binance API endpoint: https://fapi.binance.com/fapi/v1/ticker/price
        # The ticker symbol, such as "btcusdt", can be verified at this endpoint
        ticker = binance_config['supported_coin'].lower() + 'usdt'

        # Create the Binance WebSocket URL
        wss_url = UrlFactory.create_binance_wss_url(enabled_exchange_name=enabled_exchange_name, net_loc=net_loc, ticker=ticker)

    client = ClientFactory.create_client(
        enabled_exchange_name=enabled_exchange_name,
        config=binance_config,
        order_place_file_path=ProjectPaths.ORDER_PLACE,
        response_file_path=ProjectPaths.RESPONSE
    )

    client.print_message(Messages.CLIENT_HEADER)

    #client.place_order(symbol='BTCUSDT', side='SELL', trade_type='MARKET', quantity=0.02)

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
        strategy_folder_path=ProjectPaths.STRATEGY,
        response_file_path=ProjectPaths.RESPONSE
    )

    if not file_check.order_place_file_exists and not file_check.response_file_exists:
        manager.run()

        if file_check.order_place_file_exists and file_check.response_file_exists:
            schedule.every(10).seconds.do(job)
            while True:
                schedule.run_pending()
                time.sleep(1)
    else:
        raise FileExistsError(f'[ERROR] The file(s) "{ProjectPaths.ORDER_PLACE}" or "{ProjectPaths.RESPONSE}" already existed at the start.')

def job():
    print("test job")

def binance_enabled(loaded_exchange_config):
    return loaded_exchange_config['Binance'].getboolean('is_enabled')

class FileCheck:
    @property
    def order_place_file_exists(self) -> bool:
        return os.path.exists(ProjectPaths.ORDER_PLACE)

    @property
    def response_file_exists(self) -> bool:
        return os.path.exists(ProjectPaths.RESPONSE)

if __name__ == '__main__':
    main()
