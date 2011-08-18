"""World model."""
# Standard library.
import logging
import math
from operator import attrgetter
import weakref
# My stuff.
import events
import evtman
import geometry
import materials
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
        # By default, an entity has a mass of 60 kg and a radius of 50 cm.
        # Making them so big allows me to check that my collision code allows
        # them to just squeeze between two tiles that are one meter apart.
        self.body = physics.CircularBody(60, geometry.Vector(),
                                         materials.MATERIAL_FLESH, 0.5)
        self._walk_force = physics.ConstantForce(geometry.Vector())
        self.friction_force = physics.KineticFrictionForce(-100)
        self.body.forces.add(self._walk_force)
        self.body.forces.add(self.friction_force)
        self._walk_strentgh = 1000
        self.is_moving = False
        #
        self.post(events.EntityCreatedEvent(entity_id))
        LOGGER.info("Entity %i created.", entity_id)
    def makeSummary(self):
        """Return a dictionary with enough info the the View to work with."""
        return {"entity_id" : self.entity_id,
                "area_id" : self.area_id,
                "pos": self.body.pos.copy()}
    def setPosVel(self, pos, vel):
        """Set the position and velocity of the body, post MovedEvent."""
        if pos != self.body.pos:
            self.post(events.EntityMovedEvent(self.entity_id, pos))
        self.body.pos = pos
        self.body.vel = vel
    def onMoveEntityRequest(self, event):
        """Push the entity according to the player's wish."""
        if event.entity_id == self.entity_id:
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
        self.affectEntityWithTile(entity)
        self.post(events.EntityEnteredAreaEvent(entity_id,
                                                self._area_id,
                                                entity.body.pos))
    def removeEntity(self, entity):
        """Remove the entity from the area."""
        entity_id = entity.entity_id
        try:
            del self._entities[entity_id]
        except KeyError:
            raise NotInAreaError()
        entity.area_id = None
        self.post(events.EntityLeftAreaEvent(entity_id, self._area_id))

    def tileCoordAt(self, pos):
        """Return the coordinate of the tile corresponding to the position.
        
        Tiles are centered at integer positions.  The tile of coordinate (0, 0)
        for example has its center at the position Vector(0, 0).  That's handy.
        
        The tiles borders are at half-integer positions.  The tile (0, 0) is
        limited x = -.5, x = +.5, y = -.5 and y = +5.  When the position is an
        exact half integer, we need to decide on which of the two or four
        possible tiles you stand.  We consider that (-.5, 0) belongs to tile
        (0, 0) but that (.5, 0) belongs to (1, 0).  Tiles start at the half
        integers, and finish just before the next half integers.  This works
        both for x and y.
        
        """
        tile_x = int((.5 + pos.x) // 1)
        tile_y = int((.5 + pos.y) // 1)
        return tile_x, tile_y

    #-------------------------------  Physics.  -------------------------------

    def affectEntityWithTile(self, entity):
        """Apply the effect of tile on which the entity stands."""
        coord = self.tileCoordAt(entity.body.pos)
        try:
            tile_ = self.tile_map.tiles[coord]
        except KeyError:
            friction = 0
        else:
            nature = tile_.nature
            material = tile.MATERIALS[nature]
            friction = material.friction
        entity.friction_force.mu = friction

    def pruneTiles(self, entity):
        """Return the coordinates of the solid tiles near the entity.

        Entities are circles, but I look for the tiles in a rectangular area
        around the entity first.  This function only returns the tiles you have
        to worry about.  Only on these tiles you need to run the full collision
        testing code.

        """
        margin = entity.body.radius
        x, y = entity.body.pos
        # Wow, it took me quite some time to figure out these rules.  I wanted
        # to reduce the tiles to the strict minimum.  The trick is that the
        # half-integer positions are on the edges of tiles (the tiles are
        # centered on integer coordinates).  Now, if x_max = 0.5 it means we
        # have to consider the tiles at x=0 and x=1.  So .5 must be rounded up
        # to 1.  But if x_min = 0.5, we must also consider the tiles at x = 0
        # and x = 1, which means that this time, .5 is rounded down to 0.
        x_min = x - margin # These are all floats: the limits of the entity.
        x_max = x + margin
        y_min = y - margin
        y_max = y + margin
        tile_x_min = int(-((.5 - x_min) // 1)) # These are integers:
        tile_x_max = int((.5 + x_max) // 1)    # Coordinates of the tiles to
        tile_y_min = int(-((.5 - y_min) // 1)) # consider for collisions.
        tile_y_max = int((.5 + y_max) // 1)
        coords = set()
        tiles = self.tile_map.tiles
        for tile_x in range(tile_x_min, tile_x_max + 1):
            for tile_y in range(tile_y_min, tile_y_max + 1):
                try:
                    # Underscore because module with the name "tile".
                    tile_ = tiles[(tile_x, tile_y)]
                except KeyError:
                    pass
                else:
                    if tile_.isSolid():
                        coords.add((tile_x, tile_y))
        return coords

    def detectCollisionsWithTiles(self, collider):
        """Return a set of Collision objects."""
        coords = self.pruneTiles(collider)
        collisions = set()
        for coord in coords:
            tile_nature = self.tile_map.tiles[coord].nature
            material = tile.MATERIALS[tile_nature]
            tile_body = physics.RectangularBody(float('inf'),
                                            geometry.Vector(coord),
                                            material,
                                            1., 1.)
            collision = tile_body.collidesCircle(collider.body)
            if collision:
                collisions.add(collision)
        return collisions

    def detectCollisionsWithEntities(self, collider):
        """Return a set of Collision objects."""
        # Brute force for now: test against all the other entities.
        collisions = set()
        for collidee in self._entities.itervalues():
            if collider is not collidee:
                collision = collidee.body.collidesCircle(collider.body)
                if collision is not None:
                    collisions.add(collision)
        return collisions

    def processCollisions(self, entity):
        """Process the collisions where entity stands.

        All the collisions are computed.

        If no collision, then the entity is sent to new_pos with the velocity
        new_vel.

        If there are collision, then the closest one is chosen and processed.
        The entity is moved the the point resulting from that processing, with
        the resulting velocity.

        """
        collisions = self.detectCollisionsWithTiles(entity)
        collisions |= self.detectCollisionsWithEntities(entity)
        if collisions:
            closest = min(collisions, key=attrgetter('distance'))
            closest.correctPosition()
            closest.correctVelocity()
        else:
            closest = None
        # And this is to stop sending EntityMovedEvent all over the place when
        # the speed is measured in micrometer per century.
        if entity.body.vel.norm() < 0.01:
            entity.body.vel.x = 0
            entity.body.vel.y = 0
        return closest

    def moveEntityByPhysics(self, entity, timestep):
        """Run the physics (integration + collisions) on the given entity.

        This function call call itself (with a smaller timestep)  when the
        entity is too fast.

        """
        body = entity.body
        # First thing to do is move the entity to where it wants to go.
        new_pos, new_vel = entity.body.integrate(timestep)
        if new_pos == body.pos and new_vel.norm() == 0:
            return False
#        LOGGER.info("Entity %i pos=%r, vel=%r.",
#                    entity.entity_id, body.pos, body.vel)
        # Now we must check whether we moved too fast or not.  Moving by more
        # than your radius can make you miss collisions.  So when that happens,
        # we cancel the movement we just did and we use smaller steps.
        # Recursively.
        distance = new_pos.dist(body.pos)
        if distance > body.radius:
            iter_nb = int(math.ceil(distance / body.radius))
            LOGGER.info("Too fast by factor %i.", iter_nb)
            for unused in xrange(iter_nb):
                collision = self.moveEntityByPhysics(entity, timestep / iter_nb)
                if collision:
                    # No need to process the other pieces of the time step: we
                    # already bumped into something.
                    return True
            return False # No collision on any of the time step pieces.
        # Here we are sure that we moved slowly enough.  Time to check for
        # collisions.  We detect the collisions and react to them in order to
        # find a safe place.  But if we can't find a safe place then we cancel
        # everything and we put the entity back where it was.  That's why we
        # store these original values now.
        pos_ori = body.pos
        body.pos = new_pos
        body.vel = new_vel
        attempt = 10
        collision = True # Dummy value to start the loop.
        while attempt and collision:
            collision = self.processCollisions(entity)
            attempt -= 1
        if collision:
            if attempt == 0:
                LOGGER.info("Collision iteration exceeded, "
                            "solved by reverting.")
                body.pos = pos_ori
                body.vel[:] = (0, 0)
        return bool(collision)

    def runPhysics(self, timestep):
        """Compute the physics and apply it."""
        for entity in self._entities.itervalues():
            before = entity.body.pos
            self.moveEntityByPhysics(entity, timestep)
            after = entity.body.pos
            if before != after:
                entity.is_moving = True
                self.post(events.EntityMovedEvent(entity.entity_id, after))
                self.affectEntityWithTile(entity)
            if entity.is_moving:
                if entity.body.vel == geometry.Vector(0, 0):
                    entity.is_moving = False
                    self.post(events.EntityStoppedEvent(entity.entity_id))


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
        """Player wants to create a new entity."""
        self.createEntity()
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
        entity = self._entities[event.entity_id]
        area_id = nextThing(self._areas.keys(), entity.area_id, event.offset)
        self.moveEntityToArea(event.entity_id, area_id)
