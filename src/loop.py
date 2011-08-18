#! /usr/bin/python
"""Game Loop.

"""
# Standard library.
from __future__ import division
import time
# My stuff.
from events import ProcessInputsEvent, RunPhysicsEvent, RenderFrameEvent
import evtman
import time_


class Timer(evtman.SingleListener):
    def __init__(self, event_manager, time, period, event):
        evtman.SingleListener.__init__(self, event_manager)
        self.time = time
        self.period = period
        self.event = event
    def process(self, time):
        if time >= self.time:
            self.post(self.event)
            self._event_manager.pump()
            while self.time <= time:
                self.time += self.period
        return self.time
             

class GameLoopController(evtman.SingleListener):
    """Runs the whole game."""
    PERIOD_INPUT = 1 / 20
    PERIOD_PHYSICS = 1 / 10
    PERIOD_RENDER = 1 / 60
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._running = False
    def run(self):
        """Run until a QuitEvent is broadcast."""
        now = time_.wallClock()
        timer_input = Timer(self._event_manager, now, self.PERIOD_INPUT, ProcessInputsEvent())
        timer_physics = Timer(self._event_manager, now, self.PERIOD_PHYSICS, RunPhysicsEvent(self.PERIOD_PHYSICS))
        timer_render = Timer(self._event_manager, now, self.PERIOD_RENDER, RenderFrameEvent())
        self._running = True
        while self._running:
            # This game loop is very simple and don't expect it to do anything
            # smart.  It tries to update at 60 FPS and if it can't, too bad.
            now = time_.wallClock()
            next_input = timer_input.process(now)
            next_physics = timer_physics.process(now)
            next_render = timer_render.process(now)

            # I do one nice things though: sleep to free CPU.  I don't want
            # to melt your cores and suck all your batteries if you're mobile.
            time_next = min(next_input, next_physics, next_render)
            time_left = time_next - time_.wallClock()
            if time_left >= 0:
                time.sleep(time_left)

    def onQuitEvent(self, unused):
        """Stop everything."""
        self._running = False
