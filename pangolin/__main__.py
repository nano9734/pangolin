# SPDX-License-Identifier: GPL-2.0-or-later

"""Main entry point for running Pangolin.

Execution:
1. Load and validate config.

Notes:
- Use Ctrl+C to terminate safely.
"""

from pathlib import Path

from pangolin import Config
from pangolin import UrlFactory
from pangolin import Client
from pangolin import Manager

class Project:
    NAME = "pangolin"

class FileExtensions:
    INI = ".ini"
    JSON = ".json"

class FileNames:
    CONFIG = Project.NAME + FileExtensions.INI
    ORDER_PLACE = "order_place" + FileExtensions.JSON
    RESPONSE = "response" + FileExtensions.JSON

class DirectoryNames:
    DATA = "data"
    STRATEGY = "strategies"

class ProjectPaths:
    ORDER_PLACE = Path(Project.NAME) / DirectoryNames.DATA / FileNames.ORDER_PLACE
    RESPONSE = Path(Project.NAME) / DirectoryNames.DATA / FileNames.RESPONSE
    STRATEGY = Path(Project.NAME) / DirectoryNames.STRATEGY

class ExchangesNames:
    BINANCE = "binance"

class ClassNames:
    CLIENT = "Client"
    CONFIG = "Config"
    MANAGER = "Manager"
    FACTORY = "UrlFactory"

class HeaderMessages:
    LEFT_SEPARATOR = "*** "
    RIGHT_SEPARATOR = " ***"
    CLIENT_HEADER = LEFT_SEPARATOR + ClassNames.CLIENT + RIGHT_SEPARATOR
    CONFIG_HEADER = LEFT_SEPARATOR + ClassNames.CONFIG + RIGHT_SEPARATOR
    MANAGER_HEADER = LEFT_SEPARATOR + ClassNames.MANAGER + RIGHT_SEPARATOR
    FACTORY_HEADER = LEFT_SEPARATOR + ClassNames.FACTORY + RIGHT_SEPARATOR

class BinanceHosts:
    FUTURES_WSS = "fstream.binance.com"
    FUTURES_REST_API = "fapi.binance.com"
    TEST_FUTURES_ORDER_URL = "testnet.binancefuture.com"

class BinanceUrls:
    TESTNET_FUTURES_TIME = "https://testnet.binancefuture.com/fapi/v1/time"

# Define main function
def main():
    config = Config(
        config_file_name=FileNames.CONFIG,
        allow_missing=False
    )

    config.display_message(message=HeaderMessages.CONFIG_HEADER)
    loaded_config = config.load()

    url_factory = UrlFactory()

    # Initialize Binance-related variables here so they can be referenced outside of conditional blocks
    binance_futures_client_url = None
    binance_futures_urls = []

    # Initialize client values
    client_symbol = None
    client_url = None
    client_api_key = None
    client_secret_key = None

    if loaded_config["Binance"]["is_enabled"] == "yes":
        # Set the enabled exchange
        enabled_exchange_name = ExchangesNames.BINANCE.capitalize()

        # BinancE API endpoint: https://fapi.binance.com/fapi/v1/ticker/price
        # The ticker symbol, such as "btcusdt", can be verified at this endpoint.
        ticker = loaded_config["Binance"]['supported_coin'].lower() + 'usdt'
        symbol = ticker.upper()
        client_symbol = symbol

        url_factory.display_message(message=HeaderMessages.FACTORY_HEADER)

        # Create the Binance URLs
        binance_futures_wss_url = url_factory.create_binance_futures_wss_url(host=BinanceHosts.FUTURES_WSS, ticker=ticker)
        binance_futures_price_url = url_factory.create_binance_futures_price_url(host=BinanceHosts.FUTURES_REST_API, symbol=symbol)
        binance_futures_exchange_info_url = url_factory.create_binance_futures_exchange_info_url(host=BinanceHosts.FUTURES_REST_API, symbol=symbol)

        if loaded_config["Binance"]["is_testnet"] == "yes":
            binance_futures_time_url = BinanceUrls.TESTNET_FUTURES_TIME

        # Append Binance future URLs
        for binance_futures_url in [
            binance_futures_wss_url,
            binance_futures_price_url,
            binance_futures_exchange_info_url,
            binance_futures_time_url
        ]:
            binance_futures_urls.append(binance_futures_url)

        # Binance API keys
        if loaded_config["Binance"]["is_testnet"] == "yes":
            client_api_key = loaded_config["Binance"]["test_api_key"]
            client_api_secret = loaded_config["Binance"]["test_api_secret"]
        elif loaded_config["Binance"]["is_testnet"] == "no":
            client_api_key = loaded_config["Binance"]["api_key"]
            client_api_secret = loaded_config["Binance"]["api_secret"]

        # Overwrite config
        if loaded_config["Binance"]["is_testnet"] == "yes":
            binance_futures_client_url = BinanceHosts.TEST_FUTURES_ORDER_URL

        tumbling_window_seconds = loaded_config["Binance"]["tumbling_window_seconds"]
        max_display_loop_count = loaded_config["Binance"]["max_display_loop_count"]
        max_total_loop_count = loaded_config["Binance"]["max_total_loop_count"]

    # Initialize outside if statement for safe reference later
    assembled_urls = []

    if binance_futures_urls:
        assembled_urls = binance_futures_urls

    client = Client(
        client_symbol=client_symbol,
        assembled_urls=assembled_urls,
        client_api_key=client_api_key,
        client_api_secret=client_api_secret,
        order_place_file_path=ProjectPaths.ORDER_PLACE,
        response_file_path=ProjectPaths.RESPONSE
    )

    manager = Manager(
        client = client,
        strategy_folder_path=ProjectPaths.STRATEGY,
        order_place_file_path=ProjectPaths.ORDER_PLACE,
        response_file_path=ProjectPaths.RESPONSE,
        assembled_urls=assembled_urls,
        tumbling_window_seconds=tumbling_window_seconds,
        max_display_loop_count=max_display_loop_count,
        max_total_loop_count=max_total_loop_count
    )

    manager.display_message(message=HeaderMessages.MANAGER_HEADER, use_new_line=True)
    manager.check_file_conflicts()

    if loaded_config["Binance"]["is_enabled"] == "yes" and len(binance_futures_urls) == 4:
        print(f'[INFO] Manager started for exchange "{enabled_exchange_name}"')
        manager.run_binance_stream()

if __name__ == '__main__':
    main()
