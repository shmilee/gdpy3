# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
This is the subpackage ``plotters`` of gdpy3.
``plotter``, get by :func:`get_plotter`, has attributes
:attr:`base.BasePlotter.name`,
:attr:`base.BasePlotter.style_available`,
:attr:`base.BasePlotter.style`,
:attr:`base.BasePlotter.figures`,
:attr:`base.BasePlotter.example_axes`
and methods
:meth:`base.BasePlotter.check_style`,
:meth:`base.BasePlotter.filter_style`,
:meth:`base.BasePlotter.param_from_style`,
:meth:`base.BasePlotter.add_axes`,
:meth:`base.BasePlotter.create_figure`,
:meth:`base.BasePlotter.get_figure`,
:meth:`base.BasePlotter.show_figure`,
:meth:`base.BasePlotter.close_figure`,
:meth:`base.BasePlotter.save_figure`,
'''

from . import base

__all__ = ['get_plotter']

plotter_names = ['MatplotlibPlotter']
plotter_types = ['mpl::']


def get_plotter(name):
    '''
    Given a str *name*, return a plotter instance.

    The name must start with one type of ``plotter_types``,
    for example 'mpl::any-string-here'.
    Raises ValueError if name invalid or type not supported.

    Notes
    -----
    plotter types:
    1. 'mpl::' for :class:`mplplotter.MatplotlibPlotter`.
    '''
    sep = '::'
    name = str(name)
    if name.find(sep) > 0:
        ptype = name.split(sep=sep)[0] + sep
        if ptype == 'mpl::':
            from .mplplotter import MatplotlibPlotter
            plotter = MatplotlibPlotter(name)
        else:
            raise ValueError('Unsupported plotter type: "%s"! '
                             'Did you mean one of: "%s"?'
                             % (ptype, ', '.join(plotter_types)))
    else:
        raise ValueError('Invalid name: "%s"! '
                         'Name must start with one type of: "%s".'
                         % (name, ', '.join(plotter_types)))
    return plotter


def is_plotter(obj):
    '''
    Return True if obj is a plotter instance, else return False.
    '''
    return isinstance(obj, base.BasePlotter)
