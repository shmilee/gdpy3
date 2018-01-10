# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

import os

from ..glogger import getGLogger

__all__ = ['get_plotter']
log = getGLogger('P')

plotter_names = ['MatplotlibPlotter']
plotter_types = ['mpl::', 'matplotlib::']

def get_plotter(name):
    '''
    Given a str *name*, return a plotter instance.

    The name must start with one type of ``plotter_types``,
    for example 'mpl::any-string-here'.
    Raises ValueError if name invalid or type not supported.
    '''
    sep = '::'
    name = str(name)
    if name.find(sep) > 0:
        ptype = name.split(sep=sep)[0] + sep
        if ptype in ('mpl::', 'matplotlib::'):
            from .mplplotter import MatplotlibPlotter
            plotter = MatplotlibPlotter(name)
        else:
            raise ValueError('Unsupported plotter type: "%s"! '
                             'Did you mean one of: "%s"?'
                             % (ptype, ', '.join(plotter_types)))
    else:
        raise ValueError('Invalid name: "%s"! '
                         'Name must start with one type of: "%s".'
                         % (name,', '.join(plotter_types)))
    return plotter
