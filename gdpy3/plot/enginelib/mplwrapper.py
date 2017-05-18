# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r'''
A simple wrapper for matplotlib used to plot simple figure.
'''

import logging
from matplotlib import style
from matplotlib.pyplot import figure
from matplotlib.axes._axes import Axes
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.gridspec import SubplotSpec

__all__ = ['mplfigure_factory']

log = logging.getLogger('gdp')


Default_FigureStructure = {
    'Style': [{'figure.figsize': (8, 6), 'figure.dpi': 100}],
    'AxesStructures': [{'Default_AxesStructure'}, {'Must set dict'}],
}

Default_AxesStructure = {
    'data': [
        [1, 'plot', ('xarray', 'yarray', 'ro-'), {'label': 'line default'}],
        ['int', 'Axes plot func', ("args",), {"kwargs, such as 'label'"}],
    ],
    'layout': ['int, grid or list', {'add_subplot or add_axes kwargs'}],
    'style': [{'axes.grid': True}],
    'revise': 'revise_function(fig, ax)',
}


def mplfigure_factory(figurestructure, num=None):
    '''
    Return a matplotlib.figure.Figure instance.

    Parameters
    ==========
    figurestructure: dict
        all objects you need to plot a figure
    num: integer or string, optional, default: none
        pass this into function matplotlib.pyplot.figure

    Notes
    =====
    1. The figurestructure dict has 2 keys: 'Style' and 'AxesStructures'.
       'Style' is optional.
    2. Value of 'Style' is a list of mplstyles, and valid elements can be
       available style names in `style.available`, dict with valid key,
       value pairs for `matplotlib.rcParams`, or a path to a style file.
       Default: [{'figure.figsize': (8, 6), 'figure.dpi': 100}]
    3. Value of 'AxesStructures' is a list of `AxesStructure`. Each
       `AxesStructure` is a dict has 4 keys: 'data', 'layout', 'style'
       and 'revise'. 'style' and 'revise' are optional.
    3.1. Value of 'data' is a list of line_list. line_list[0] is an order
         number. line_list[1] is the name of a function attribute of
         :class:`matplotlib.axes._axes.Axes`. It can be any plot function,
         such as 'contour', 'fill', 'imshow', 'pcolor', 'plot', etc.
         line_list[2] is a tuple of args for plot function, such as
         xarray, yarray, 'ro-'. line_list[3] is a dict of kwargs
         for plot function, such as {'label': 'a line', 'linewidth': 2}.
    3.2. Value of 'layout' is a list of 2 elements. layout[0] is
         a position rect list for matplotlib.figure.Figure.add_axes, or
         a three digit number for matplotlib.figure.Figure.add_subplot, or
         a instance of :class:`matplotlib.gridspec.GridSpec`. layout[1] is
         a dict of kwargs for Figure.add_axes or Figure.add_subplot.
    3.3. Value of 'style' is a list of mplstyles. The style will
         only affect this axes except others.
         Default: [{'axes.grid': True}]
    3.4. Value of 'revise' is an optional function to revise the axes.
         It accepts two parameters: this figure, and this axes.
    4. If you want to plot 3D figure, such as 'plot3D', 'plot_surface',
       in :class:`mpl_toolkits.mplot3d.axes3d.Axes3D`.
       First, add projection='3d' to layout[1].
       Then, set line_list[1] to the plot function.
    '''

    if not isinstance(figurestructure, dict):
        raise ValueError("FigureStructure must be a dict. " +
                         "Not %s." % type(figurestructure))
    figstyle = Default_FigureStructure['Style']
    if 'Style' in figurestructure:
        if isinstance(figurestructure['Style'], list):
            figstyle = figstyle + _filter_styles(figurestructure['Style'])
        else:
            log.error("FigureStructure['Style'] must be a list. " +
                      "Not %s. " % type(figurestructure['Style']) +
                      "Ignore 'Style' setting!")
    if not isinstance(figurestructure['AxesStructures'], list):
        raise ValueError("FigureStructure['AxesStructures'] must be a list. "
                         "Not %s." % type(figurestructure['AxesStructures']))
    log.debug("Figure Style: %s" % str(figstyle))
    with style.context((figstyle)):
        fig = figure(num=num)
        for i, axstructure in enumerate(figurestructure['AxesStructures'], 1):
            log.debug("Picking AxesStructure %d ..." % i)
            _mplaxes_factory(fig, axstructure)
    return fig


def _mplaxes_factory(fig, axstructure):
    '''
    Add axes to figure.

    Parameters
    ==========
    fig: `matplotlib.figure.Figure` instance
    axstructure: `AxesStructure` dict
    '''

    # simple check
    for k in ('data', 'layout'):
        if k not in axstructure:
            log.error("AxesStructure must contain key: '%s'!" % k)
            log.debug("Ignore this axes.")
            return
        if not isinstance(axstructure[k], list):
            log.error("AxesStructure[%s] must be a list. " % k +
                      "Not %s." % type(axstructure[k]))
            log.debug("Ignore this axes.")
            return
    # check layout
    layout = axstructure['layout']
    if not(isinstance(layout, list) and len(layout) == 2):
        log.error("AxesStructure['layout'] must be a two elements list.")
        log.debug("Ignore this axes.")
        return
    if not isinstance(layout[0], (int, list, SubplotSpec)):
        log.error("AxesStructure['layout'][0] must be a "
                  "int, list or SubplotSpec.")
        log.debug("Ignore this axes.")
        return
    # check style
    axstyle = Default_AxesStructure['style']
    if 'style' in axstructure:
        if isinstance(axstyle, list):
            axstyle = axstyle + _filter_styles(axstructure['style'])
        else:
            log.error("AxesStructure['style'] must be a list. " +
                      "Not %s. " % type(axstructure['style']) +
                      "Ignore 'style' setting!")
    # begin with style
    log.debug("Axes Style: %s" % str(axstyle))
    with style.context(axstyle):
        # use layout
        try:
            log.debug("Adding axes %s ..." % layout[0])
            if isinstance(layout[0], list):
                ax = fig.add_axes(layout[0], **layout[1])
            else:
                ax = fig.add_subplot(layout[0], **layout[1])
        except Exception as exc:
            log.error("Failed to add axes %s: %s" % (layout[0], exc))
            return
        # use data
        for index, plotfunc, dataargs, datakwargs in axstructure['data']:
            try:
                log.debug("Adding artist %s ..." % index)
                plotfunc = getattr(ax, plotfunc)
                plotfunc(*dataargs, **datakwargs)
            except Exception as exc:
                log.error("Failed to add artist %s: %s" % (index, exc))
        # optional revise function
        if 'revise' in axstructure:
            try:
                log.debug("Revising axes %s ..." % layout[0])
                axstructure['revise'](fig, ax)
            except Exception as exc:
                log.error("Failed to revise axes %s: %s" % (layout[0], exc))


def _filter_styles(mplstyles):
    '''
    Check the mplstyles available or not.
    Accept a list.
    Return a list.
    '''
    validstyles = []
    for st in mplstyles:
        try:
            with style.context(st):
                pass
            validstyles.append(st)
        except Exception as exc:
            log.error("Ignore style '%s': %s" % (st, exc))
    return validstyles
