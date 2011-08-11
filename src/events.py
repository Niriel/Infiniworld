#! /usr/bin/python
"""Common events for Infiniworld.

Any module is allowed to create its events.  However, it is sometimes
convenient to have some here to avoid circular dependencies.

"""
from evtman import Event

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

class PlayerMovedEvent(Event):
    """The player is asking to move its character.
    
    This is raised when the player is pressing the keys or using the joypad,
    asking to move a character.  This event is posted by the controller in
    charge of polling the keyboard and other input devices.  The
    PlayerController receives it, and responds by posting a MoveEntityRequest
    corresponding to the entity that the player is controlling.
    
    The best practice is to post this event ONLY when the force changes.

    """
    attributes = ('force', )
