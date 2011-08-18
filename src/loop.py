#! /usr/bin/python
"""Game Loop.

"""
# Standard library.
from __future__ import division
import logging
import math
import time
# My stuff.
from events import ProcessInputsEvent, RunPhysicsEvent, RenderFrameEvent
import evtman
import time_

LOGGER = logging.getLogger('loop')

class GameLoopController(evtman.SingleListener):
    """Runs the whole game."""
    # This is the period at which we look for user inputs from the
    # mouse/keyboard/joystick.
    INPUT_PERIOD = 1 / 20
    # This is the period at which we run the physics engine.  Note that we use
    # a fixed time step: this increases the repeatability.  If for some reason
    # the time spent since the last iteration of the game loop is bigger than
    # PHYSICS_PERIOD, then we run the physics several times until we catch up.
    PHYSICS_PERIOD = 1 / 25
    # However we put a cap to the number of times we run the physics before
    # rendering a frame: on very slow machines we still want to see something
    # happening on the screen even if the physics is too slow.  The game will
    # probably be unplayable, but at least the player won't be blind.
    PHYSICS_RUNS_MAX = 5
    # This is the minimum period between two frames.  You can set it to zero in
    # order to render at max FPS, but that's silly because your screen has a
    # limited refresh rate anyway.  A good default value could be 1/60 meaning
    # a max of 60 FPS.
    FRAME_PERIOD = 1 / 60

    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._running = False

    def run(self):
        time_finished = 0
        # This are the times at which we should run the next inputs physics
        # or frame renderings.  Let's do it right now for a start.
        input_next = physics_next = frame_next = time.time()
        # This is used for the interpolation of the frames between two physics
        # states.
        physics_prev_1 = 0
        physics_prev_2 = 0
        ratio = 0
        # Start the almost-infinite loop.  The event handler onQuittedEvent
        # will turn self.running to False to end the game.
        self._running = True
        while self._running:
            # That's the time in this iteration of the loop.  Our reference
            # for all calculations.
            time_iter = time_.wallClock()

            if time_iter < time_finished:
                LOGGER.warning("CLOCK WENT BACK IN TIME from %r to %r",
                               time_iter,
                               time_finished)
                # Bad situation here, we do not try to recover, we just skip
                # the rest of the loop and we hope it's getting better.
                input_next = time_iter
                physics_next = time_iter
                frame_next = time_iter
                physics_prev_2 = 0
                time_finished = 0
                # This will give us a jumpy physics since we are shortening
                # a period.  But hey, that's almost never gonna happen, you're
                # not supposed to have your clock sent back in time often !
                continue

            #----------------------------  Inputs  ----------------------------

            if time_iter >= input_next:
                # No need to loop, taking the last inputs is enough.
                self.post(ProcessInputsEvent())
                # Process the events NOW.  Otherwise, the physics step won't
                # be aware of the input changes.  The event queue is FIFO:
                # - event 1: process input request
                # - event 2: run physics request
                # - event 3: player moves north (for example)
                self._event_manager.pump()
                # We don't care if we missed some iterations.  We only want to
                # know the next one in the real-world future.
                left_over = (time_iter - input_next) % self.INPUT_PERIOD
                input_next = time_iter + self.INPUT_PERIOD - left_over

            #---------------------------  Physics  ----------------------------

            # Update the physics of the world as many time as needed, up to a
            # limit, so that we keep refreshing the screen and processing
            # inputs even when we're late.
            physics_runs = 0
            while (time_iter >= physics_next and
                   physics_runs < self.PHYSICS_RUNS_MAX):
                physics_runs += 1
                # Note that we update the physics with a constant delta-time.
                # An alternative would be to run the physics up to right know,
                # and have a variable delta-time.  Apparently, according to the
                # wisdom I found on the Internet, it is a rather bad thing. So
                # I stick to fixed dt.  It's pretty intuitive though, as you
                # can easily explode your simulation with very small or very
                # large dt.
                self.post(RunPhysicsEvent(self.PHYSICS_PERIOD))
                self._event_manager.pump()
                # It is forbidden to skip any physics step so we really ask for
                # the next time, even if that next time is in the real-world
                # past.
                physics_next += self.PHYSICS_PERIOD
                # You could think it could make sense to set physics_prev_2
                # before a multiple update.  But that doesn't work: each
                # physics update sends some events when entities move, and the
                # view catches these events.  We can't pretend that did not
                # happen.
                physics_prev_2 = physics_prev_1
                physics_prev_1 = time_iter
                # Note that physics_prev_1 >= physics_prev_2 even when the
                # clock went back in time because when the clock goes back in
                # time we reset physics_prev_2 to zero.  However, I put this
                # assertion because you cannot trust anyone these days.
                assert physics_prev_1 >= physics_prev_2, \
                       "physics_prev_2 (%r) > physics_prev_1 (%r)" % \
                       (physics_prev_2, physics_prev_1)

            # Start panicking if we get way behind.  Updating the physics of
            # the world is expecting to take less time than rendering frames of
            # polling user inputs from the network.  Something's going wrong
            # here.  This can be triggered if, during the game, you start
            # Firefox or something like that, stealing CPU time from the game.
            # Once Firefox is running it's fine, but the process of starting it
            # is tough.  Another way of having is problem is having a computer
            # that's way too slow.
            if physics_runs >= self.PHYSICS_RUNS_MAX:
                LOGGER.warning("Main loop has troubles catching up: not "
                               "enough CPU time given to the program.  Close "
                               "other programs, or use a faster machine.")
                # Since the game physics is late relatively to the real world,
                # we should not try to interpolate, and instead we must render
                # the world in its last known state. 
                snap_to_last_physics = True
            else:
                snap_to_last_physics = False

            #------------------------- Render frame  --------------------------

            if time_iter >= frame_next:
                # In principle we update the screen more often than we update
                # the physics. There is a need for interpolation.  We
                # interpolate, we do not extrapolate: extrapolating means
                # trying to guess the future, and even if the physics is
                # deterministic, the user input and the AI are much less so.
                # Extrapolating would lead to errors and need corrections,
                # resulting in jitter on the screen. Instead, the frame we
                # render corresponds to some time in the past between two known
                # and correct physical states.  This is a very near past since
                # we update the physics many times per second anyway ; the
                # delay should hardly be noticeable.  To interpolate we
                # introduce a ratio.
                if snap_to_last_physics:
                    ratio = 1
                else:
                    # This is the time we are trying to render.  Somewhere in
                    # the near past.
                    render_time = time_iter - self.PHYSICS_PERIOD
                    # In normal cases, we will have: physics_prev_2 <
                    # render_time <= physics_prev_1 <= time_iter. But that's
                    # dreaming.
                    if physics_prev_2 == 0:
                        # The very first iteration of the game, and each time
                        # the clock went back in time, physics_prev_2
                        # equals zero and the other times are quite big.
                        # Calculating a ratio from here would give us a number
                        # very close to 1, but still it would be kinda dirty
                        # to interpolate between a sane and an insane state.
                        # So just snap to the sane state.
                        ratio = 1
                    elif render_time < physics_prev_2:
                        # For example, if the physics had to catch up for
                        # some delay, then the physics_prev_2 is at a
                        # distance smaller than self.PHYSICS_PERIOD.  We
                        # cannot render that far in the past anymore.
                        # render_time = physics_prev_2
                        ratio = 0
                    elif render_time > physics_prev_1:
                        # And if for some reason the physics is late, then
                        # that's how far we can render, nothing else.
                        # Happens if you pause the game for example.
                        # render_time = physics_prev_1
                        ratio = 1
                    else:
                        # This is the common case: render_time is between the
                        # last two physics time.
                        try:
                            ratio = ((render_time - physics_prev_2) /
                                     (physics_prev_1 - physics_prev_2))
                        except ZeroDivisionError:
                            # This happens each time we needed to catch up on
                            # the physics.  Since we're late we need to display
                            # the last state in order to show the most accurate
                            # information we have.
                            ratio = 1
                            # I thought first that I could test the equality of
                            # physics_prev_1 and physics_prev_2 before
                            # dividing.  But I decided against: I'd rather let
                            # the system complain because that's going to be
                            # way faster and way safer.
                        else:
                            if math.isinf(ratio):
                                # Could happen one day if the denominator is
                                # tiny.  I don't trust divisions.
                                ratio = 1
                            elif ratio < 0:
                                # Clock sent back to the past ?  Weird.  I
                                # don't really know what could do this so I
                                # just round up to zero and I raise an
                                # exception.
                                if __debug__:
                                    print "------- ratio < 0", ratio
                                    print "physics_prev_2", repr(physics_prev_2)
                                    print "render_time   ", repr(render_time)
                                    print "physics_prev_1", repr(physics_prev_1)
                                    print "time_iter     ", repr(time_iter)
                                    raise RuntimeError("Negative ratio")
                                ratio = 0
                            elif ratio > 1:
                                # Refuse to extrapolate.  The view displays up
                                # to the last known physics state, no further.
                                # Imagine you pause the game for example, in
                                # that case the physics is stuck, you really
                                # don't want to see stuff moving infinitely.
                                ratio = 1
                                if __debug__:
                                    print "------- ratio > 0", ratio
                                    print "physics_prev_2", repr(physics_prev_2)
                                    print "render_time   ", repr(render_time)
                                    print "physics_prev_1", repr(physics_prev_1)
                                    print "time_iter     ", repr(time_iter)
                                    raise RuntimeError("Big ratio")
                self.post(RenderFrameEvent(ratio))
                self._event_manager.pump()
                #
                left_over = (time_iter - frame_next) % self.FRAME_PERIOD
                frame_next = time_iter + self.FRAME_PERIOD - left_over

            # Do we have some time left to sleep and therefore save some CPU ?
            # Our highest frequency thing is the frame rendering.  So that's
            # what limits the time we can spend sleeping.
            closest_time = min((input_next, physics_next, frame_next))
            left_over = closest_time - time_.wallClock()
            if left_over > 0:
                # I first thought it would be wise not to sleep for the full
                # left over time and I slept for 90 % of it.  I was wrong.
                # That was leading me to running the loop for nothing and
                # sleeping less and less time until finally we had something to
                # do.  Kind of a Zenon paradox, with more and more shorter and
                # shorter sleeps.  Bad.  So it's better to sleep the full time,
                # and be woken up a little bit too late to be sure to actually
                # have something to do during the next iteration.
                time.sleep(left_over)
            time_finished = time_.wallClock()

    def onQuitEvent(self, unused):
        """Stop everything."""
        self._running = False
