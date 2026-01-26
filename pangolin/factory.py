class UrlFactory:
    def create_binance_futures_wss_url(self, host: str, ticker: str) -> str:
        binance_futures_wss_url = "wss://" + host + "/ws/" + ticker + "@aggTrade"
        print(f"[UrlFactory] WebSocket URL ({binance_futures_wss_url}) has been assembled.")
        return binance_futures_wss_url

    def create_binance_futures_price_url(self, host: str, symbol: str) -> str:
        create_binance_futures_price_url = "https://" + host + "/fapi/v1/ticker/price?symbol=" + symbol
        print(f"[UrlFactory] Rest API URL ({create_binance_futures_price_url}) has been assembled.")
        return create_binance_futures_price_url

    def create_binance_futures_exchange_info_url(self, host: str, symbol: str) -> str:
        binance_futures_exchange_info_url = "https://" + host + "/fapi/v1/exchangeInfo?symbol=" + symbol
        print(f"[UrlFactory] Rest API URL ({binance_futures_exchange_info_url}) has been assembled.")
        return binance_futures_exchange_info_url
