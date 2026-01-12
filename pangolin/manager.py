# SPDX-License-Identifier: GPL-2.0-or-later

import json
import os
import time
from contextlib import closing
from datetime import datetime
from typing import Mapping
from typing import Tuple
from websocket import create_connection
from websocket import WebSocketTimeoutException
from .strategies import GetStrategy
from dataclasses import dataclass

class Manager:
    STREAM_MANAGER_INTERRUPT_MSG = '[INFO] StreamManager interrupted by user.'
    CONNECTION_MSG = "[WebSocket] connected to {} at {}"
    ZERO_FLOAT = 0.0

    def __init__(self, enabled_exchange_name: str, loaded_exchange_config: Mapping[str, str], wss_url: str, database: "Database", order_place_file_path: str):
        self.enabled_exchange_name = enabled_exchange_name
        self.loaded_exchange_config = loaded_exchange_config
        self.wss_url = wss_url
        self.database = database
        self.order_place_file_path = order_place_file_path
        self.cumulative_count = 0
        self.cumulative_price = self.ZERO_FLOAT
        self.cumulative_quantity = self.ZERO_FLOAT
        self.last_trade_id = None
        self.last_price = None
        self.last_current_time = time.time()
        self.avg_price = self.ZERO_FLOAT
        self.display_loop_count = 0
        self.total_loop_count = 0
        self.strategy = GetStrategy()

    def run(self):
        retry_count = 0
        stop_running = False
        print(f"[INFO] StreamManager started for exchange '{self.exchange_name}'")

        if self.order_place_file_exists:
            raise FileExistsError(f"Order place file already exists: {self.order_place_file_path}")

        while True:
            try:
                with closing(create_connection(self.wss_url, timeout=30, enable_multithread=True, ping_interval=20, ping_timeout=10)) as ws_conn:
                    retry_count = 0  # reset on success
                    trade_data_extractor = self.get_trade_data_extractor()
                    self.log_ws_connected() # log connection message
                    last_recv_time = time.time()

                    while True:
                        try:
                            message = ws_conn.recv()
                            if not message:
                                raise ConnectionError("Empty message received")
                            last_recv_time = time.time()
                        except WebSocketTimeoutException:
                            if time.time() - last_recv_time > 60:
                                raise ConnectionError("No data for 60s")
                            continue

                        try:
                            symbol, price, quantity, timestamp = trade_data_extractor(message)
                        except (json.JSONDecodeError, KeyError, TypeError) as e:
                            print(f"[WARN] parse error: {e}")
                            continue

                        self.cumulative_count += 1
                        self.cumulative_price += price
                        self.cumulative_quantity += quantity

                        # 10초 간격 타이머 출력
                        current_time = time.time()
                        current_time_str = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
                        if current_time - self.last_current_time >= 10:
                            if self.order_place_file_exists:
                                stop_running = True
                                break
                            self.display_loop_count += 1
                            self.total_loop_count += 1

                            if self.total_loop_count % 360 == 0:
                                print(f"[INFO] Total loop[{self.total_loop_count}] reached 1000. All will be reset at {current_time_str}.")
                                self.last_current_time = current_time
                                self.cumulative_count = 0
                                self.cumulative_price = self.ZERO_FLOAT
                                self.cumulative_quantity = self.ZERO_FLOAT
                                self.display_loop_count = 0
                                self.total_loop_count = 0
                                self.database.delete_all_stocks()
                                self.database.save_changes()
                                continue # do not use raise, go to the next iteration

                            if self.total_loop_count % 6 == 0:
                                self.database.save_changes()
                                self.strategy.execute(database_cursor=self.database.cursor)

                            self.avg_price = self.cumulative_price / self.cumulative_count

                            stock_record = {
                                "symbol": symbol,
                                "avg_price": self.avg_price,
                                "cumulative_quantity": self.cumulative_quantity,
                                "current_time": current_time
                            }

                            self.database.insert_row(**stock_record)

                            print(f'*** iteration {self.display_loop_count} ***')
                            print(f'Received: {self.cumulative_count} messages')
                            print(f'Time:     {current_time_str}')
                            print(f'Price:    {self.cumulative_price:.0f} / {self.cumulative_count} = {self.avg_price:.4f}')
                            print(f'Quantity: {self.cumulative_quantity:.2f}')
                            print() # add a line break for console readability
                            self.last_current_time = current_time
                            self.cumulative_count = 0
                            self.cumulative_price = self.ZERO_FLOAT
                            self.cumulative_quantity = self.ZERO_FLOAT

                    if stop_running:
                        print("Exiting outer loop")
                        break  # outer loop 탈출

            except KeyboardInterrupt:
                print(self.STREAM_MANAGER_INTERRUPT_MSG)
                break

            except (ConnectionError, TimeoutError) as e:
                retry_count += 1
                wait = min(60, 2 ** retry_count)
                print(f"[WS ERROR] {e}, retry in {wait}s")
                time.sleep(wait)

            except Exception as e:
                print(f"[FATAL] {e}")
                raise

    def get_trade_data_extractor(self):
        extractor_name = f"extract_{self.enabled_exchange_name}_trade_data"
        extractor = getattr(self, extractor_name, None)

        if extractor is None:
            raise ValueError(f"[ERROR] Unsupported exchange: {self.enabled_exchange_name}")

        return extractor

    @property
    def order_place_file_exists(self) -> bool:
        return os.path.exists(self.order_place_file_path)

    @property
    def exchange_name(self) -> str:
        return self.enabled_exchange_name

    def log_ws_connected(self) -> None:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = self.CONNECTION_MSG.format(self.wss_url, timestamp)
        print(message)

    def extract_binance_trade_data(self, message: str) -> Tuple[str, float, float, float]:
        json_data = json.loads(message)
        symbol = str(json_data['s'])
        price = float(json_data['p'])
        quantity = float(json_data['q'])
        timestamp = int(json_data["T"]) / 1000
        return symbol, price, quantity, timestamp
