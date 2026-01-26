from pathlib import Path

class Project:
    NAME = "pangolin"

class FileExtensions:
    INI = ".ini"
    JSON = ".json"

class FileNames:
    CONFIG = Project.NAME + FileExtensions.INI
    RESPONSE = "response" + FileExtensions.JSON

class DirectoryNames:
    DATA = "data"
    STRATEGY = "strategies"

class Paths:
    RESPONSE = Path(Project.NAME) / DirectoryNames.DATA / FileNames.RESPONSE
    STRATEGY = Path(Project.NAME) / DirectoryNames.STRATEGY

class Hosts:
    BINANCE_FUTURES_STREAM = "fstream.binance.com"
    BINANCE_FUTURES_API = "fapi.binance.com"
    BINANCE_TESTNET_FUTURES_API = "testnet.binancefuture.com"

class Endpoints:
    BINANCE_FUTURES_TIME = "/fapi/v1/time"
    BINANCE_FUTURES_ORDER = "/fapi/v1/order"

class Urls:
    BINANCE_FUTURES_TIME = "https://" + Hosts.BINANCE_FUTURES_API + Endpoints.BINANCE_FUTURES_TIME
    BINANCE_TESTNET_FUTURES_TIME = "https://" + Hosts.BINANCE_TESTNET_FUTURES_API + Endpoints.BINANCE_FUTURES_TIME
    BINANCE_FUTURES_ORDER = "https://" + Hosts.BINANCE_FUTURES_API + Endpoints.BINANCE_FUTURES_ORDER
    BINANCE_TESTNET_FUTURES_ORDER = "https://" + Hosts.BINANCE_TESTNET_FUTURES_API + Endpoints.BINANCE_FUTURES_ORDER
