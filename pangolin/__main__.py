from pangolin import constants
from pangolin import Config
from pangolin import UrlFactory
from pangolin import Client
from pangolin import Manager
from pathlib import Path
import time

def main():
    print("*** CONFIG ***" + "\n")

    loaded_config = Config(config_file_name=constants.FileNames.CONFIG, allow_missing=False).loads()

    dynamic_urls: list[str] = []
    static_urls: list[str] = []

    if is_binance_enabled(loaded_config):
        active_exchange_name = "Binance"

        if is_binance_testnet(loaded_config):
            binance_futures_api_host = constants.Hosts.BINANCE_TESTNET_FUTURES_API
        else:
            binance_futures_api_host = constants.Hosts.BINANCE_FUTURES_API

        active_ticker = get_config_value(loaded_config, active_exchange_name, key_name="supported_coin").lower() + "usdt"
        active_symbol = get_config_value(loaded_config, active_exchange_name, key_name="supported_coin").upper() + "USDT"

        print("\n" + "=== Ready URLs ===")

        binance_futures_wss_url = UrlFactory().create_binance_futures_wss_url(host=constants.Hosts.BINANCE_FUTURES_STREAM, ticker=active_ticker)
        binance_futures_price_url = UrlFactory().create_binance_futures_price_url(host=binance_futures_api_host, symbol=active_symbol)
        binance_futures_exchange_info_url = UrlFactory().create_binance_futures_exchange_info_url(host=binance_futures_api_host, symbol=active_symbol)

        dynamic_urls.extend([binance_futures_wss_url, binance_futures_price_url, binance_futures_exchange_info_url])

        if is_binance_testnet(loaded_config):
            binance_futures_time_url = constants.Urls.BINANCE_TESTNET_FUTURES_TIME
            binance_futures_order_url= constants.Urls.BINANCE_TESTNET_FUTURES_ORDER
        else:
            binance_futures_time_url = constants.Urls.BINANCE_FUTURES_TIME
            binance_futures_order_url = constants.Urls.BINANCE_FUTURES_ORDER

        static_urls.extend([binance_futures_time_url, binance_futures_order_url])

        active_urls = dynamic_urls + static_urls

        print(f"[MAIN] Rest API URL ({binance_futures_time_url}) has been created.")
        print(f"[MAIN] Rest API URL ({binance_futures_order_url}) has been created.\n")

        if is_binance_testnet(loaded_config):
            active_api_key = get_api_key(loaded_config, active_exchange_name, is_testnet=True)
            active_api_secret = get_api_secret(loaded_config, active_exchange_name, is_testnet=True)
        else:
            active_api_key = get_api_key(loaded_config, active_exchange_name, is_testnet=False)
            active_api_secret = get_api_secret(loaded_config, active_exchange_name, is_testnet=False)

    client = Client(
        active_urls=active_urls,
        active_symbol=active_symbol,
        active_api_key=active_api_key,
        active_api_secret=active_api_secret,
    )

    manager = Manager(
        client=client,
        active_urls=active_urls,
        tumbling_window_seconds=get_config_value(loaded_config, active_exchange_name, key_name="tumbling_window_seconds"),
        max_total_loop_count=get_config_value(loaded_config, active_exchange_name, key_name="max_total_loop_count"),
        max_display_loop_count=get_config_value(loaded_config, active_exchange_name, key_name="max_display_loop_count"),
        connect_timeout_sec=get_config_value(loaded_config, active_exchange_name, key_name="connect_timeout_sec"),
        recv_timeout_sec=get_config_value(loaded_config, active_exchange_name, key_name="recv_timeout_sec"),
        max_retry_wait_sec=get_config_value(loaded_config, active_exchange_name, key_name="max_retry_wait_sec"),
    )

    print("*** MANAGER ***")

    if manager.response_file_exists:
        raise FileExistsError(f"[ERROR] Response file already exists: {manager.response_file_path}")

    if is_binance_enabled(loaded_config):
        manager.run_binance_stream()
        while Path(Paths.RESPONSE).is_file():
            binance_futures_order_status = client.get_binance_futures_order_status()
            if binance_futures_order_status == "FILLED":
                side = client.get_order_side()
            elif binance_futures_order_status == "NEW":
                continue
            elif binance_futures_order_status == "PARTIALLY_FILLED":
               continue

        """
        file_path = ProjectPaths.RESPONSE
        else:
            client.place_binance_take_profit_order()
            client.place_binance_stop_loss_order()
        """

def is_binance_enabled(loaded_config) -> bool:
    if loaded_config["Binance"]["is_enabled"] == "yes":
        return True
    elif loaded_config["Binance"]["is_enabled"] == "no":
        return False
    else:
        raise ValueError('[ERROR] Invalid value for Binance.is_enabled; expected "yes" or "no".')

def is_binance_testnet(loaded_config) -> bool:
    if loaded_config["Binance"]["is_testnet"] == "yes":
        return True
    elif loaded_config["Binance"]["is_testnet"] == "no":
        return False
    else:
        raise ValueError('[ERROR] Invalid value for Binance.is_testnet; expected "yes" or "no".')

def get_api_key(loaded_config, active_exchange_name, is_testnet:bool) -> str:
    if active_exchange_name == "Binance":
        if is_testnet == True:
            active_api_key = loaded_config["Binance"]["test_api_key"]
        elif is_testnet == False:
            active_api_key = loaded_config["Binance"]["api_key"]

    return active_api_key

def get_api_secret(loaded_config, active_exchange_name, is_testnet:bool) -> str:
    if active_exchange_name == "Binance":
        if is_testnet == True:
            active_api_secret = loaded_config["Binance"]["test_api_secret"]
        elif is_testnet == False:
            active_api_secret = loaded_config["Binance"]["api_secret"]

    return active_api_secret

def get_config_value(loaded_config, active_exchange_name, key_name:str) -> str:
    config_value = loaded_config[active_exchange_name][key_name]
    return config_value

if __name__ == '__main__':
    main()
