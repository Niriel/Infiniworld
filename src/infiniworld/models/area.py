#! /usr/bin/python
"""AreaModel.

"""
from operator import attrgetter
import logging
import math
import weakref

from infiniworld.evtman import SingleListener
import tile
import events
from entitymap import EntityMap
from errors import AlreadyInAreaError
from errors import NotInAreaError
from infiniworld import physics
from infiniworld import geometry

LOGGER = logging.getLogger('world')

def tileCoordAt(pos):
    """Return the coordinate of the tile corresponding to the position.

    Tiles are centered at integer positions.  The tile of coordinate (0, 0) for
    example has its center at the position Vector(0, 0).  That's handy.

    The tiles borders are at half-integer positions.  The tile (0, 0) is
    limited x = -.5, x = +.5, y = -.5 and y = +5.  When the position is an
    exact half integer, we need to decide on which of the two or four possible
    tiles you stand.  We consider that (-.5, 0) belongs to tile (0, 0) but that
    (.5, 0) belongs to (1, 0).  Tiles start at the half integers, and finish
    just before the next half integers.  This works both for x and y.

    """
    tile_x = int((.5 + pos.x) // 1)
    tile_y = int((.5 + pos.y) // 1)
    return tile_x, tile_y

def tileCoordsAround((x, y), radius):
    """Return the coordinates of the tiles around (x, y) in within the radius.
    
    We return a rectangle here, not a circle.
    
    """
    # Wow, it took me quite some time to figure out these rules.  I wanted to
    # reduce the tiles to the strict minimum.  The trick is that the half-
    # integer positions are on the edges of tiles (the tiles are centered on
    # integer coordinates).  Now, if x_max = 0.5 it means we have to consider
    # the tiles at x=0 and x=1.  So .5 must be rounded up to 1.  But if x_min =
    # 0.5, we must also consider the tiles at x = 0 and x = 1, which means that
    # this time, .5 is rounded down to 0.
    x_min = (x - radius) # These are all floats: the limits of the entity.
    x_max = (x + radius)
    y_min = (y - radius)
    y_max = (y + radius)
    tile_x_min = int(-((.5 - x_min) // 1)) # These are integers:
    tile_x_max = int((.5 + x_max) // 1)    # Coordinates of the tiles to
    tile_y_min = int(-((.5 - y_min) // 1)) # consider for collisions.
    tile_y_max = int((.5 + y_max) // 1)
    return tile_x_min, tile_x_max, tile_y_min, tile_y_max


class AreaModel(SingleListener):
    """An area has a tile map, entities, etc..

    An area can represent a town, a dungeon level, the overworld...

    """
    COLLISION_ATTEMPTS = 5
    def __init__(self, event_manager, world, area_id):
        SingleListener.__init__(self, event_manager)
        self.area_id = area_id
        self.world = world
        # Only keep weak references to the entities because they are owned by
        # the World itself, not by the area.  They can move between areas, or
        # even be in no area at all.
        self.entities = weakref.WeakValueDictionary()
        # The tile map is a data structure that describes the fixed features of
        # the landscape.  By fix, I mean that these features cannot move.
        # However, one can imagine that some of these features appear,
        # disappear or change.  For example, a door can open.
        self.tile_map = tile.TileMap()
        # The entity map is here ONLY for performance purposes.  It allows a
        # relatively quick access to the entities in a region.  This helps us
        # limiting the number of entities to look for during collisions, or
        # when a creature is looking around for nearby victims.
        self.entity_map = EntityMap()
        # Useful for collision detection: entities are colliding if the
        # distance between them is smaller than the sum of their radii. Keeping
        # track of the biggest possible radius helps you delimiting the area
        # containing the entities you may be colliding with.  Nothing beyond
        # your_radius + biggest_radius can touch you.
        self._biggest_entity_radius = 0
        LOGGER.debug("Area %i created.", area_id)
    def findBiggestEntityRadius(self):
        """How far we have to look when testing collisions between entities."""
        radius = 0
        for entity in self.entities.itervalues():
            if entity.body.radius > radius:
                radius = entity.body.radius
    def addEntity(self, entity):
        """Add the entity to the area.

        If you are moving the entity from an area to another, you have to take
        care yourself of removing the entity from the first area yourself. Only
        the WorldModel can do that, because it's the only thing that knows both
        areas.

        """
        entity_id = entity.entity_id
        if entity_id in self.entities:
            raise AlreadyInAreaError()
        entity.area = self
        self.entities[entity_id] = entity
        self.affectEntityWithTile(entity)
        self.entity_map.add(entity)
        if entity.body.radius > self._biggest_entity_radius:
            self._biggest_entity_radius = entity.body.radius
        self.post(events.EntityEnteredAreaEvent(entity.makeSummary()))
    def removeEntity(self, entity):
        """Remove the entity from the area."""
        entity_id = entity.entity_id
        try:
            del self.entities[entity_id]
        except KeyError:
            raise NotInAreaError()
        self.entity_map.remove(entity)
        entity.area = None
        self.findBiggestEntityRadius()
        self.post(events.EntityLeftAreaEvent(entity_id, self.area_id))

    #-------------------------------  Physics.  -------------------------------

    def affectEntityWithTile(self, entity):
        """Apply the effect of tile on which the entity stands."""
        coord = tileCoordAt(entity.body.pos)
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
        x_min, x_max, y_min, y_max = tileCoordsAround(entity.body.pos,
                                                      entity.body.radius)
        coords = set()
        tiles = self.tile_map.tiles
        for tile_x in range(x_min, x_max + 1):
            for tile_y in range(y_min, y_max + 1):
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
                                            True,
                                            material,
                                            1., 1.)
            collision = tile_body.collidesCircle(collider.body)
            if collision:
                collisions.add(collision)
        return collisions

    def detectCollisionsWithEntities(self, collider):
        """Return a set of Collision objects."""
        collisions = set()
        entities = self.entity_map.getNear(collider.body.pos,
                                           collider.body.radius +
                                           self._biggest_entity_radius)
        for collidee in entities:
            if not collidee.exists:
                continue
            if collider is not collidee:
                collision = collidee.body.collidesCircle(collider.body)
                if collision is not None:
                    collision.entity = collidee
                    collisions.add(collision)
        return collisions

    def processCollisions(self, entity):
        """Process the collisions where entity stands.

        It computes all the collisions and sorts them by distance.

        It modifies the position and speed according to the closest solid
        collision.

        Return value.
        -------------
        True if collided with a solid entity, False otherwise.

        """
        collidees = []
        if not entity.body.solid:
            # Non solid objects cannot collide anything. BUT they can be
            # collided with.  For example: an item to be picked on the floor.
            # Since the item is not supposed to move we don't care what it
            # collides, however we want other creatures to pick it up.
            return False
        collisions = self.detectCollisionsWithTiles(entity)
        collisions |= self.detectCollisionsWithEntities(entity)
        result = False
        if collisions:
            # Sort the collision by distance.  We reverse the order to make the
            # popping of the closest collision easier.
            collisions = sorted(collisions,
                                key=attrgetter('distance'),
                                reverse=True)
            while collisions:
                collision = collisions.pop()
                if collision.entity:
                    collidees.append(collision.entity)
                if collision.collidee.solid:
                    # Change the position of the collider only so that it
                    # does not collide any more.
                    collision.correctPosition()
                    # Since the position changed, we must update that.
                    self.entity_map.move(entity)
                    # And here we apply the elastic collision formula, which
                    # changes the velocities of the two bodies.
                    collision.correctVelocity()
                    # With all that, the position of the collidee did not
                    # change.  But it may change in the next time step due to
                    # mere integration since its velocity changed.
                    result = True
                    break # Stop at the first collision.
        # And this is to stop sending EntityMovedEvent all over the place when
        # the speed is measured in micrometer per century.
        if entity.body.vel.norm() < 0.01:
            entity.body.vel.zero()
        for collidee in collidees:
            if entity.exists and collidee.exists:
                collidee.reactToCollision(entity)
        return result

    def moveEntityByPhysics(self, entity, timestep):
        """Run the physics (integration + collisions) on the given entity.

        Integration.
        ------------

        The new position and velocity of the entity are computed by integrating
        the equations of motions.

        It is possible that the new position is far away from the original
        position.  This is dangerous because that could cause an entity to
        tunnel through others, missing collisions completely.

        To solve the tunneling we need a smaller time step.  When the new
        position of the entity is more than one entity radius away from the
        start position, then we cancel this move.  Instead, we recursively call
        the current function with a smaller time step as many time as we think
        necessary.

        Collisions.
        -----------

        Thanks to the recursion explained above, we know we won't miss a
        collision.  We must check the new position of the entity for
        collisions.  For that, we call the processCollisions method.  This
        method *detects* the closest collision, if any, and *corrects* the
        position of the entity by pushing the entity back to yet another new
        position.

        This detection-correction cycle must be repeated because that new
        position may also lead to a collision.  Ideally we would repeat this
        indefinitely until we are in a position that does not collide with
        anything.  But in practice it does not work: we can get stuck in an
        endless loop, and even if we don't it takes a lot of CPU time.
        Therefore we put an upper limit to the number of times we process the
        collisions.  An upper limit of 3-5 is enough.  Indeed, if you
        need more, it's clearly because you are totally stuck and unable to
        move anyway.  We call this an unsolvable collision.

        In case of unsolvable collision we cancel the entire move: the entity
        is sent back to its position before the first integration, which is the
        only safe place we know of.  We also set its velocity to 0 so that it
        does not keep getting itself in the same situation at the next physics
        update (of course, in case of forces, it will).

        Return value.
        -------------

        The return value is used for the recursion.  Imagine the entity moves
        too fast.  We need to cut the time step in two and call the method
        twice to compensate.  Now, imagine that after the first call a
        unsolvable collision is detected: then there is no need to do the
        second call since we are stuck anyway.

        The return value is a boolean telling us whether we ended up in an
        unsolvable collision (and had to revert to a safe place) or not.

        """
        body = entity.body
        # First thing to do is to try to move the entity to where it wants to
        # go.  body.integrate does not really modify the position and velocity
        # of the body; it simply returns the position and velocity that the
        # body would have after that integration.
        new_pos, new_vel = body.integrate(timestep)
        if body.pos == new_pos and body.vel == new_vel:
            # Not only the entity did not move, it does not change speed
            # either. Then we are done.  We return False to say that we are not
            # stuck.  That's true since we did not move and we assume we start
            # in a sane position.  Checking the position only is not
            # sufficient: when you are bumping onto a wall, the wall pushes you
            # back to where you are from so your position may not change;
            # however, your velocity has changed because an elastic collision
            # has occurred.
            return False
        # Now we must check whether we moved too fast or not.  Moving by more
        # than your radius can make us miss collisions.  So when that happens,
        # we cancel the movement we just did and we use smaller steps.
        # Recursively.
        distance = new_pos.dist(body.pos)
        if distance > body.radius:
            iter_nb = int(math.ceil(distance / body.radius))
            for unused in xrange(iter_nb):
                stuck = self.moveEntityByPhysics(entity, timestep / iter_nb)
                if stuck:
                    # No need to process the other pieces of the time step: we
                    # are stuck here.
                    return True # or return stuck.
            return False # We ended up in a good position.
        # Here we are sure that we moved slowly enough.  Time to check for
        # collisions.  We detect the collisions and react to them in order to
        # find a safe place.  But if we can't find a safe place then we cancel
        # everything and we put the entity back where it was.  That's why we
        # store these original values now.
        pos_ori = body.pos
        # I need to move the entity now because the collision response modifies
        # the positions and velocities in place.
        body.pos = new_pos
        body.vel = new_vel
        self.entity_map.move(entity)
        attempt = 5
        collided = True # Dummy value to start the loop.
        while attempt and collided:
            collided = self.processCollisions(entity)
            attempt -= 1
        stuck = False
        if collided and attempt == 0:
            # Unsolvable collision!  We're stuck.
            body.pos = pos_ori
            self.entity_map.move(entity)
            body.vel.zero()
            stuck = True
        return stuck

    def runPhysics(self, timestep):
        """Uses physics to move all the entities."""
        for entity in self.entities.itervalues():
            if not entity.exists:
                continue
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


    #--------------------------------  Events.  -------------------------------
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
        if event.area_id == self.area_id:
            entities = [entity.makeSummary()
                         for entity in self.entities.itervalues()]
            tilemap = self.tile_map.makeSummary()
            self.post(events.AreaContentEvent(self.area_id,
                                              entities, tilemap))
    def onRunPhysicsEvent(self, event):
        """The main loop tells us to move our entities."""
        self.runPhysics(event.timestep)
