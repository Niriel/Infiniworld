#! /usr/bin/python
"""Game Loop.

"""
import time
from events import ProcessInputsEvent, RenderFrameEvent
import evtman
import time_

class GameLoopController(evtman.SingleListener):
    # One common clock for everything for now.
    PERIOD = 1. / 60
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._running = False
    def run(self):
        time_update = time_.wallClock()
        self._running = True
        while self._running:
            time_now = time_.wallClock()
            if time_now >= time_update:
                self.post(ProcessInputsEvent())
                self._event_manager.pump()
                self.post(RenderFrameEvent())
                self._event_manager.pump()
                while time_update < time_now:
                    time_update += self.PERIOD
            time_left = time_update - time_now
            if time_left >= 0:
                time.sleep(time_left)
    def onQuitEvent(self, unused):
        self._running = False
