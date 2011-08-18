#! /usr/bin/python
"""

"""
import collections

Material = collections.namedtuple('Material', ('friction', 'eff_n', 'eff_t'))

MATERIAL_STONE = Material(-100, .9, 1.0)
MATERIAL_DIRT = Material(-150, .8, 1.0)
MATERIAL_GRASS = Material(-200, .3, 1.0)
MATERIAL_SAND = Material(-200, .1, 1.0)
MATERIAL_SHALLOWWATER = Material(-400, 0., 1.0)
MATERIAL_DEEPWATER = Material(-800, 0., 1.0)
MATERIAL_RUBBER = Material(-100, 1., 1.0)
MATERIAL_FLESH = Material(-150, .7, 1.0)
