import logging
from logging.handlers import RotatingFileHandler
import sys

_log_format = f"%(asctime)s \t [%(levelname)s] \t %(name)s \t (%(filename)s).%(funcName)s(%(lineno)d) \t %(message)s"
datefmt = '%d-%m-%Y %H:%M:%S'


def get_file_handler():
    file_handler = RotatingFileHandler('error.log', maxBytes=10000, encoding='utf-8')  # 100000 bytes = 100 KB
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter(_log_format, datefmt))
    return file_handler


def get_stream_handler():
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter(_log_format, datefmt))
    return stream_handler


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_file_handler())
    logger.addHandler(get_stream_handler())
    return logger
