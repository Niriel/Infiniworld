#! /usr/bin/python
"""PlayerController

"""
import evtman
import world

class PlayerController(evtman.SingleListener):
    """Middle man between the keyboard and the controlled character.
    
    The previous line can sound a bit weird: in the real world, the keyboard
    is a mean for the player to control a game-world character.
    
    It is obvious however that the game --made in Python which does not have a
    telepathy.py module-- cannot access the player.  However, what the game can
    do, is infer the desires of the player from his/her keystrokes.  A player
    controls one character, and therefore the desires of the player are
    translated into desires of that characters.
    
    For example, the space key is pressed.  Let's say that the space key is
    used for activating an object in the game world, such as pulling a lever.
    The keyboard controller detects that the key is pressed and sends an event
    saying that Someone is trying to activate something.
    
    Now, the PlayerController receives that event.  The PlayerController knows
    which of the hundreds of characters of the game is the character controlled
    by the player.  Therefore, it raises another Event:
    CharacterActivatesEvent, containing an identifier for the said character.
    The GameWorld will listen to that event, and because it knows the
    landscape, realize that that character is facing a door. It will then then
    understand that the character is trying to open that door.
    
    It could have been possible of course to make the keyboard controller
    directly aware of which character it was controlling.  But the keyboard
    controller is only one of the many ways to control a character, and the
    keyboard controller depends on an architecture and some set of libraries
    (such as pygame). We do not want to have to include this player-to-
    character translation in every single
    keyboard/joypad/mouse/touchscreen/whatever controller.
    
    """
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._entity_id = None
    def onPlayerMovedEvent(self, event):
        """Player says move.  Move what ?"""
        if self._entity_id is not None:
            self.post(world.MoveEntityRequest(self._entity_id, event.force))
    def onEntityCreatedEvent(self, event):
        """TEMPORARY, DEBUG ONLY."""
        # TODO: remove
        # This is not serious of course.  We will need a better way of
        # assigning an entity to a player.
        self._entity_id = event.entity_id
