#! /usr/bin/python
"""Space partitioning of the entities in an area.  For performance purposes.

"""
from __future__ import division

def chunkCoordAt(pos, scale):
    """Return the coordinate of the chunk corresponding to the position.

    A chunk is made of scale*scale tiles.

    Chunk are centered at integer positions.  The chunk of coordinate (0, 0)
    for example has its center at the position Vector(0, 0).  That's handy.

    The chunk borders are at half-integer positions.  The chunk (0, 0) is
    limited x = -.5, x = +.5, y = -.5 and y = +5.  When the position is an
    exact half integer, we need to decide on which of the two or four possible
    chunks you stand.  We consider that (-.5, 0) belongs to chunk (0, 0) but
    that (.5, 0) belongs to (1, 0).  Chunks start at the half integers, and
    finish just before the next half integers.  This works both for x and y.

    """
    chunk_x = int((.5 + pos.x / scale) // 1)
    chunk_y = int((.5 + pos.y / scale) // 1)
    return chunk_x, chunk_y

def chunkCoordsAround((x, y), radius, scale):
    """Return the coords of the chucks around (x, y) within the radius."""
    # Wow, it took me quite some time to figure out these rules.  I wanted to
    # reduce the chunks to the strict minimum.  The trick is that the half-
    # integer positions are on the edges of chunks (the chunks are centered on
    # integer coordinates).  Now, if x_max = 0.5 it means we have to consider
    # the chunks at x=0 and x=1.  So .5 must be rounded up to 1.  But if x_min
    # = 0.5, we must also consider the chunks at x = 0 and x = 1, which means
    # that this time, .5 is rounded down to 0.
    x_min = (x - radius) / scale # These are all floats: limits of the entity.
    x_max = (x + radius) / scale
    y_min = (y - radius) / scale
    y_max = (y + radius) / scale
    # I could call chuckCoordAt here but we would lose speed.
    chunk_x_min = int(-((.5 - x_min) // 1)) # These are integers:
    chunk_x_max = int((.5 + x_max) // 1)    # Coordinates of the chunks to
    chunk_y_min = int(-((.5 - y_min) // 1)) # consider for collisions.
    chunk_y_max = int((.5 + y_max) // 1)
    return chunk_x_min, chunk_x_max, chunk_y_min, chunk_y_max


class EntityMap(object):
    """Keep track of which chunk the entities are on, to speed up search."""
    # I first wanted to use weak references.  However it's bad for performance.
    # The getNear function is called super often.  Replacing the
    # weakdictionary and weakset with normal dictionary and set makes the
    # method run in 75% of its previous time.  I don't know what I should do:
    # stick to weakrefs by principle, or use 'strong' refs?  I sort of have the
    # feeling that here, strong refs is more error prone.  Indeed, if I forget
    # to remove an entity from this map then I may see strange behaviors. So
    # I'll use them.

    # Another thing I did for the performance is to introduce the scale factor
    # and the notion of chunk.  It's MUCH faster to check 4 chunks of 8*8 tiles
    # than 16*16 = 256 tiles (most of which don't contain any entity anyway).
    def __init__(self):
        object.__init__(self)
        self._entities = {}
        self._coords = {} #weakref.WeakKeyDictionary()
        self.scale = 8
    def getAt(self, coord):
        """Return a set of the entities at the given chunk coordinates."""
        try:
            entity_set = self._entities[coord]
        except KeyError:
            entity_set = set() #weakref.WeakSet()
            self._entities[coord] = entity_set
        return entity_set
    def add(self, entity):
        """Add the entity to the tile corresponding to its position.

        Warning: it does not remove that entity from another tile.  For that,
        use move.

        """
        coord = chunkCoordAt(entity.body.pos, self.scale)
        self.getAt(coord).add(entity)
        self._coords[entity] = coord
    def remove(self, entity):
        """Remove the entity from the tile corresponding to its position."""
        coord = self._coords[entity]
        entities = self.getAt(coord)
        entities.remove(entity)
        if not entities:
            del self._entities[coord]
        del self._coords[entity]
    def move(self, entity):
        """Remove the entity from the tile at old_pos and add it to its pos.

        The current position of the entity is used.  So make sure to call this
        method AFTER setting the position of your entity.

        """
        old_coord = self._coords[entity]
        new_coord = chunkCoordAt(entity.body.pos, self.scale)
        if old_coord != new_coord:
            entities = self.getAt(old_coord)
            entities.remove(entity)
            if not entities:
                del self._entities[old_coord]
            self.getAt(new_coord).add(entity)
            self._coords[entity] = new_coord
    def getNear(self, pos, radius):
        """Used for pruning entities in a collision, for instance.

        A square area is examined around the position `pos`, plus or minus
        `radius` in x and y.  All world coordinates.

        All the tiles covered by that definitions are examined for entities.

        All the found entities are returned in a set.

        """
        x_min, x_max, y_min, y_max = chunkCoordsAround(pos, radius, self.scale)
        result = set()
        for x in xrange(x_min, x_max + 1):
            for y in xrange(y_min, y_max + 1):
                result.update(self.getAt((x, y)))
        return result
