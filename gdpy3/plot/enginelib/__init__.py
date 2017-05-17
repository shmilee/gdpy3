# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r'''
    plot engines
'''

import logging

__all__ = ['mplwrapper']

log = logging.Logger('gdp')


def get_figure_factory(engine):
    if engine in ('mpl', 'matplot', 'matplotlib'):
        log.debug("Use plot-engine 'matplotlib'.")
        from .mplwrapper import mplfigure_factory
        return mplfigure_factory
    else:
        log.error("Plot-engine '%s' not found!" % engine)
        return None
