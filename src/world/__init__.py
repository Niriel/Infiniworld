"""World model."""
# Standard library.
import logging
import weakref
# My stuff.
import events
import evtman
import gen
import geometry
import physics
import tile

LOGGER = logging.getLogger('world')

class WorldError(RuntimeError):
    """Base exception class for the world package."""
class AlreadyInAreaError(WorldError):
    """The area already contains what you are trying to add to it."""
class NotInAreaError(WorldError):
    """The area does not contain that object."""

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


class EntityModel(evtman.SingleListener):
    """An entity in Infiniworld is anything that can move."""
    def __init__(self, event_manager, entity_id):
        evtman.SingleListener.__init__(self, event_manager)
        self.entity_id = entity_id
        self.area_id = None
        # By default, an entity has a mass of 60 kg.  Yeah.
        self.particle = physics.Particle(60, geometry.Vector())
        self._walk_force = physics.ConstantForce(geometry.Vector())
        self._friction_force = physics.KineticFrictionForce(-100)
        self.particle.forces.add(self._walk_force)
        self.particle.forces.add(self._friction_force)
        self._walk_strentgh = 1000
        #
        self.post(events.EntityCreatedEvent(entity_id))
        LOGGER.info("Entity %i created.", entity_id)
    def makeSummary(self):
        """Return a dictionary with enough info the the View to work with."""
        return {"entity_id" : self.entity_id,
                "area_id" : self.area_id,
                "pos": self.particle.pos.copy()}
    def setPosVel(self, pos, vel):
        """Set the position and velocity of the particle, post MovedEvent."""
        if pos != self.particle.pos:
            self.post(events.EntityMovedEvent(self.entity_id, pos))
        self.particle.pos = pos
        self.particle.vel = vel
    def onMoveEntityRequest(self, event):
        """Push the entity according to the player's wish."""
        self._walk_force.vector = event.force * self._walk_strentgh



class AreaModel(evtman.SingleListener):
    """An area has a tile map, entities, etc.

    An area can represent a town, a dungeon level, the overworld...

    """
    def __init__(self, event_manager, area_id):
        evtman.SingleListener.__init__(self, event_manager)
        self._area_id = area_id
        # Only keep weak references to the entities because they are owned by
        # the World itself, not by the area.  They can move between areas, or
        # even be in no area at all.
        self._entities = weakref.WeakValueDictionary()
        self.tile_map = tile.TileMap() 
    def addEntity(self, entity):
        """Add the entity to the area.

        If you are moving the entity from an area to another, you have to take
        care yourself of removing the entity from the first area yourself. Only
        the WorldModel can do that, because it's the only thing that knows both
        areas.

        """
        entity_id = entity.entity_id
        entity.area_id = self._area_id
        if entity_id in self._entities:
            raise AlreadyInAreaError()
        self._entities[entity_id] = entity
        self.post(events.EntityEnteredAreaEvent(entity_id,
                                                self._area_id,
                                                entity.particle.pos))
    def removeEntity(self, entity):
        """Remove the entity from the area."""
        entity_id = entity.entity_id
        try:
            del self._entities[entity_id]
        except KeyError:
            raise NotInAreaError()
        entity.area_id = None
        self.post(events.EntityLeftAreaEvent(entity_id, self._area_id))
    def runPhysics(self, timestep):
        """Compute the physics and apply it."""
        for entity in self._entities.itervalues():
            particle = entity.particle
            new_pos, new_vel = particle.integrate(timestep)
            entity.setPosVel(new_pos, new_vel)
    def onAreaContentRequest(self, event):
        """Someone asks what's in this area.

        Warning: the response is an AreaContentEvent that is posted, and
        therefore put at the end of the event queue.  It means that a few
        events can be processed between the AreaContentRequest and the
        AreaContentEvent. One can imagine that an entity has arrived or left
        the area.  When this happens, the AreaContentEvent may not correct
        anymore.  However, that invalid state is corrected by other events
        coming later.

        Scenario 1:

        AreaModel posts EntityEnteredAreaEvent.
        AreaView posts AreaContentRequest.
        AreaView receives EntityEnteredAreaEvent and adds EntityView.
        AreaModel receives AreaContentRequest.
        AreaModel posts AreaContentEvent.
        AreaView receives AreaContentEvent, which contains the most up-to-date
            information, so that's good.

        Scenario 2:

        AreaView posts AreaContentRequest.
        AreaModel receives AreaContentRequest and posts AreaContentEvent.
        AreaModel posts EntityEnteredAreaEvent
        AreaView receives AreaContentRequest, which is not invalid.
        AreaView receives EntityEnteredAreaEvent, which puts AreaView in a
            valid state.

        """
        if event.area_id == self._area_id:
            entities = [entity.makeSummary()
                         for entity in self._entities.itervalues()]
            tilemap = self.tile_map.makeSummary()
            self.post(events.AreaContentEvent(self._area_id,
                                              entities, tilemap))
    def onRunPhysicsEvent(self, event):
        """The main loop tells us to move our entities."""
        self.runPhysics(event.timestep)

