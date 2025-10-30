from pangolin import Config
from pangolin import APIManager
from pangolin import StreamManager

def main():
    config = Config(
        file_name='example.ini'
    )

    api_manager = APIManager(
        config
    )

    stream_manager = StreamManager(
        config,
        binance_futures_testnet=True
    )

if __name__ == '__main__':
    main()
