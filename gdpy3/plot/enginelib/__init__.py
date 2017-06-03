# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r'''
    plot engines
'''

import logging
from .mplwrapper import mplengine

__all__ = ['engine_available', 'get_engine']

log = logging.Logger('gdp')

engine_available = [
    'mpl', 'matplotlib',
]
default_engine = 'matplotlib'


def get_engine(name):
    '''
    Return a Engine instance by name
    '''

    if name not in engine_available:
        log.error("Plot engine '%s' not found in '%s'! Use default '%s'!"
                  % (name, engine_available, default_engine))
        name = default_engine
    if name in ('mpl', 'matplotlib'):
        log.debug("Use plot engine 'matplotlib'.")
        return mplengine
    else:
        pass
