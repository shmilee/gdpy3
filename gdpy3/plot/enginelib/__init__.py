# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
    plot engines
'''

from .mplwrapper import mplengine, log

__all__ = ['engine_available', 'get_engine']

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
        log.ddebug("Use plot engine 'matplotlib'.")
        return mplengine
    else:
        pass


def style_available(engine=default_engine):
    '''
    Return a list of available styles in Engine *engine*.
    '''
    if engine not in engine_available:
        log.error("Plot engine '%s' not found in '%s'!"
                  % (engine, engine_available))
        return []
    if engine in ('mpl', 'matplotlib'):
        return mplengine.style_available
    else:
        pass
