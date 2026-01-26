from pathlib import Path
from datetime import datetime
import time
import json
from websocket import create_connection # WebSokcetStream
from websocket import WebSocketTimeoutException # WebSokcetStream
from contextlib import closing# WebSokcetStream
from .strategy import Strategy

from pangolin import constants

class Manager:
    def __init__(
        self,
        client,
        active_urls: list[str],
        tumbling_window_seconds: int,
        max_total_loop_count: int,
        max_display_loop_count: int,
        connect_timeout_sec: int,
        recv_timeout_sec: int,
        max_retry_wait_sec: int,
    ):
        self.client = client
        self.active_urls = active_urls
        self.tumbling_window_seconds = int(tumbling_window_seconds) # Parsed from config as str; converted to int
        self.max_total_loop_count = max_total_loop_count
        self.max_display_loop_count = max_display_loop_count
        self.connect_timeout_sec = connect_timeout_sec
        self.recv_timeout_sec = recv_timeout_sec
        self.max_retry_wait_sec = max_retry_wait_sec

        self.strategy_folder_path = constants.Paths.STRATEGY
        self.response_file_path = constants.Paths.RESPONSE

        self.cumulative_count = 0
        self.cumulative_price = 0.0
        self.cumulative_quantity = 0.0
        self.avg_prices = []

        self.last_trade_id = None
        self.last_price = None
        self.last_current_time = time.time()

        self.display_loop_count = 0
        self.total_loop_count = 0

        self.strategy = Strategy(
            strategy_folder_path=self.strategy_folder_path
        )

    @property
    def response_file_exists(self) -> bool:
        return Path(self.response_file_path).is_file()

    def run_binance_stream(self):
        binance_futures_wss_url = self.active_urls[0] # WebSocket URL
        binance_futures_price_url = self.active_urls[1] # REST URL for current price
        binance_futures_exchange_info_url = self.active_urls[2] # REST URL for exchange metadata

        # Loop control variables
        retry_count = 0
        stop_running = False

        while not stop_running:
            # Main loop to maintain the WebSocket connection
            #
            # Exception handling:
            # - KeyboardInterrupt: gracefully exit the loop if interrupted by the user
            # - ConnectionError / OSError: handle network-related errors
            #
            # Note: WebSocketTimeoutException should be handled only inside the recv()
            try:
                with closing(
                    create_connection(
                        binance_futures_wss_url, # WebSocketStream URL
                        timeout=self.connect_timeout_sec # Connection timeout
                    )
                ) as ws_conn:
                    retry_count = 0 # Initialize the retry counter for reconnection attempts
                    last_recv_time = time.time()  # Get the current time when the connection is created
                    ws_conn.settimeout(self.recv_timeout_sec) # Set the timeout to the websocket

                    # Emit connection success and startup readiness logs
                    now_timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[INFO] Connected to {binance_futures_wss_url} at {now_timestamp_str} via WebSocket.")
                    print("[INFO] Everything is ready. WebSocket streaming will be started.\n")

                    while True:
                        # Raise WebSocketTimeoutException if no message is received within self.recv_timeout_sec
                        try:
                            raw_message = ws_conn.recv() # Receive data from the socket
                            last_recv_time = time.time() # Get the current time when the message is received

                            # Process incoming WebSocket message:
                            # - Raise ConnectionError if no message received
                            # - Parse message and skip if empty, invalid, or unexpected format
                            # - Catch JSON parsing and key/type errors, log warning, and continue
                            if not raw_message:
                                raise ConnectionError("[ERROR] Empty message received.") # Raise error if no message was received
                            try:
                                # Parse the raw Binance message and valsdate its format
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

                            # Get the current time in seconds
                            self.current_time = time.time()

                            # format current time as a readable string
                            self.current_time_str = datetime.fromtimestamp(self.current_time).strftime('%Y-%m-%d %H:%M:%S')

                            # Check if the defined interval has passed since the last update
                            if self.current_time - self.last_current_time >= self.tumbling_window_seconds:

                                # No messages received during this window; discard this window
                                if self.cumulative_count == 0:
                                    self.last_current_time = self.current_time
                                    continue

                                # Response file detected; signal to stop streaming
                                if self.response_file_exists:
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
                                    total_loop_reset_message = (
                                        "[INFO] Total loop {} reached {}. All will be reset at {}."
                                    ).format(
                                        self.total_loop_count,
                                        self.max_total_loop_count,
                                        self.current_time_str
                                    )

                                    print(total_loop_reset_message)
                                    self.last_current_time = self.current_time

                                    # Reset cumulative statistics for next interval
                                    self.cumulative_count = 0
                                    self.cumulative_price = 0.0
                                    self.cumulative_quantity = 0.0

                                    # Reset loop counters
                                    self.display_loop_count = 0
                                    self.total_loop_count = 0

                                    # Reset avg_prices
                                    self.avg_prices = []

                                    # Go to the next loop
                                    continue

                                #  Handle actions when display loop count reaches maximum
                                if self.display_loop_count % int(self.max_display_loop_count) == 0:
                                    print("=== Triggered ===")
                                    display_loop_reset_message = "[INFO] Display loop {} reached {}/{}. Reset cumulative values will be reset at {}."
                                    print(
                                        display_loop_reset_message.format(
                                            self.display_loop_count,
                                            self.max_display_loop_count,
                                            self.total_loop_count,
                                            self.current_time_str
                                        )
                                    )

                                    strategy = self.strategy.loads(
                                        avg_prices=self.avg_prices
                                    )

                                    strategy.execute(
                                        client=self.client
                                    )

                                    self.last_current_time = self.current_time

                                    # Reset cumulative statistics for next interval
                                    self.cumulative_count = 0
                                    self.cumulative_price = 0.0
                                    self.cumulative_quantity = 0.0

                                    # Reset loop counter
                                    self.display_loop_count = 0
                                    continue

                                # Reset cumulative values related to trades
                                self.last_current_time = self.current_time
                                self.cumulative_price = 0.0
                                self.cumulative_quantity = 0.0

                                # Reset cumulative count related to trades
                                self.cumulative_count = 0

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
                            if (time.time() - last_recv_time) > self.max_retry_wait_sec:
                                raise ConnectionError(f"[INFO] No data for {self.max_retry_wait_sec}s")
                            continue

            # KeyboardInterrupt will be Raised when the user hits the interrupt key (normally Control-C).
            #
            # Reference:
            # - https://docs.python.org/3.13/library/exceptions.html#KeyboardInterrupt
            except KeyboardInterrupt:
                print("[INFO] StreamManager interrupted by user.\n")
                break

            except (ConnectionError, OSError) as e:
                if stop_running:
                    break
                retry_count += 1
                wait = min(self.max_retry_wait_sec, BACKOFF_BASE ** retry_count)
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

    def display_binance_iteration(self):
        print(f'*** iteration {self.display_loop_count} ***')
        print(f'Received: {self.cumulative_count} messages')
        print(f'Time:     {self.current_time_str}')
        print(f'Price:    {self.cumulative_price:.0f} / {self.cumulative_count} = {self.avg_price:.4f}')
        print(f'Quantity: {self.cumulative_quantity:.2f} \n')
