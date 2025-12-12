from urllib.parse import urlunsplit

class StreamManager:
    def __init__(self, config, database):
        print('*** StreamManager ***')

        for validated_exchange_name in config.validated_exchange_names:
            wss_url_list = self._build_websocket_endpoint_list(
                config=config,
                supported_coin_list=self._build_supported_coin_list(config, validated_exchange_name),
                validated_exchange_name=validated_exchange_name
            )

    def _build_supported_coin_list(self, config, validated_exchange_name):
        supported_coin_list_str = getattr(
            config, f'{validated_exchange_name.lower()}_supported_coin_list'
        )

        supported_coin_list = [
            coin_name.strip() for coin_name in supported_coin_list_str.split(',')
        ]

        if config.developer_mode_enabled == True:
            print(f'[INFO] Successfully created {validated_exchange_name.lower()}_supported_coin_list: {supported_coin_list}')

        return supported_coin_list

    def _build_websocket_endpoint_list(self, config, supported_coin_list, validated_exchange_name):
        wss_url_list = []
        for supported_coin_name in supported_coin_list:
            wss_url = self._create_wss_url(supported_coin_name, validated_exchange_name)
            if wss_url is not None:
                wss_url_list.append(wss_url)

        if config.developer_mode_enabled == True:
            i = 1
            for wss_url in wss_url_list:
                print(f'[INFO] Successfully created wss_url_list[{i}]: {wss_url}')
                i = i + 1

        return wss_url_list

    def _create_wss_url(self, supported_coin_name, validated_exchange_name):
        symbol = supported_coin_name.strip().lower() + 'usdt'
        params = f'streams={symbol}@aggTrade/{symbol}@markPrice'
        wss_url = urlunsplit(['wss', 'fstream.binance.com', 'stream', params, ''])

        return wss_url
