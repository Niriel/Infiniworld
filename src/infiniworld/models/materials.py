#! /usr/bin/python
"""Describes the physical properties of the various materials in the game.

"""
import collections

Material = collections.namedtuple('Material', ('friction', 'eff_n', 'eff_t'))

MATERIAL_STONE = Material(-4, .9, 1.0)
MATERIAL_DIRT = Material(-5, .8, 1.0)
MATERIAL_GRASS = Material(-6, .3, 1.0)
MATERIAL_SAND = Material(-6, .1, 1.0)
MATERIAL_SHALLOWWATER = Material(-8, 0., 1.0)
MATERIAL_DEEPWATER = Material(-10, 0., 1.0)
MATERIAL_RUBBER = Material(-5, 1., 1.0)
MATERIAL_FLESH = Material(-5, .7, 1.0)
