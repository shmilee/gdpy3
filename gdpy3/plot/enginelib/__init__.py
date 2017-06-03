# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r'''
    plot engines
'''

import logging
from .mplwrapper import mplfigure_factory, mplstyle_available

__all__ = ['engine_available', 'get_figure_factory', 'get_style_available']

log = logging.Logger('gdp')

engine_available = [
    'mpl', 'matplotlib',
]
default_engine = 'matplotlib'


def get_figure_factory(engine):
    if engine not in engine_available:
        log.error("Plot engine '%s' not found in '%s'! Use default '%s'!"
                  % (engine, engine_available, default_engine))
        engine = default_engine
    if engine in ('mpl', 'matplotlib'):
        log.debug("Use plot engine 'matplotlib'.")
        return mplfigure_factory
    else:
        pass

def get_style_available(engine):
    if engine not in engine_available:
        log.error("Plot engine '%s' not found in '%s'!"
                  % (engine, engine_available))
        return []
    if engine in ('mpl', 'matplotlib'):
        log.debug("Use plot engine 'matplotlib'.")
        return mplstyle_available
    else:
        pass

