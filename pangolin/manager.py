from .strategy import Strategy
from pathlib import Path

from datetime import datetime
import time
import json

# WebSocket
from websocket import create_connection
from websocket import WebSocketTimeoutException
from contextlib import closing

class Manager:
    # Error messages
    ERROR_ORDER_FILE_EXISTS = "[ERROR] Order place file already exists: {}"
    ERROR_RESPONSE_FILE_EXISTS = "[ERROR] Response file already exists: {}"
    ERROR_EMPTY_MESSAGE = "[ERROR] Empty message received."

    # Info messages
    INFO_NO_FILE_CONFLICTS = "[INFO] Check complete: no file conflicts found."
    STARTUP_MESSAGE = "[INFO] Everything is ready. WebSocket streaming will be started."
    CONNECTION_MESSAGE = "[INFO] Connected to {} at {} via WebSocket."
    INTERRUPT_MESSAGE = '[INFO] StreamManager interrupted by user.'

    # Time / Timeout constants (seconds)
    CONNECT_TIMEOUT_SEC = 30
    RECV_TIMEOUT_SEC = 10
    NO_DATA_TIMEOUT_SEC = 60

    # Numeric constants
    ZERO_FLOAT = 0.0

    def __init__(
        self,
        strategy_folder_path: str,
        order_place_file_path: str,
        response_file_path: str,
        assembled_urls: list[str]
    ):
        self.strategy_folder_path = strategy_folder_path
        self.order_place_file_path = order_place_file_path
        self.response_file_path = response_file_path

        self.assembled_urls = assembled_urls

        self.cumulative_count = 0
        self.cumulative_price = self.ZERO_FLOAT
        self.cumulative_quantity = self.ZERO_FLOAT

        self.last_trade_id = None
        self.last_price = None
        self.last_current_time = time.time()

        self.display_loop_count = 0
        self.total_loop_count = 0

        self.strategy = Strategy(strategy_folder_path=self.strategy_folder_path)

    @property
    def order_place_file_exists(self) -> bool:
        return Path(self.order_place_file_path).exists()

    @property
    def response_file_exists(self) -> bool:
        return Path(self.response_file_path).exists()

    def check_file_conflicts(self) -> None:
        if self.order_place_file_exists:
            raise FileExistsError(self.ERROR_ORDER_FILE_EXISTS.format(self.order_place_file_path))
        if self.response_file_exists:
            raise FileExistsError(self.ERROR_RESPONSE_FILE_EXISTS.format(self.response_file_path))
        self.display_message(message=self.INFO_NO_FILE_CONFLICTS, use_new_line=False)

    def run_binance_stream(self):
        # Binance Futures URLs
        binance_futures_wss_url = self.assembled_urls[0] # WebSocket stream URL
        binance_futures_price_url = self.assembled_urls[1] # Current price REST API URL
        binance_futures_exchange_info_url = self.assembled_urls[2] # Exchange info REST API URL

        # Loop control variables
        retry_count = 0
        stop_running = False

        while True:
            # Main loop to maintain the WebSocket connection
            # Exception handling:
            # - KeyboardInterrupt: gracefully exit the loop if interrupted by the user
            # - ConnectionError / OSError: handle network-related errors
            # Note: WebSocketTimeoutException should be handled only inside the recv()
            try:
                with closing(create_connection(binance_futures_wss_url, timeout=self.CONNECT_TIMEOUT_SEC)) as ws_conn:
                    retry_count = 0 # Initialize the retry counter for reconnection attempts
                    last_recv_time = time.time() # Record the current time once
                    ws_conn.settimeout(self.RECV_TIMEOUT_SEC) # Set the timeout to the websocket
                    self.log_ws_connected(print_messeage=True, binance_futures_wss_url=binance_futures_wss_url)
                    self.display_message(message=self.STARTUP_MESSAGE, use_new_line=False) # Display startup header message

                    while True:
                        # May raise WebSocketTimeoutException if no message is received within RECV_TIMEOUT_SEC
                        try:
                            raw_message = ws_conn.recv() # Receive data from the socket
                            last_recv_time = time.time() # Get the current time in seconds since the epoch

                            # Process incoming WebSocket message:
                            # - Raise ConnectionError if no message received
                            # - Parse message and skip if empty, invalid, or unexpected format
                            # - Catch JSON parsing and key/type errors, log warning, and continue
                            if not raw_message:
                                raise ConnectionError(self.ERROR_EMPTY_MESSAGE) # Raise error if no message was received
                            try:
                                # Parse the raw Binance message and validate its format
                                parsed_message = self.extract_binance_message(raw_message)
                                if parsed_message is None:
                                    # Skip if message is empty or invalid
                                    print("[WARN] skipped empty or invalid message")
                                    continue
                                if len(parsed_message) != 4:
                                    # Skip if message format is unexpected
                                    print(f"[WARN] unexpected message format: {parsed_message}")
                                    continue
                                # Unpack the validated message
                                symbol, price, quantity, timestamp = parsed_message
                            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                                # Handle JSON parsing errors and invalid message formats
                                print(f"[WARN] parse error: {error}")
                                continue

                            # Update cumulative statistics with the latest trade data
                            self.cumulative_count += 1
                            self.cumulative_price += price
                            self.cumulative_quantity += quantity

                            # Get the current time in seconds since the epoch
                            self.current_time = time.time()

                             # Format current time as a readable string
                            self.current_time_str = datetime.fromtimestamp(self.current_time).strftime('%Y-%m-%d %H:%M:%S')

                            # Check if the defined interval has passed since the last update (Normally 10 seconds)...
                            if self.current_time - self.last_current_time >= 10:
                                if self.order_place_file_exists and response_file_exists:
                                    stop_running = True
                                    break

                                # Increment loop counters
                                self.display_loop_count += 1
                                self.total_loop_count += 1

                                if self.total_loop_count % 6 == 0:
                                    print(f"[INFO] Total loop[{self.total_loop_count}] reached 1000. All will be reset at {self.current_time_str}.")
                                    self.last_current_time = self.current_time

                                    # Reset cumulative statistics for next interval
                                    self.cumulative_count = 0
                                    self.cumulative_price = self.ZERO_FLOAT
                                    self.cumulative_quantity = self.ZERO_FLOAT

                                    # Reset loop counters
                                    self.display_loop_count = 0
                                    self.total_loop_count = 0
                                    continue

                                # Compute the average price per trade
                                self.avg_price = self.cumulative_price / self.cumulative_count

                                # Display current iteration summary
                                self.display_binance_iteration()

                                # Reset cumulative values related to trades
                                self.last_current_time = self.current_time
                                self.cumulative_price = self.ZERO_FLOAT
                                self.cumulative_quantity = self.ZERO_FLOAT

                                # Reset cumulative count related to trades
                                self.cumulative_count = 0

                            if stop_running:
                                # Stop flag (stop_running) is set, exit the outer while loop and terminate processing
                                print("Exiting outer loop")
                                break # Break out of the outer loop and stop execution

                        # WebSocketTimeoutException will be raised at socket timeout during read/write data
                        #
                        # Note:
                        # - When the timeout value is reached, WebSocketTimeoutException is triggered by _socket.py's send() and recv() functions
                        #
                        # References:
                        # - https://websocket-client.readthedocs.io/en/latest/examples.html
                        # - https://websocket-client.readthedocs.io/en/latest/exceptions.html#websocket._exceptions.WebSocketTimeoutException

                        except WebSocketTimeoutException:
                            # Compare the current time with last_recv_time, initially set inside `with closing(...) as ws_conn`
                            if (time.time() - last_recv_time) > self.NO_DATA_TIMEOUT_SEC:
                                raise ConnectionError(f"[INFO] No data for {self.NO_DATA_TIMEOUT_SEC}s")
                            continue

            except KeyboardInterrupt:
                self.display_message(message=self.INTERRUPT_MESSAGE, use_new_line=True)
                break

            except (ConnectionError, OSError) as e:
                retry_count += 1
                wait = min(self.NO_DATA_TIMEOUT_SEC, BACKOFF_BASE ** retry_count)
                print(f"[WS ERROR] {e}, retry in {wait}s")
                time.sleep(wait)

    def process_binance_raw_message(self, raw_message):
        pass

    def extract_binance_message(self, message: str):
        try:
            json_data = json.loads(message)

            if json_data.get("e") != "aggTrade":
                return None

            symbol = str(json_data["s"])
            price = float(json_data["p"])
            quantity = float(json_data["q"])
            timestamp = int(json_data["T"]) / 1000

            return symbol, price, quantity, timestamp

        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def display_message(self, message: str, use_new_line: bool):
        if use_new_line:
            print("\n" + message)
        else:
            print(message)

    def log_ws_connected(self, print_messeage: bool, binance_futures_wss_url: str) -> None:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if print_messeage:
            message = self.CONNECTION_MESSAGE.format(binance_futures_wss_url, timestamp)
            print(message)

    def display_binance_iteration(self):
        print(f'*** iteration {self.display_loop_count} ***')
        print(f'Received: {self.cumulative_count} messages')
        print(f'Time:     {self.current_time_str}')
        print(f'Price:    {self.cumulative_price:.0f} / {self.cumulative_count} = {self.avg_price:.4f}')
        print(f'Quantity: {self.cumulative_quantity:.2f} \n')
