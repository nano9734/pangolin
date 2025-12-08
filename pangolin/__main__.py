from pangolin import Config
from pangolin import Database
from pangolin import APIManager
from pangolin import StreamManager

# define main function
def main():
    config = Config()
    database = Database(config)
    api_manager = APIManager()
    stream_manager = StreamManager(config)

# execute only run as a script
if __name__ == '__main__':
    main()
