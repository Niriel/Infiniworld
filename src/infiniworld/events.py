#! /usr/bin/python
"""Common events for Infiniworld.

Any module is allowed to create its events.  However, it is sometimes
convenient to have some here to avoid circular dependencies.

"""
from evtman import Event

# pylint: disable-msg=R0903
# Too few public methods.  Normal, they're events

class QuitEvent(Event):
    """Order the game to shut down itself.

    This is the last event that will be processed.

    """

class ProcessInputsEvent(Event):
    """Get inputs from the mouse, network, all this stuff."""
    to_log = False

class RenderFrameEvent(Event):
    """Draw things on the screen."""
    to_log = False
    attributes = ('ratio',)

class RunPhysicsEvent(Event):
    """The physics engine has work to do."""
    to_log = False
    attributes = ('timestep',)

class PausePhysicsRequest(Event):
    """Used to pause/unpause the game physics.

    Set the attribute `paused` to True to pause the game.

    """
    attributes = ('paused',)

class PhysicsPausedEvent(Event):
    """Signals that the game is paused or unpaused."""
    attributes = ('paused',)

# Commands are Events that are produced by direct order from the player. They
# are translations of keypresses.  As such, they know NOTHING about entities,
# areas, etc..  Ideally, a keyboard controller should only issue commands.
class StartGameCommand(Event):
    """Leave the title screen, start the physics engine and all that."""
class StartMovingEastCommand(Event):
    """Player moves his character."""
    to_log = False
class StartMovingNorthCommand(Event):
    """Player moves his character."""
    to_log = False
class StartMovingWestCommand(Event):
    """Player moves his character."""
    to_log = False
class StartMovingSouthCommand(Event):
    """Player moves his character."""
    to_log = False
class StopMovingEastCommand(Event):
    """Player moves his character."""
    to_log = False
class StopMovingNorthCommand(Event):
    """Player moves his character."""
    to_log = False
class StopMovingWestCommand(Event):
    """Player moves his character."""
    to_log = False
class StopMovingSouthCommand(Event):
    """Player moves his character."""
    to_log = False
class FireCommand(Event):
    """Player character attacks."""

class CreateAreaCommand(Event):
    """Used in test/debug to create areas."""

class CreateEntityCommand(Event):
    """Used in test/debug to create areas."""

class ViewNextAreaCommand(Event):
    """Used in test/debug to create areas."""
    attributes = ('offset',)

class ControlNextEntityCommand(Event):
    """Used in test/debug to create areas."""
    attributes = ('offset',)

class MoveEntityToNextAreaCommand(Event):
    """Used in test/debug to create areas."""
    attributes = ('offset',)

class TogglePausePhysicsCommand(Event):
    """Used to pause/unpause the game physics.

    Automatically toggles from paused to non-paused.

    """

class GameOverEvent(Event):
    """Duh."""

class ScreenShotCommand(Event):
    """Save a copy of the screen to a file."""

class StatusTextEvent(Event):
    """Send some text to the status text box."""
    attributes = ('text',)