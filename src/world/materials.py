#! /usr/bin/python
"""

"""
import collections

Material = collections.namedtuple('Material', ('friction', 'eff_n', 'eff_t'))

MATERIAL_STONE = Material(-100, .9, .8)
MATERIAL_DIRT = Material(-150, .8, .8)
MATERIAL_GRASS = Material(-200, .3, .8)
MATERIAL_SAND = Material(-200, .1, .8)
MATERIAL_SHALLOWWATER = Material(-400, 0., .5)
MATERIAL_DEEPWATER = Material(-800, 0., .5)
MATERIAL_RUBBER = Material(-100, 1., .1)
# Rubber is probably the material with the highest friction coefficient.
# However, we use Friction here as a mean to slow down moving entities, and
# these don't slide, they walk, so they're not slowed down, that's why I put
# only 100.  However, rub yourself on a rubber wall, you don't go far, that's
# why the tangential efficiency is .1. I think this is messy, I will rethink
# that.
MATERIAL_FLESH = Material(-150, .7, .6)
