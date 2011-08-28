#! /usr/bin/python
"""Pictures and fonts for Apocalypse Bunny.

"""
from infiniworld.models import tile
import pygame_

def load():
    """Load all the files needed for the game.
    
    Because it uses pygame.Surface.convert, you should only call that after
    having opened the pygame display.
    
    """
    sprites = ('sprite_blood.png',
               'sprite_bunny_dead.png',
               'sprite_bunny.png',
               'sprite_carrot.png',
               'sprite_fox.png',
               'sprite_heart.png')
    tiles = ('tile_dirt_high.png',
             'tile_dirt.png',
             'tile_grass_high.png',
             'tile_grass.png',
             'tile_sand_high.png',
             'tile_sand.png',
             'tile_stone_high.png',
             'tile_stone.png',
             'tile_water_deep_high.png',
             'tile_water_deep.png',
             'tile_water_shallow_high.png',
             'tile_water_shallow.png')
    pics = pygame_.loadPictures(tiles)
    for key, pic in pics.iteritems():
        pics[key] = pic.convert()
    pygame_.ASSETS_PICS.update(pics)
    #
    pics = pygame_.loadPictures(sprites)
    for key, pic in pics.iteritems():
        pics[key] = pic.convert_alpha()
    pygame_.ASSETS_PICS.update(pics)
    #
    tile_assets = {tile.NATURE_DEEPWATER: 'tile_water_deep.png',
                   tile.NATURE_DIRT: 'tile_dirt.png',
                   tile.NATURE_GRASS: 'tile_grass.png',
                   tile.NATURE_SAND: 'tile_sand.png',
                   tile.NATURE_SHALLOWWATER: 'tile_water_shallow.png',
                   tile.NATURE_STONE: 'tile_stone.png'}
    pygame_.TILE_ASSETS_LOW.update(tile_assets)
    tile_assets = {tile.NATURE_DEEPWATER: 'tile_water_deep_high.png',
                   tile.NATURE_DIRT: 'tile_dirt_high.png',
                   tile.NATURE_GRASS: 'tile_grass_high.png',
                   tile.NATURE_SAND: 'tile_sand_high.png',
                   tile.NATURE_SHALLOWWATER: 'tile_water_shallow_high.png',
                   tile.NATURE_STONE: 'tile_stone_high.png'}
    pygame_.TILE_ASSETS_HIGH.update(tile_assets)
    #
    fonts = pygame_.loadFonts([('pf_tempesta_seven.ttf', 16)])
    pygame_.ASSETS_FONTS.update(fonts)
