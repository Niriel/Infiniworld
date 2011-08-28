#! /usr/bin/python
"""Tell the game where to find its stuff.

"""
import sys
import os

DIR_BIN = os.path.dirname(sys.argv[0])
DIR_BASE = os.path.abspath(os.path.join(DIR_BIN, '..'))
DIR_DOC = os.path.join(DIR_BASE, 'doc')
DIR_ETC = os.path.join(DIR_BASE, 'etc')
DIR_LIB = os.path.join(DIR_BASE, 'src')
DIR_SHARE = os.path.join(DIR_BASE, 'share')
DIR_VAR = os.path.join(DIR_BASE, 'var')
DIR_VAR_LOG = os.path.join(DIR_VAR, 'log')
DIR_VAR_SAV = os.path.join(DIR_VAR, 'saves')
DIR_VAR_SCR = os.path.join(DIR_VAR, 'screenshots')
DIR_TMP = os.path.join(DIR_BASE, 'tmp')
