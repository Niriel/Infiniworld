#! /usr/bin/python
"""Game Loop.

"""
# Standard library.
from __future__ import division
import logging
import time
# My stuff.
from infiniworld.events import ProcessInputsEvent
from infiniworld.events import RunPhysicsEvent
from infiniworld.events import RenderFrameEvent
from infiniworld.events import PhysicsPausedEvent
from infiniworld import evtman
from infiniworld import time_

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
    PHYSICS_PERIOD = 1 / 20
    # However we put a cap to the number of times we run the physics before
    # rendering a frame: on very slow machines we still want to see something
    # happening on the screen even if the physics is too slow.  The game will
    # probably be unplayable, but at least the player won't be blind.
    PHYSICS_RUNS_MAX = 10
    # This is the minimum period between two frames.  You can set it to zero in
    # order to render at max FPS, but that's silly because your screen has a
    # limited refresh rate anyway.  A good default value could be 1/60 meaning
    # a max of 60 FPS.
    FRAME_PERIOD = 1 / 60

    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._running = False
        # The physics doesn't run by default.  That lets us show a starting
        # screen.
        self._paused_physics = True

    def run(self):
        """Where ALL the magic happens."""
        # In order to be able to pause various elements of the loop (we'll
        # probably just pause the physics actually), we do not refer to
        # absolute times but to accumulated elapsed times.  Because if you
        # unpause your game after one hour, you do not want the physics to
        # start catching up with one hour of simulation.  So what we do when
        # the game is paused is simply stopping to accumulate time.
        input_accu = physics_accu = frame_accu = 0
        # The elapsed time is a difference between the time at the beginning of
        # the loop and the time at the beginning of the previous loop.  We need
        # that second time here for being able to enter the loop.
        time_old = time_.wallClock()
        # This is used for the interpolation of the frames between two physics
        # states.
        frame_interp_accu = 0
        ratio = 0
        # Start the almost-infinite loop.  The event handler onQuittedEvent
        # will turn self.running to False to end the game.
        self._running = True
        while self._running:
            # That's the time in this iteration of the loop.  Our reference
            # for all calculations.
            time_new = time_.wallClock()
            elapsed_time = time_new - time_old

            if elapsed_time < 0:
                LOGGER.warning("CLOCK WENT BACK IN TIME from %r to %r.  "
                               "Solved by skipping game loop iteration.",
                               time_old, time_new)
                # Bad situation here, we do not try to recover, we just skip
                # the rest of the loop and we hope it's getting better.
                time_old = time_new
                continue

            #----------------------------  Inputs  ----------------------------

            input_accu += elapsed_time
            if input_accu >= self.INPUT_PERIOD:
                input_accu %= self.INPUT_PERIOD
                self.post(ProcessInputsEvent())
                self._event_manager.pump()

            #---------------------------  Physics  ----------------------------

            if not self._paused_physics:
                physics_accu += elapsed_time
                frame_interp_accu += elapsed_time

            # Update the physics of the world as many time as needed, up to
            # a limit, so that we keep refreshing the screen and processing
            # inputs even when we're late.
            physics_runs = 0
            while (physics_accu >= self.PHYSICS_PERIOD and
                   physics_runs < self.PHYSICS_RUNS_MAX):
                physics_accu -= self.PHYSICS_PERIOD
                frame_interp_accu %= self.PHYSICS_PERIOD
                physics_runs += 1
                # Note that we update the physics with a constant time step. An
                # alternative would be to run the physics up to right know, and
                # have a variable time step.  Apparently, according to the
                # wisdom I found on the Internet, the variable time step is a
                # rather bad thing.  So I stick to fixed time step.  It's
                # pretty intuitive though, as you can easily explode your
                # simulation with very small or very large time step.
                #
                # Update: yeah, I had some funny behaviors when using large
                # friction coefficients with small masses, the explosions were
                # really time-step-dependent.  So I fix my time step to make
                # sure that I can contain the explosions.
                #
                # Be careful though: when entities move at high speed,
                # the physics engine will use smaller time steps.  Make sure
                # that your simulation is stable with a time step five to ten
                # times smaller than this one.
                self.post(RunPhysicsEvent(self.PHYSICS_PERIOD))
                self._event_manager.pump()

            # Start panicking if we get way behind.  Updating the physics
            # of the world is expected to take less time than rendering
            # frames or polling user inputs from the network.  Something's
            # going wrong here.  This can be triggered if, during the game,
            # you start Firefox or something like that, stealing CPU time
            # from the game. Once Firefox is running it's fine, but the
            # process of starting it is tough.  Another way of having is
            # problem is having a computer that's way too slow.
            if physics_runs >= self.PHYSICS_RUNS_MAX:
#                LOGGER.warning("Main loop has troubles catching up: not "
#                               "enough CPU time given to the program.  "
#                               "Close other programs, or use a faster "
#                               "machine.")
                # Since the game physics is late relatively to the real
                # world, we should not try to interpolate, and instead we
                # must render the world in its last known state.
                snap_to_last_physics = True
            else:
                snap_to_last_physics = False

            #------------------------- Render frame  --------------------------

            # I am a bit annoyed here.  Indeed, when I reach this point, I am
            # totally ignoring the fact that computing the physics did take
            # some time.  I think I could have a look at the wall clock again.
            # BUT this will make the interpolation weird.

            frame_accu += elapsed_time
            if frame_accu >= self.FRAME_PERIOD:
                try:
                    frame_accu %= self.FRAME_PERIOD
                except ZeroDivisionError:
                    # FRAME_PERIOD = 0 for unlimited FPS.
                    frame_accu = 0
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
                    ratio = frame_interp_accu / self.PHYSICS_PERIOD
                    if ratio > 1:
                        # Refuse to extrapolate.  The view displays up
                        # to the last known physics state, no further.
                        # Imagine you pause the game for example, in
                        # that case the physics is stuck, you really
                        # don't want to see stuff moving infinitely.
                        ratio = 1
                self.post(RenderFrameEvent(ratio))
                self._event_manager.pump()

            #----------------------------  Sleep.  ----------------------------

            # Do we have enough time left to sleep during this iteration? Let's
            # find the next thing we will have to do, the closest
            # input/physics/frame update in time.
            closest = min(self.INPUT_PERIOD - input_accu,
                          self.PHYSICS_PERIOD - physics_accu,
                          self.FRAME_PERIOD - frame_accu)
            # We already spent time in this iteration though, we must subtract
            # this time from the closest time.  That will bring the closest
            # event even closer.
            closest -= time_.wallClock() - time_new
            if closest >= 0:
                time.sleep(closest)
            #--------------------------  We're done.  -------------------------
            time_old = time_new

    def pausePhysics(self, paused):
        """Pause or un-pause the world physics.

        When paused, the time does not flow in the game world.

        """
        self._paused_physics = paused
        self.post(PhysicsPausedEvent(self._paused_physics))

    def onTogglePausePhysicsCommand(self, unused):
        """Typically posted when player presses P key."""
        self.pausePhysics(not self._paused_physics)

    def onPausePhysicsRequest(self, event):
        """Usually posted by the game itself to start or stop the physics."""
        self.pausePhysics(event.paused)

    def onQuitEvent(self, unused):
        """Quit the application, return to shell."""
        self._running = False
