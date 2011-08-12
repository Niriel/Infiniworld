"""World generators."""

import random
import world

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
        tile_map = GenerateTileMap(area_size, .2)
        area_model.tile_map = tile_map
    return world_model
