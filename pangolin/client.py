import requests
import urllib.parse
import hashlib
import hmac
import json
import time
from decimal import Decimal
from decimal import ROUND_DOWN
from pangolin import constants

class Client:
    def __init__(self, active_urls: list[str], active_symbol: str, active_api_key: str, active_api_secret: str):
        self.active_urls = active_urls
        self.active_symbol = active_symbol
        self.active_api_key = active_api_key
        self.active_api_secret = active_api_secret
        self.response_file_path = constants.Paths.RESPONSE

    def calculate_binance_futures_order_price(self) -> None:
        binance_futures_price_url = self.binance_futures_price_url
        binance_futures_exchange_info_url = self.binance_futures_exchange_info_url
        binance_futures_symbol_info = requests.get(binance_futures_exchange_info_url).json()["symbols"][0]

        for symbol_filter in binance_futures_symbol_info["filters"]:
            if symbol_filter["filterType"] == "PRICE_FILTER":
                binance_futures_order_tick_size = Decimal(symbol_filter["tickSize"])
            elif symbol_filter["filterType"] == "LOT_SIZE":
                binance_futures_order_step_size = Decimal(symbol_filter["stepSize"])

        binance_futures_latest_price = Decimal(requests.get(binance_futures_price_url).json()["price"])

        self.binance_futures_take_profit_price = (
            (binance_futures_latest_price * Decimal("1.060")) / binance_futures_order_tick_size
        ).quantize(0, ROUND_DOWN) * binance_futures_order_tick_size

        self.binance_futures_order_price = (
            (binance_futures_latest_price * Decimal("1.000")) / binance_futures_order_tick_size
        ).quantize(0, ROUND_DOWN) * binance_futures_order_tick_size

        self.binance_futures_stop_loss_price = (
            (binance_futures_latest_price * Decimal("0.940")) / binance_futures_order_tick_size
        ).quantize(0, ROUND_DOWN) * binance_futures_order_tick_size

        self.binance_futures_order_quantity = (
            (Decimal(self.amount_usdt) * Decimal(self.leverage) / self.binance_futures_order_price) / binance_futures_order_step_size
        ).quantize(0, ROUND_DOWN) * binance_futures_order_step_size

    def retrieve_binance_server_time(self):
        binance_futures_server_time = requests.get(
            self.binance_futures_time_url
        ).json().get("serverTime")

        return binance_futures_server_time

    def binance_place_order(self, side: str, trade_type: str, time_in_force: str, amount_usdt: int, leverage: int) -> None:
        self.side = side
        self.amount_usdt = amount_usdt
        self.leverage = leverage

        # Step 1: Assign Binance Futures URLs
        self.binance_futures_price_url = self.combined_urls[1]
        self.binance_futures_exchange_info_url = self.combined_urls[2]
        self.binance_futures_time_url = self.combined_urls[3]
        self.binance_futures_order_url = self.combined_urls[4]

        self.calculate_binance_futures_order_price()

        print("[Client] binance_futures_take_profit_price: " + str(self.binance_futures_take_profit_price))
        print("[Client] binance_futures_order_price:       " + str(self.binance_futures_order_price))
        print("[Client] binance_futures_stop_loss_price:   " + str(self.binance_futures_stop_loss_price))
        print("[Client] binance_futures_order_quantity:    " + str(self.binance_futures_order_quantity))

        binance_futures_server_time = self.retrieve_binance_server_time()

        binance_futures_order_json_data = self.create_binance_futures_order_json(
            symbol=self.active_symbol,
            side=side,
            trade_type=trade_type,
            time_in_force=time_in_force,
            price=self.binance_futures_order_price,
            quantity=self.binance_futures_order_quantity,
            leverage=self.leverage,
            timestamp=binance_futures_server_time,
        )

        binance_futures_order_params = json.loads(binance_futures_order_json_data)

        # Generate HMAC signature
        binance_futures_order_params["signature"] = hmac.new(
            self.active_api_secret.encode("utf-8"),
            urllib.parse.urlencode(binance_futures_order_params).encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        binance_futures_order_response = requests.post(
            self.binance_futures_order_url,
            headers={"X-MBX-APIKEY": self.active_api_key},
            data=binance_futures_order_params
        )

        if binance_futures_order_response.status_code == 200:
            self.binance_futures_order_response_json_data = binance_futures_order_response.json()
            self.binance_futures_order_response_json_data["source"] = 'binanceFutures'
            with open(self.response_file_path, "w", encoding="utf-8") as json_file:
                json.dump(self.binance_futures_order_response_json_data, json_file, indent=4, ensure_ascii=False)

    def create_binance_futures_order_json(
        self,
        symbol: str,
        side: str,
        trade_type: str,
        time_in_force: str,
        price: int,
        quantity: int,
        leverage: int,
        timestamp: int
    ) -> str:
        self.symbol = symbol
        self.side = side
        self.trade_type = trade_type
        self.time_in_force = time_in_force
        self.price = price
        self.quantity = quantity
        self.leverage = leverage
        self.timestamp = timestamp

        order_dict = {
            "symbol": self.symbol,
            "side": self.side,
            "type": self.trade_type,
            "timeInForce": self.time_in_force,
            "price": str(self.price),
            "quantity": str(self.quantity),
            "leverage": self.leverage,
            "timestamp": self.timestamp
        }

        return json.dumps(order_dict, indent=4)

    def get_binance_futures_order_status(self) -> str:
        binance_futures_order_status_params = {
            "symbol": self.binance_futures_order_response_json_data["symbol"],
            "orderId": self.binance_futures_order_response_json_data["orderId"],
            "timestamp": requests.get(self.binance_futures_time_url).json().get("serverTime")
        }

        binance_futures_order_status_params["signature"] = hmac.new(
            self.active_api_secret.encode("utf-8"),
            urllib.parse.urlencode(binance_futures_order_status_params).encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        binance_futures_order_status_response = requests.get(
            self.binance_futures_order_url,
            headers={"X-MBX-APIKEY": self.active_api_key},
            params=binance_futures_order_status_params
        )

        if binance_futures_order_status_response.status_code == 200:
            binance_futures_order_response_json_data = binance_futures_order_status_response.json()
            return binance_futures_order_response_json_data["status"]

    def get_order_side(self):
        return self.side
        """
        #print(binance_futures_order_response_json_data)

        # entry_price = binance_futures_order_response_json_data["price"]

        self.combined_urls = combined_urls
        self.active_symbol = active_symbol
        self.active_api_key = active_api_key
        self.active_api_secret = active_api_secret
        self.response_file_path = response_file_path

        self.binance_futures_price_url = self.combined_urls[1]
        self.binance_futures_exchange_info_url = self.combined_urls[2]
        self.binance_futures_time_url = self.combined_urls[3]
        self.binance_futures_order_url = self.combined_urls[4]
        """
