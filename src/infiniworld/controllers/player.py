#! /usr/bin/python
"""PlayerController

"""
import logging
from infiniworld import evtman
from infiniworld import geometry
from infiniworld import models
from infiniworld.events import GameOverEvent
from infiniworld.models import events


LOGGER = logging.getLogger("player")

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
        self.area_id = None
        self.going_east = 0
        self.going_north = 0
        self.going_west = 0
        self.going_south = 0

    def moveEntity(self):
        """The player pushes his/her entity in a given direction."""
        x = self.going_east - self.going_west
        y = self.going_north - self.going_south
        if x and y:
            x /= 2 ** .5
            y /= 2 ** .5
        direction = geometry.Vector(x, y)
        self.post(models.events.MoveEntityRequest(self._entity_id, direction))

    def onStartMovingEastCommand(self, unused):
        """Players wants to move East."""
        if not self.going_east:
            self.going_east = 1
            self.moveEntity()
    def onStartMovingNorthCommand(self, unused):
        """Players wants to move North."""
        if not self.going_north:
            self.going_north = 1
            self.moveEntity()
    def onStartMovingWestCommand(self, unused):
        """Players wants to move West."""
        if not self.going_west:
            self.going_west = 1
            self.moveEntity()
    def onStartMovingSouthCommand(self, unused):
        """Players wants to move South."""
        if not self.going_south:
            self.going_south = 1
            self.moveEntity()
    def onStopMovingEastCommand(self, unused):
        """Players stops moving East."""
        if self.going_east:
            self.going_east = 0
            self.moveEntity()
    def onStopMovingNorthCommand(self, unused):
        """Players stops moving North."""
        if self.going_north:
            self.going_north = 0
            self.moveEntity()
    def onStopMovingWestCommand(self, unused):
        """Players stops moving West."""
        if self.going_west:
            self.going_west = 0
            self.moveEntity()
    def onStopMovingSouthCommand(self, unused):
        """Players stops moving South."""
        if self.going_south:
            self.going_south = 0
            self.moveEntity()
    def onFireCommand(self, unused):
        """Player wants its entity to attack."""
        self.post(events.AttackRequest(self._entity_id))
    def onViewAreaEvent(self, event):
        """Debug/Test. Remember the current area."""
        self.area_id = event.area_id
        LOGGER.debug("Viewing area %r.", event.area_id)
    def onControlEntityEvent(self, event):
        """Remember the current entity."""
        self._entity_id = event.entity_id
        LOGGER.debug("Controlling entity %r.", event.entity_id)
    def onCreatureDiedEvent(self, event):
        """Game over?"""
        if event.entity_id == self._entity_id:
            self.post(GameOverEvent())
