#! /usr/bin/python
"""Time management.

This module is here because the behavior of time.clock and time.time is very
different on Linux and on Windows.

"""
import platform
import time
import logging

LOGGER = logging.getLogger("time")

# Attempt to provide the game loop with the most accurate timer it can find.
_platform = platform.system()
LOGGER.debug("Platform: %s", _platform)
if _platform == 'Windows':
    wallClock = time.clock
    LOGGER.debug("=> Using time.clock for timing.")
else:
    wallClock = time.time
    LOGGER.debug("=> Using time.time for timing.")
del _platform
# Problem: what I log here is not going to be logged anywhere since it is
# executed on import, and there is no LOGGER configured yet.
