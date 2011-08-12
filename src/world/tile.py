#! /usr/bin/python
"""Tiles are the elements of landscape.

A tile covers an entire 1 by 1 meter surface.  So a boulder is not a tile,
a boulder is ON a tile.

"""

# Natural.
NATURE_STONE = 0
NATURE_DIRT = 1
NATURE_GRASS = 2
NATURE_SAND = 3
NATURE_SHALLOWWATER = 4
NATURE_DEEPWATER = 5

NATURES_FROM_NAME = {}
NATURES_FROM_ID = {}
for _name, _value in globals().items():
    if _name.startswith('NATURE_'):
        _name = _name[7:]
        NATURES_FROM_NAME[_name] = _value
        NATURES_FROM_ID[_value] = _name

# pylint: disable-msg=R0903
# Too few public methods.  Well, that's a dumb container, so yeah.
class Tile(object):
    """The piece of landscape in that 1 by 1 meter square."""
    def __init__(self, nature, height):
        """Initializes a new Tile object.
        
        `nature`: constant such as STONE_FLOOR.
        `height`: 0 for floor, 1 for wall.
        
        Since the game is 2D, anything with a height of 1 is unwalkable.
        
        """
        object.__init__(self)
        self.nature = nature
        self.height = height
    def __repr__(self):
        nature = 'NATURE_%s' % NATURES_FROM_ID[self.nature]
        return "%s(%s, %i)" % (self.__class__.__name__, nature, self.height)
    def makeSummary(self):
        """Serialization-friendly data for passing around in events."""
        return (self.nature, self.height)
# pylint: enable-msg=R0903


class TileMap(object):
    """A collection of tiles make a tile map."""
    def __init__(self, tiles=None):
        self.tiles = {} if tiles is None else tiles
    def makeSummary(self):
        """Serialization-friendly data for passing around in events."""
        summary = {}
        for coord, tile in self.tiles.iteritems():
            summary[coord] = tile.makeSummary()
        return summary
