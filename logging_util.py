# logger_utils.py
import logging


class LoggerHelper:
    # set up logger
    logger = logging.getLogger('mylog')
    logger.setLevel(logging.DEBUG)

    handler = logging.FileHandler('mylog.log')
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    @staticmethod
    def debug(message):
        LoggerHelper.logger.debug(message)

    @staticmethod
    def info(message):
        LoggerHelper.logger.info(message)

    @staticmethod
    def warning(message):
        LoggerHelper.logger.warning(message)

    @staticmethod
    def error(message):
        LoggerHelper.logger.error(message)

    @staticmethod
    def critical(message):
        LoggerHelper.logger.critical(message)
