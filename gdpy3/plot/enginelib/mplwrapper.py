# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r'''
A simple wrapper for matplotlib used to plot simple figure.
'''

import os
import logging
from matplotlib import style
from matplotlib import rcParams
from matplotlib.pyplot import figure, close
from matplotlib.axes._axes import Axes
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.gridspec import SubplotSpec

from .base import Engine

__all__ = ['mplengine']

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
    if 'Style' in figurestructure:
        if isinstance(figurestructure['Style'], list):
            figstyle = _check_styles(figurestructure['Style'])
        else:
            log.error("FigureStructure['Style'] must be a list. " +
                      "Not %s. " % type(figurestructure['Style']) +
                      "Ignore 'Style' setting!")
    if 'figstyle' not in dir() or not figstyle:
        figstyle = Default_FigureStructure['Style']
    if not isinstance(figurestructure['AxesStructures'], list):
        raise ValueError("FigureStructure['AxesStructures'] must be a list. "
                         "Not %s." % type(figurestructure['AxesStructures']))
    log.debug("Figure Style: %s" % str(figstyle))
    with style.context(_filter_styles(figstyle)):
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
    if 'style' in axstructure:
        if isinstance(axstructure['style'], list):
            axstyle = _check_styles(axstructure['style'])
        else:
            log.error("AxesStructure['style'] must be a list. " +
                      "Not %s. " % type(axstructure['style']) +
                      "Ignore 'style' setting!")
    if 'axstyle' not in dir() or not axstyle:
        axstyle = Default_AxesStructure['style']
    # begin with style
    log.debug("Axes Style: %s" % str(axstyle))
    with style.context(_filter_styles(axstyle)):
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


STYLE_LIBRARY_PATH = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'mpl-stylelib')
mplstyle_available = style.available.copy()


def _update_gdpy3_mplstyle_library():
    global mplstyle_available
    for path, name in style.core.iter_style_files(STYLE_LIBRARY_PATH):
        mplstyle_available.append(name)
_update_gdpy3_mplstyle_library()


def _check_styles(mplstyles):
    '''
    Check the mplstyles available or not.
    Accept a list.
    Return a list.
    '''
    validstyles = []
    for st in mplstyles:
        if st in mplstyle_available:
            validstyles.append(st)
            continue
        try:
            with style.context(st):
                pass
            validstyles.append(st)
        except Exception as exc:
            log.error("Ignore style '%s': %s" % (st, exc))
    return validstyles


def _filter_styles(mplstyles):
    '''
    Filter the mplstyle in *mplstyles*.
    If the name starts with 'gdpy3-', change it to absolute path.
    Accept a list of mplstyle.
    Return a list.
    '''
    validstyles = []
    for st in mplstyles:
        if isinstance(st, str) and st.startswith('gdpy3-'):
            validstyles.append(
                os.path.join(STYLE_LIBRARY_PATH, st + '.mplstyle'))
        else:
            validstyles.append(st)
    return validstyles


def mplclose(fig):
    '''
    Close the figure *fig*.
    '''
    close(fig)

mplengine = Engine('matplotlib')
mplengine.figure_factory = mplfigure_factory
mplengine.style_available = mplstyle_available
mplengine.close = mplclose


# tool functions

def get_mplstyle_param(mplstyle, param):
    '''
    Return param value from mplstyle
    '''
    if isinstance(mplstyle, str) or hasattr(mplstyle, 'keys'):
        mplstyle = [mplstyle]
    if param in rcParams:
        with style.context(_filter_styles(_check_styles(mplstyle))):
            return rcParams[param]
    else:
        log.error("Invalid param '%s' for matplotlib.rcParams!" % param)
        return None


def get_mplcolorbar_revise_func(label, grid_alpha=0.3, **kwargs):
    '''
    Return a colorbar `revise function` for FigureStructure.

    Parameters
    ----------
    label: label of mappable which the colorbar applies
    keyword arguments: kwargs passed to colorbar
        *cax*, *ax*, *fraction*, *pad*, *ticks*, etc.
    '''
    def revise_func(figure, axes):
        axes.grid(alpha=grid_alpha)
        mappable = None
        for child in axes.get_children():
            if child.get_label() == label:
                mappable = child
        if mappable:
            figure.colorbar(mappable, **kwargs)
    return revise_func

mplengine.tool = {
    'get_style_param': get_mplstyle_param,
    'get_colorbar_revise_func': get_mplcolorbar_revise_func,
}
