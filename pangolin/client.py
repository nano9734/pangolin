import requests
import json
from decimal import Decimal, ROUND_DOWN

class Client:
    def __init__(
        self,
        client_symbol: str,
        assembled_urls: list[str],
        client_api_key: str,
        client_api_secret: str,
        order_place_file_path: str,
        response_file_path: str
    ):
        self.client_symbol = client_symbol
        self.assembled_urls = assembled_urls
        self.client_api_key = client_api_key
        self.client_api_secret = client_api_secret
        self.order_place_file_path = order_place_file_path
        self.response_file_path = response_file_path

    def binance_place_order(self, leverage: int, amount_usdt: int, side: str, trade_type: str):
        # Binance Futures URLs
        binance_futures_price_url = self.assembled_urls[1] # Current price REST API URL
        binance_futures_exchange_info_url = self.assembled_urls[2] # Exchange info REST API URL
        binance_futures_time_url = self.assembled_urls[3] # Server time REST API URL
        binance_futures_order_url = self.assembled_urls[4] # Order REST API
        print(binance_futures_time_url)

        amount_usdt = 100

        price_response = requests.get(binance_futures_price_url).json()
        latest_price = Decimal(price_response["price"])

        quantity = amount_usdt / latest_price

        exchange_info_response = requests.get(binance_futures_exchange_info_url).json()

        symbol_info = exchange_info_response["symbols"][0]

        tick_size = None
        step_size = None

        time_response = requests.get(binance_futures_time_url).json()
        timestamp = time_response.get("serverTime")

        for f in symbol_info["filters"]:
            if f["filterType"] == "PRICE_FILTER":
                tick_size = Decimal(f["tickSize"])
            elif f["filterType"] == "LOT_SIZE":
                step_size = Decimal(f["stepSize"])

        order_price = (latest_price / tick_size).quantize(0, ROUND_DOWN) * tick_size
        order_quantity = (amount_usdt / latest_price / step_size).quantize(0, ROUND_DOWN) * step_size

        binance_order_json = self.create_binance_order_json(
            symbol=self.client_symbol,
            leverage=leverage,
            side=side,
            trade_type=trade_type,
            timeInForce="GTC",
            quantity=order_quantity,
            price=order_price,
            timestamp=timestamp
        )

        print(binance_order_json)

    def create_binance_order_json(
        self,
        symbol: str,
        leverage: int,
        side: str,
        trade_type: str,
        timeInForce: str,
        quantity: int,
        price: int,
        timestamp: int
    ):

        order_dict = {
            "symbol": symbol,
            "leverage": leverage,
            "side": side,
            "type": trade_type,
            "timeInForce": timeInForce,
            "quantity": str(quantity),
            "price": str(price),
            "timestamp": timestamp
        }

        return json.dumps(order_dict, indent=4)