class WorldModel(evtman.SingleListener):
    """The unique and authoritative top-level representation of the game world.
    
    """
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._entity_id_max = -1
        self._entities = {}
        self._area_id_max = -1
        self._areas = {}
    def unregister(self):
        """Also unregisters its content."""
        for area in self._areas.values():
            area.unregister()
        for entity in self._entities.values():
            entity.unregister()
        evtman.SingleListener.unregister(self)
    def createArea(self):
        """Create a new area."""
        self._area_id_max += 1
        area_id = self._area_id_max
        area = AreaModel(self._event_manager, area_id)
        self._areas[area_id] = area
        LOGGER.info("Area %i created.", area_id)
        return area
    def createEntity(self):
        """Populate the world with a new entity."""
        self._entity_id_max += 1
        entity_id = self._entity_id_max
        entity = EntityModel(self._event_manager, entity_id)
        self._entities[entity_id] = entity
        return entity
    def destroyEntity(self, entity_id):
        """Remove an entity from the world, forever."""
        entity = self._entities.pop(entity_id)
        entity.unregister()
        self.post(events.EntityDestroyedEvent(entity_id))
    def moveEntityToArea(self, entity_id, area_id_new):
        """Move the entity to the new area.

        If area_id_new is None, the entity will belong to no area.

        """
        entity = self._entities[entity_id]
        area_id_old = entity.area_id
        if area_id_old == area_id_new:
            return
        if area_id_old is not None:
            self._areas[area_id_old].removeEntity(entity)
        if area_id_new is not None:
            self._areas[area_id_new].addEntity(entity)
        LOGGER.info("Entity %r moved to area %r." % (entity_id, area_id_new))
    def nextEntity(self, entity_id, offset):
        """Return the previous or next entity_id in use."""
        return nextThing(self._entities.keys(), entity_id, offset)
    def nextArea(self, area_id, offset):
        """Return the previous or next area_id in use."""
        return nextThing(self._areas.keys(), area_id, offset)
    def onCreateEntityCommand(self, unused):
        """Player wants to create a new entity.

        This is not meant to stay, it's only for testing purposes.

        """
        # TODO: remove.
        self.createEntity()
    def onCreateAreaCommand(self, unused):
        """Player wants to create a new area.

        This is not meant to stay, it's only for testing purposes.

        """
        # TODO: remove
        self.createArea()
    def onViewNextAreaRequest(self, event):
        """Player wants to see another area."""
        # TODO: remove
        area_id = self.nextArea(event.area_id, event.offset)
        self.post(events.ViewAreaEvent(area_id))
    def onControlNextEntityRequest(self, event):
        """Player wants to control another entity."""
        # TODO: remove
        entity_id = self.nextEntity(event.entity_id, event.offset)
        self.post(events.ControlEntityEvent(entity_id))
    def onMoveEntityToNextAreaRequest(self, event):
        """Player wants to move an entity to another area."""
        # TODO: remove
        if event.entity_id is None:
            return
        entity = self._entities[event.entity_id]
        area_id = nextThing(self._areas.keys(), entity.area_id, event.offset)
        self.moveEntityToArea(event.entity_id, area_id)
