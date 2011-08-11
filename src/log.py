#! /usr/bin/python
"""Configuration of the logging system.
"""
import logging
import sys

__all__ = ['setup']

class CachelessFormatter(logging.Formatter):
    # I came up with that after reading the answers to
    #     http://stackoverflow.com/questions/5875225/
    # which pointed me to
    #     http://bugs.python.org/issue6435
    # I still think Vinay Sajip has a bit of an attitude :p.
    def format(self, record):
        # Disable the caching of the exception text.
        backup = record.exc_text
        record.exc_text = None
        s = logging.Formatter.format(self, record)
        record.exc_test = backup
        return s

class ConsoleFormatter(CachelessFormatter):
    def formatException(self, exc_info):
        return "           %s: %s" % exc_info[:2]

def setup(path):
    file_handler = logging.FileHandler(path, mode='w')
    file_handler.setLevel(logging.DEBUG)
    formatter = CachelessFormatter("%(asctime)s %(levelname)-8s "
                                   "%(name)-16s %(message)s "
                                   "[%(filename)s@%(lineno)d in %(funcName)s]")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    formatter = ConsoleFormatter("%(levelname)-8s - %(message)s")
    console_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    if __debug__:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info("Logger ready.")

if __name__ == '__main__':
    setup('test.log')
    logger = logging.getLogger()
    logger.debug("Only shows in the file")
    try:
        1 / 0
    except ZeroDivisionError:
        pass
    logger.exception("boom")
