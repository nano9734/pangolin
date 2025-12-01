import json
import sqlite3
import sys
from contextlib import closing
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo
from websocket import create_connection
from .strategies import GetStrategy

class StreamManager:
    def __init__(self, config, database_file_name):
        self.database_file_name = database_file_name
        # create an instance of GetStrategy
        self.get_strategy = GetStrategy()

        if config.stream_manager_is_enabled == 'yes':
            # allowed exchange class names
            class_names = []
            for class_name in config.allowed_class_names:
                if class_name not in ['config', 'logger', 'database', 'stream_manager']:
                    class_names.append(class_name.capitalize())

            # one class or multiple classes
            if len(class_names) == 1:
                class_name = class_names[0]
                url = self.build_url(config, class_name=class_name, class_names=None)
                self.process_stream_data(url)
            else:
                # url = self.build_url(config, class_name=None, class_names=class_names)
                pass # multiple classes...

            #self.process_stream_data(url)

    def build_url(self, config, class_name, class_names):
        protocol = 'wss'
        # construct Binance WebSocket stream URL
        if class_name == 'Binance':
            host = 'fstream.binance.com'
            path = 'stream'
            if class_names is None:
                if config.binance_supported_coin_list == 'BTC':
                    symbol = config.binance_supported_coin_list.lower() + 'usdt'
                    params = f'streams={symbol}@aggTrade/{symbol}@markPrice'
                    url_data = [protocol, host, path, params, '']
                return urlunsplit(url_data)

    def process_stream_data(self, url):
        while True:
            try:
                if urlsplit(url).netloc == 'fstream.binance.com':
                    table_name = 'binance_futures'
                    json_data = self.retrieve_json_data(url)
                    if json_data['stream'].endswith('aggTrade'):
                        price = float(json_data['data']['p'])
                        quantity = float(json_data['data']['q'])
                        trade_time_ms = int(json_data['data']['T'])
                        current_time_ms = int(datetime.now(ZoneInfo('Asia/Seoul')).timestamp() * 1000)

                        # connect to database
                        conn = sqlite3.connect(self.database_file_name)
                        cursor = conn.cursor()

                        # create an table if not exists
                        cursor.execute(
                            f"""
                            CREATE TABLE IF NOT EXISTS {table_name} (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                price REAL,
                                quantity REAL,
                                trade_time INTEGER
                            );
                            """
                        )

                        # insert a value into table
                        cursor.execute(
                            f"""
                            INSERT INTO {table_name} (price, quantity, trade_time)
                            VALUES (:price, :quantity, :trade_time)
                            """,
                            {
                                "price": price,
                                "quantity": quantity,
                                "trade_time": trade_time_ms
                            }
                        )

                        conn.commit()
                        conn.close()
                        self.get_strategy.run()

            except KeyboardInterrupt:
                print("\nProgram interrupted. Exiting...")
                sys.exit()

    def retrieve_json_data(self, url):
        with closing(create_connection(url)) as conn:
            return json.loads(conn.recv())
