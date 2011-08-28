#! /usr/bin/python
"""WorldModel.

"""
# Standard library.
import logging
# My stuff.
import events
from entity import EntityModel
from area import AreaModel
from infiniworld.evtman import SingleListener

LOGGER = logging.getLogger('world')

def nextThing(things, thing, offset):
    """Return the previous or next element in an array.

    `things` is an array.
    `thing` is an element of that array.
    `offset` = -1 for previous, 1 for next.

    >>> things = ['apple', 'egg', 'spam']
    >>> nextThing(things, 'egg', 1)
    'spam'
    >>> nextThing(things, 'egg', -1)
    'apple'

    It wraps around:

    >>> nextThing(things, 'spam', 1)
    'apple'
    >>> nextThing(things, 'apple', -1)
    'spam'

    If things is unknown, you get the first element:

    >>> nextThing(things, 'Supercopter', 1)
    'apple'
    >>> nextThing(things, None, -1) # More serious
    'apple'

    If things is empty, you get None:

    >>> nextThing([], 'bunny', 1)
    None

    """
    try:
        index = things.index(thing)
    except ValueError:
        # Not in list.
        if things:
            return things[0]
        else:
            return None
    else:
        index += offset
        index %= len(things)
    return things[index]


class WorldModel(SingleListener):
    """The unique and authoritative top-level representation of the game world.

    """
    def __init__(self, event_manager):
        SingleListener.__init__(self, event_manager)
        self._entity_id_max = -1
        self.entities = {}
        self._area_id_max = -1
        self._areas = {}
    def unregister(self):
        """Also unregisters its content."""
        for area in self._areas.values():
            area.unregister()
        for entity in self.entities.values():
            entity.unregister()
        SingleListener.unregister(self)
    def createArea(self):
        """Create a new area."""
        self._area_id_max += 1
        area_id = self._area_id_max
        area = AreaModel(self._event_manager, self, area_id)
        self._areas[area_id] = area
        return area
    def createEntity(self, factory):
        """Populate the world with a new entity."""
        self._entity_id_max += 1
        entity_id = self._entity_id_max
        entity = factory(self._event_manager, entity_id)
        self.entities[entity_id] = entity
        return entity
    def destroyEntity(self, entity):
        """Remove an entity from the world, forever."""
        del self.entities[entity.entity_id]
        area = entity.area
        if area:
            area.removeEntity(entity)
        entity.unregister()
        self.post(events.EntityDestroyedEvent(entity.entity_id))
    def moveEntityToArea(self, entity_id, area_id_new):
        """Move the entity to the new area.

        If area_id_new is None, the entity will belong to no area.

        """
        entity = self.entities[entity_id]
        area_id_old = entity.area_id
        if area_id_old == area_id_new:
            return
        if area_id_old is not None:
            self._areas[area_id_old].removeEntity(entity)
        if area_id_new is not None:
            self._areas[area_id_new].addEntity(entity)
        LOGGER.debug("Entity %r moved to area %r." % (entity_id, area_id_new))
    def nextEntity(self, entity_id, offset):
        """Return the previous or next entity_id in use."""
        return nextThing(self.entities.keys(), entity_id, offset)
    def nextArea(self, area_id, offset):
        """Return the previous or next area_id in use."""
        return nextThing(self._areas.keys(), area_id, offset)
    def onDestroyEntityRequest(self, event):
        """Something wants an entity to disappear forever."""
        entity = self.entities[event.entity_id]
        self.destroyEntity(entity)
    def onCreateEntityCommand(self, unused):
        """Player wants to create a new entity."""
        self.createEntity(EntityModel)
    def onCreateAreaCommand(self, unused):
        """Player wants to create a new area."""
        self.createArea()
    def onViewNextAreaRequest(self, event):
        """Player wants to see another area."""
        area_id = self.nextArea(event.area_id, event.offset)
        self.post(events.ViewAreaEvent(area_id))
    def onControlNextEntityRequest(self, event):
        """Player wants to control another entity."""
        entity_id = self.nextEntity(event.entity_id, event.offset)
        self.post(events.ControlEntityEvent(entity_id))
    def onMoveEntityToNextAreaRequest(self, event):
        """Player wants to move an entity to another area."""
        if event.entity_id is None:
            return
        entity = self.entities[event.entity_id]
        area_id = nextThing(self._areas.keys(), entity.area_id, event.offset)
        self.moveEntityToArea(event.entity_id, area_id)
    def onEntitySummaryRequest(self, event):
        """Someone needs info about an entity."""
        # I could have put that code on the EntityModel but that would be less
        # efficient: all the entities would receive it and none would really
        # care.  Maybe I should move more code from the entities to here?  Like
        # onMoveEntityRequest for example...
        entity = self.entities[event.entity_id]
        summary = entity.makeSummary()
        self.post(events.EntitySummaryEvent(summary))
