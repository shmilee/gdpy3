# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r'''
    This is the subpackage ``plot`` of package gdpy3.
'''

__all__ = ['pick', 'GCase']

import os
import sys
import logging

from .. import read as gdr
from .gcase import GCase
from .enginelib import engine_available, style_available

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    # format='[%(asctime)s %(name)s] %(levelname)s - %(message)s',
    # datefmt='%Y-%m-%d %H:%M:%S',
    format='[%(name)s]%(levelname)s - %(message)s'
)

log = logging.getLogger('gdp')


def pick(path, default_enable=[], figurestyle=['gdpy3-notebook'], **kwargs):
    '''
    Pick up GTC data in *path*, get a GTC case.
    Return an GCase object which contains all figures, calculations.

    Parameters
    ----------
    path: str
        path of the .npz, .hdf5 file to open
        or path of the directory of GTC .out files
    default_enable, figurestyle:
        parameters for :class:`gdpy3.plot.gcase.GCase`
    '''
    try:
        dataobj = gdr.read(path)
    except Exception:
        log.error("Failed to read path '%s'!" % path)
        raise

    try:
        case = GCase(dataobj, default_enable, figurestyle)
    except Exception:
        log.error("Failed to get 'GCase' object!")
        raise
    else:
        return case
