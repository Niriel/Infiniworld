#! /usr/bin/python
"""World generators."""
# Standard library.
from __future__ import division

import random
# My stuff.
import infiniworld
import world

def GenerateInterestingTileMap(size, obstacle_density):
    """This generator plants seeds that grow regions on a certain type.  You
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
    natures = infiniworld.models.tile.NATURES_FROM_ID.keys()
    natures.remove(infiniworld.models.tile.NATURE_RUBBER)
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
        tile = infiniworld.models.tile.Tile(nature, height)
        tiles[seed] = tile
    # Now, contaminate the universe.
    while available:
        for seed in list(seeds):
            # I will modify the set `seeds` so I take a copy for this
            # iteration.  Hence the 'list' in the line above.
            seeds.remove(seed)
            nature = tiles[seed].nature
            # All the available tiles around the seed are going to be new
            # seeds.
            around = set(((seed[0] - 1, seed[1] - 1),
                          (seed[0], seed[1] - 1),
                          (seed[0] + 1, seed[1] - 1),
                          (seed[0] - 1, seed[1]),
                          (seed[0] + 1, seed[1]),
                          (seed[0] - 1, seed[1] + 1),
                          (seed[0], seed[1] + 1),
                          (seed[0] + 1, seed[1] + 1)))
            # Sets are wonderful <3.
            around &= available
            seeds |= around
            available -= around
            for seed in around:
                obstacle = random.random()
                height = 1 if obstacle < obstacle_density else 0
                tile = infiniworld.models.tile.Tile(nature, height)
                tiles[seed] = tile
    # Center is low.
    for x in xrange(-1, 2):
        for y in xrange(-1, 2):
            if (x, y) in tiles:
                tiles[(x, y)].height = 0
    # Borders are high.
    for x in xrange(min_x, max_x + 1):
        tiles[(x, min_y)].height = 1
        tiles[(x, max_y)].height = 1
    for y in xrange(min_y, max_y + 1):
        tiles[(min_x, y)].height = 1
        tiles[(max_x, y)].height = 1
    #
    tile_map = infiniworld.models.tile.TileMap(tiles)
    return tile_map

def GenerateWorld(event_manager, area_size):
    """Procedural generation, woohoo !"""
    world_model = infiniworld.models.WorldModel(event_manager)
    area_model = world_model.createArea()
    tile_map = GenerateInterestingTileMap(area_size, .2)
    coords = set([coord
                  for coord, tile_ in tile_map.tiles.iteritems()
                  if tile_.height == 0])
    area_model.tile_map = tile_map
    # Place the bunny: the player character.
    creature = world_model.createEntity(world.BunnyModel)
    creature.body.pos = infiniworld.geometry.Vector()
    world_model.moveEntityToArea(creature.entity_id, area_model.area_id)
    # Monster and carrot spawners.
    fox_spawner = world.SpawnerModel(event_manager)
    fox_spawner.area = area_model
    fox_spawner.coords = coords
    fox_spawner.factory = world.ZombieFoxModel
    fox_spawner.period = 3
    #
    carrot_spawner = world.SpawnerModel(event_manager)
    carrot_spawner.area = area_model
    carrot_spawner.coords = coords
    carrot_spawner.factory = world.CarrotModel
    carrot_spawner.period = 10
    #    
    return world_model, fox_spawner, carrot_spawner
