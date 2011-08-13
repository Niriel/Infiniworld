#! /usr/bin/python
"""Game Loop.

"""
# Standard library.
import time
# My stuff.
from events import ProcessInputsEvent, RunPhysicsEvent, RenderFrameEvent
import evtman
import time_

class GameLoopController(evtman.SingleListener):
    """Runs the whole game."""
    # One common clock for everything for now.
    PERIOD = 1. / 60
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._running = False
    def run(self):
        """Run until a QuitEvent is broadcast."""
        time_update = time_.wallClock()
        self._running = True
        while self._running:
            # This game loop is very simple and don't expect it to do anything
            # smart.  It tries to update at 60 FPS and if it can't, too bad.
            time_now = time_.wallClock()
            if time_now >= time_update:
                self.post(ProcessInputsEvent())
                self._event_manager.pump()
                #
                self.post(RunPhysicsEvent(self.PERIOD))
                self._event_manager.pump()
                #
                self.post(RenderFrameEvent())
                self._event_manager.pump()
                #
                while time_update < time_now:
                    time_update += self.PERIOD
            # I do one nice things though: sleep to free CPU.  I don't want
            # to melt your cores and suck all your batteries if you're mobile.
            time_left = time_update - time_now
            if time_left >= 0:
                time.sleep(time_left)
    def onQuitEvent(self, unused):
        """Stop everything."""
        self._running = False
