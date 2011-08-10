#! /usr/bin/python
"""Time management.

"""
import platform
import time
import logging

logger = logging.getLogger("time")

_platform = platform.system()
logger.debug("Platform: %s", _platform)
if _platform == 'Windows':
    wallClock = time.clock
    logger.debug("=> Using time.clock for timing.")
else:
    wallClock = time.time
    logger.debug("=> Using time.time for timing.")
