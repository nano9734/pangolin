# SPDX-License-Identifier: GPL-2.0-or-later

"""Main entry point for running Pangolin.

Execution:
1. Load and validate config.

Notes:
- Use `python3 -m pangolin` to run Pangolin.
- Use Ctrl+C to terminate safely.
"""

from .constants import *
from pangolin import Config
from pangolin import UrlFactory
from pangolin import Client
from pangolin import Manager

# Define main function
def main():
    config = Config(
        config_file_name=FileNames.CONFIG,
        allow_missing=False
    )

    print(HeaderMessages.CONFIG_HEADER + "\n")

    loaded_config = config.load()

    url_factory = UrlFactory()

    # Binance futures URLs constructed at runtime
    binance_futures_created_urls = []
    binance_futures_assembled_urls = []

    # Active configuration values
    active_symbol = None
    active_api_key = None
    active_secret_key = None

    # Binance Futures hosts
    binance_futures_stream_host = None
    binance_futures_api_host = None

    if binance_enabled(loaded_config):
         # Enabled exchange identifier
        enabled_exchange_name = ExchangesNames.BINANCE.capitalize()

        # WebSocket stream uses mainnet only (no testnet available)
        binance_futures_stream_host = BinanceHosts.FUTURES_STREAM

        if loaded_config["Binance"]["is_testnet"] == "yes":
            binance_futures_api_host = BinanceHosts.TESTNET_FUTURES_API
        elif loaded_config["Binance"]["is_testnet"] == "no":
            binance_futures_api_host = BinanceHosts.FUTURES_API
        else:
            raise ValueError('Invalid is_testnet value: loaded_config["Binance"]["is_testnet"]')

        # Binance Futures API endpoint
        # https://fapi.binance.com/fapi/v1/ticker/price
        # Use a valid ticker symbol such as "BTCUSDT", which can be verified via this endpoint.
        active_ticker = loaded_config["Binance"]["supported_coin"].lower() + "usdt"
        active_symbol = active_ticker.upper()

        print("\n" + "*** Ready URLs ***")

        binance_futures_wss_url = url_factory.create_binance_futures_wss_url(
            host=BinanceHosts.FUTURES_STREAM,
            ticker=active_ticker
        )

        binance_futures_price_url = url_factory.create_binance_futures_price_url(
            host=binance_futures_api_host,
            symbol=active_symbol
        )

        binance_futures_exchange_info_url = url_factory.create_binance_futures_exchange_info_url(
            host=binance_futures_api_host,
            symbol=active_symbol
        )

        if loaded_config["Binance"]["is_testnet"] == "yes":
            binance_futures_time_url = BinanceUrls.TESTNET_FUTURES_TIME
            binance_futures_order_url= BinanceUrls.TESTNET_FUTURES_ORDER
        elif loaded_config["Binance"]["is_testnet"] == "no":
            binance_futures_time_url = BinanceUrls.FUTURES_TIME
            binance_futures_order_url = BinanceUrls.FUTURES_ORDER
        else:
            raise ValueError('Invalid is_testnet value: loaded_config["Binance"]["is_testnet"]')

        print(f"[MAIN] Rest API URL ({binance_futures_time_url}) has been created.")
        print(f"[MAIN] Rest API URL ({binance_futures_order_url}) has been created.")

        binance_futures_created_urls = []
        binance_futures_assembled_urls = []

        for binance_futures_assembled_url in [binance_futures_wss_url, binance_futures_price_url, binance_futures_exchange_info_url]:
            binance_futures_assembled_urls.append(binance_futures_assembled_url)

        for binance_futures_created_url in [binance_futures_time_url, binance_futures_order_url]:
            binance_futures_created_urls.append(binance_futures_created_url)

        if loaded_config["Binance"]["is_testnet"] == "yes":
            active_api_key = loaded_config["Binance"]["test_api_key"]
            active_api_secret = loaded_config["Binance"]["test_api_secret"]
        elif loaded_config["Binance"]["is_testnet"] == "no":
            active_api_key = loaded_config["Binance"]["api_key"]
            active_api_secret = loaded_config["Binance"]["api_secret"]

        tumbling_window_seconds = loaded_config["Binance"]["tumbling_window_seconds"]
        max_display_loop_count = loaded_config["Binance"]["max_display_loop_count"]
        max_total_loop_count = loaded_config["Binance"]["max_total_loop_count"]

    assembled_urls = []
    created_urls = []

    if binance_futures_assembled_urls:
        assembled_urls = binance_futures_assembled_urls

    if binance_futures_created_urls:
        created_urls = binance_futures_created_urls

    combined_urls = assembled_urls + created_urls

    client = Client(
        combined_urls=combined_urls,
        active_symbol=active_symbol,
        active_api_key=active_api_key,
        active_api_secret=active_api_secret,
        response_file_path=ProjectPaths.RESPONSE
    )

    manager = Manager(
        client=client,
        combined_urls=combined_urls,
        tumbling_window_seconds=tumbling_window_seconds,
        max_display_loop_count=max_display_loop_count,
        max_total_loop_count=max_total_loop_count,
        strategy_folder_path=ProjectPaths.STRATEGY,
        response_file_path=ProjectPaths.RESPONSE
    )

    print(HeaderMessages.MANAGER_HEADER)

    if manager.response_file_exists:
        raise FileExistsError(f"[ERROR] Response file already exists: {manager.response_file_path}")

    if binance_enabled(loaded_config):
        print(f'[INFO] Manager started for exchange "{enabled_exchange_name}"')
        manager.run_binance_stream()

def binance_enabled(loaded_config):
    if loaded_config["Binance"]["is_enabled"] == "yes":
        return True
    elif loaded_config["Binance"]["is_enabled"] == "no":
        return False
    else:
        raise ValueError('Invalid value for Binance.is_enabled; expected "yes" or "no".')

if __name__ == '__main__':
    main()
