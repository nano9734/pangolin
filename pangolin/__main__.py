from . import Config
from . import APIManager
from . import StreamManager

config = Config(file_name='config.ini')
api_manager = APIManager()
stream_manager = StreamManager(config, database_file_name='data.db')
