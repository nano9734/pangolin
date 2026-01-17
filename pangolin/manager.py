from pathlib import Path
from datetime import datetime
import time
import json

# WebSocket
from websocket import create_connection
from websocket import WebSocketTimeoutException
from contextlib import closing

# Pangolin modules
from .strategy import Strategy

class Manager:
    # Error messages
    ERROR_ORDER_FILE_EXISTS = "[ERROR] Order place file already exists: {}"
    ERROR_RESPONSE_FILE_EXISTS = "[ERROR] Response file already exists: {}"
    ERROR_EMPTY_MESSAGE = "[ERROR] Empty message received."

    # Info messages
    INFO_NO_FILE_CONFLICTS = "[INFO] Check complete: no file conflicts found."
    STARTUP_MESSAGE = "[INFO] Everything is ready. WebSocket streaming will be started.\n"
    CONNECTION_MESSAGE = "[INFO] Connected to {} at {} via WebSocket."
    INTERRUPT_MESSAGE = '[INFO] StreamManager interrupted by user.'
    DISPLAY_LOOP_RESET_MESSAGE = "[INFO] Display loop {} reached {}/{}. Reset cumulative values will be reset at {}."
    TOTAL_LOOP_RESET_MESSAGE = "[INFO] Total loop {} reached {}. All will be reset at {}."

    # Time / Timeout constants (seconds)
    CONNECT_TIMEOUT_SEC = 30
    RECV_TIMEOUT_SEC = 10
    NO_DATA_TIMEOUT_SEC = 60

    # Numeric constants
    ZERO_FLOAT = 0.0

    # BINANCE constants
    BINANCE_MESSAGE_FIELD_COUNT = 4

    def __init__(
        self,
        client,
        strategy_folder_path: str,
        order_place_file_path: str,
        response_file_path: str,
        assembled_urls: list[str],
        tumbling_window_seconds: int,
        max_display_loop_count: int,
        max_total_loop_count: int
    ):
        self.client = client

        # Initialize file paths
        self.strategy_folder_path = strategy_folder_path
        self.order_place_file_path = order_place_file_path
        self.response_file_path = response_file_path

        self.assembled_urls = assembled_urls

        self.tumbling_window_seconds = int(tumbling_window_seconds)
        self.max_display_loop_count = max_display_loop_count
        self.max_total_loop_count = max_total_loop_count

        self.cumulative_count = 0
        self.cumulative_price = self.ZERO_FLOAT
        self.cumulative_quantity = self.ZERO_FLOAT
        self.avg_prices = []

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
            #
            # Exception handling:
            # - KeyboardInterrupt: gracefully exit the loop if interrupted by the user
            # - ConnectionError / OSError: handle network-related errors
            #
            # Note: WebSocketTimeoutException should be handled only inside the recv()
            try:
                with closing(create_connection(binance_futures_wss_url, timeout=self.CONNECT_TIMEOUT_SEC)) as ws_conn:
                    retry_count = 0 # Initialize the retry counter for reconnection attempts
                    plast_recv_time = time.time()  # Get the current time when the connection is created
                    ws_conn.settimeout(self.RECV_TIMEOUT_SEC) # Set the timeout to the websocket
                    self.log_ws_connected(print_messeage=True, binance_futures_wss_url=binance_futures_wss_url)
                    self.display_message(message=self.STARTUP_MESSAGE, use_new_line=False) # Display startup header message

                    while True:
                        # May raise WebSocketTimeoutException if no message is received within RECV_TIMEOUT_SEC
                        try:
                            raw_message = ws_conn.recv() # Receive data from the socket
                            last_recv_time = time.time() # Get the current time when the message is received

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
                                if len(parsed_message) != self.BINANCE_MESSAGE_FIELD_COUNT:
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

                            # Check if the defined interval has passed since the last update
                            if self.current_time - self.last_current_time >= self.tumbling_window_seconds:
                                if self.order_place_file_exists and response_file_exists:
                                    stop_running = True
                                    break

                                # Increment loop counters
                                self.display_loop_count += 1
                                self.total_loop_count += 1

                                # Compute the average price per trade
                                self.avg_price = self.cumulative_price / self.cumulative_count

                                # Append prices into self.avg_prices
                                self.avg_prices.append(self.avg_price)

                                # Display current iteration summary
                                self.display_binance_iteration()

                                if self.total_loop_count % int(self.max_total_loop_count) == 0:
                                    print(
                                        self.TOTAL_LOOP_RESET_MESSAGE.format(
                                            self.total_loop_count,
                                            self.max_total_loop_count,
                                            self.total_loop_count,
                                            self.current_time_str
                                        )
                                    )

                                    self.last_current_time = self.current_time

                                    # Reset cumulative statistics for next interval
                                    self.cumulative_count = 0
                                    self.cumulative_price = self.ZERO_FLOAT
                                    self.cumulative_quantity = self.ZERO_FLOAT

                                    # Reset loop counters
                                    self.display_loop_count = 0
                                    self.total_loop_count = 0

                                    # Reset avg_prices
                                    self.avg_prices = []

                                    # Go to the next loop
                                    continue

                                #  Handle actions when loop count reaches maximum
                                if self.display_loop_count % int(self.max_display_loop_count) == 0:
                                    print(
                                        self.DISPLAY_LOOP_RESET_MESSAGE.format(
                                            self.display_loop_count,
                                            self.max_display_loop_count,
                                            self.total_loop_count,
                                            self.current_time_str
                                        )
                                    )

                                    strategy_instance = self.strategy.load(
                                        avg_prices=self.avg_prices
                                    )

                                    strategy_instance.execute(
                                        client=self.client
                                    )

                                    self.last_current_time = self.current_time

                                    # Reset cumulative statistics for next interval
                                    self.cumulative_count = 0
                                    self.cumulative_price = self.ZERO_FLOAT
                                    self.cumulative_quantity = self.ZERO_FLOAT

                                    # Reset loop counter
                                    self.display_loop_count = 0
                                    continue

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

            # KeyboardInterrupt will be Raised when the user hits the interrupt key (normally Control-C).
            #
            # Reference:
            # - https://docs.python.org/3.13/library/exceptions.html#KeyboardInterrupt
            except KeyboardInterrupt:
                self.display_message(message=self.INTERRUPT_MESSAGE, use_new_line=True)
                break

            except (ConnectionError, OSError) as e:
                retry_count += 1
                wait = min(self.NO_DATA_TIMEOUT_SEC, BACKOFF_BASE ** retry_count)
                print(f"[WS ERROR] {e}, retry in {wait}s")
                time.sleep(wait)

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
