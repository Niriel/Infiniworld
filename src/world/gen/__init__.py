"""World generators."""
from __future__ import division
import random
import world

def GenerateInterestingTileMap(size, obstacle_density):
    """Better generator than the other one.
    
    This generator plants seeds that grow regions on a certain type.  You
    end up with big patches of the same.
    
    """
    min_x = -size[0] // 2
    max_x = min_x + size[0] - 1
    min_y = -size[1] // 2
    max_y = min_x + size[1] - 1
    available = set(((x, y)
                     for x in xrange(min_x, max_x + 1)
                     for y in xrange(min_y, max_y + 1))
                    )
    natures = world.tile.NATURES_FROM_ID.keys()
    tiles = {}
    seeds = set()
    seeds_nb = size[0] * size[1] // 100
    for unused in range(seeds_nb):
        # I need to make a list because random.choice doesn't work on sets:
        # sets don't support indexing.
        seed = random.choice(list(available))
        available.remove(seed)
        seeds.add(seed)
        nature = random.choice(natures)
        obstacle = random.random()
        height = 1 if obstacle < obstacle_density else 0
        tile = world.tile.Tile(nature, height)
        tiles[seed] = tile
    # Now, contaminate the universe.
    while available:
        for seed in list(seeds):
            # I will modify the set `seeds` so I take a copy for this
            # iteration.
            seeds.remove(seed)
            nature = tiles[seed].nature
            # All the available tiles around the seed are going to be new
            # seeds.
            around = {(seed[0] - 1, seed[1] - 1),
                      (seed[0], seed[1] - 1),
                      (seed[0] + 1, seed[1] - 1),
                      (seed[0] - 1, seed[1]),
                      (seed[0] + 1, seed[1]),
                      (seed[0] - 1, seed[1] + 1),
                      (seed[0], seed[1] + 1),
                      (seed[0] + 1, seed[1] + 1)}
            around &= available
            seeds |= around
            available -= around
            for seed in around:
                obstacle = random.random()
                height = 1 if obstacle < obstacle_density else 0
                tile = world.tile.Tile(nature, height)
                tiles[seed] = tile
    tile_map = world.tile.TileMap(tiles)
    return tile_map

def GenerateTileMap(size, obstacle_density):
    """Procedural generation, woohoo !"""
    natures = world.tile.NATURES_FROM_ID.keys()
    tiles = {}
    size_x, size_y = size
    for x in xrange(size_x):
        for y in xrange(size_y):
            floor = random.choice(natures)
            obstacle = random.random()
            height = 1 if obstacle < obstacle_density else 0
            tile = world.tile.Tile(floor, height)
            tiles[(x - size_x // 2, y - size_y // 2)] = tile
    tile_map = world.tile.TileMap(tiles)
    return tile_map

def GenerateWorld(event_manager, areas_nb, area_size):
    """Procedural generation, woohoo !"""
    world_model = world.WorldModel(event_manager)
    for unused in xrange(areas_nb):
        area_model = world_model.createArea()
        tile_map = GenerateInterestingTileMap(area_size, .2)
        area_model.tile_map = tile_map
    return world_model
