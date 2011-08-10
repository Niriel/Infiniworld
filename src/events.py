#! /usr/bin/python
"""Common events for Infiniworld.

Put in a specific file to avoid circular dependencies.

Any module is allowed to declare its own events though.

"""
from evtman import Event

class QuitRequest(Event):
    """User asked to quit the game."""

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
    attributes = ('vector', )