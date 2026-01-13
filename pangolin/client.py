import hashlib
import hmac
import json
import os
import time
from datetime import datetime
import urllib.parse
import requests
from abc import ABC, abstractmethod

class BinanceTestnetConfig:
    FUTURES_ORDER_URL = "https://testnet.binancefuture.com/fapi/v1/order"

class Client(ABC):
    @abstractmethod
    def place_order(self, *args, **kwargs):
        pass

    def print_message(self, message: str) -> None:
        print(message)
        print() # add a line break for console readability

class BinanceClient(Client):
    def __init__(self, api_key: str, api_secret: str, order_url: str, order_place_file_path: str, response_file_path: str):
        self.futures_order_url = BinanceTestnetConfig.FUTURES_ORDER_URL
        self.api_key = api_key
        self.api_secret = api_secret
        self.order_url = order_url
        self.order_place_file_path = order_place_file_path
        self.response_file_path = response_file_path

    def place_order(self, *args, **kwargs):
        symbol = kwargs.get("symbol")
        side = kwargs.get("side")
        trade_type = kwargs.get("trade_type")
        quantity = kwargs.get("quantity")

        # JSON string → Python dict
        json_data = JsonFactory.create_json(symbol=symbol, side=side, trade_type=trade_type, quantity=quantity)
        params = json.loads(json_data)

        # 1. Get Binance timestamp
        r = requests.get("https://testnet.binancefuture.com/fapi/v1/time", timeout=5)
        binance_server_time_ms = r.json()["serverTime"]
        binance_server_time_str = datetime.utcfromtimestamp(binance_server_time_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
        params['timestamp'] = binance_server_time_ms

        local_time_dt = datetime.now()
        local_time_dt_ms = int(local_time_dt.timestamp() * 1000)
        local_time_dt_str = local_time_dt.strftime('%Y-%m-%d %H:%M:%S')

        print(f'[INFO] Binance Server Time: {binance_server_time_str} ({binance_server_time_ms}) | Local Time: {local_time_dt_str} ({local_time_dt_ms})')

        # 2. Generate HMAC signature
        query_string_for_sign = urllib.parse.urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string_for_sign.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        params['signature'] = signature
        print("[INFO] Generated Signature:", signature)

        # 3. Verify signature
        params_for_verify = {}
        for key, value in params.items():
            if key != 'signature':
                params_for_verify[key] = value

        query_string_for_verify = urllib.parse.urlencode(params_for_verify)

        is_valid = self.verify_hmac_signature(query_string_for_verify, signature)
        print("[INFO] Is the signature valid?", is_valid)

        # 4. Generate Final URL
        final_query = urllib.parse.urlencode(params)
        full_url = f"{self.order_url}?{final_query}"
        print('[READY]', full_url)

        # 5. Send the request
        headers = {
            'X-MBX-APIKEY': self.api_key
        }

        response = requests.post(
            BinanceTestnetConfig.FUTURES_ORDER_URL,
            headers=headers,
            data=params,
        )

        print("Status Code:", response.status_code)

        # Check if the request was successful
        if response.status_code == 200:
            # Extract the JSON data as a Python dictionary/list
            data = response.json()

            # Open a file in write mode ("w") and use json.dump()
            with open('output_data.json', "w") as json_file:
                # json.dump() writes the Python object to the file
                json.dump(data, json_file, indent=4)

            print("JSON response successfully saved to 'output_data.json'")
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")


    def verify_hmac_signature(self, query_string, expected_signature):
        calculated_signature = hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(calculated_signature, expected_signature)

class ClientFactory:
    @staticmethod
    def create_client(enabled_exchange_name: str, config: dict, order_place_file_path: str, response_file_path: str) -> Client:
        if enabled_exchange_name == "binance":
            if config["is_testnet"].lower() == "yes":
                return BinanceClient(
                    api_key=config["test_api_key"],
                    api_secret=config["test_api_secret"],
                    order_place_file_path=order_place_file_path,
                    response_file_path=response_file_path,
                    order_url=BinanceTestnetConfig.FUTURES_ORDER_URL,
                )

            return BinanceClient(
                api_key=config["api_key"],
                api_secret=config["api_secret"],
                order_place_file_path=order_place_file_path,
                response_file_path=response_file_path,
                order_url=BinanceMainnetConfig.FUTURES_ORDER_URL,
            )

        raise ValueError("Unsupported exchange")

class JsonFactory:
    @staticmethod
    def create_json(symbol, side, trade_type, quantity):
        order_dict = {
            'symbol': symbol,
            'side': side,
            'type': trade_type,
            'quantity': quantity
        }
        return json.dumps(order_dict, indent=4)
