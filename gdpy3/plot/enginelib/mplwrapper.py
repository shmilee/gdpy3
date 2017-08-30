# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
A simple wrapper for matplotlib used to plot simple figure.
'''

import os
from matplotlib import style, rcParams, get_backend
from matplotlib.pyplot import figure, close
from matplotlib.axes._axes import Axes
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.gridspec import SubplotSpec

from .base import Engine, log

__all__ = ['mplengine']


Default_FigureStructure = {
    'Style': [{'figure.figsize': (8, 6), 'figure.dpi': 100}],
    'AxesStructures': [{'Default_AxesStructure'}, {'Must set dict'}],
}

Default_AxesStructure = {
    'data': [
        [int, 'Axes plot func', ("args",), {"kwargs, such as 'label'"}],
        [1, 'plot', ('xarray', 'yarray', 'ro-'), {'label': 'line default'}],
        [2, 'twinx or twiny', (), dict(nextcolor='int')],
        [int, 'revise', lambda fig, axesdict, artistdict: print(fig), dict()],
    ],
    'layout': ['int, grid or list', {'add_subplot or add_axes kwargs'}],
    'style': [{'axes.grid': True}],
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
       `AxesStructure` is a dict has 3 keys: 'data', 'layout' and 'style'.
       'style' is optional.

       a. Value of 'data' is a list of method_list.
          method_list[0] is an order number. method_list[1] is the name of
          a method of :class:`matplotlib.axes._axes.Axes`. It can be any
          plot function, such as 'contour', 'fill', 'imshow', 'pcolor',
          'plot', etc. method_list[2] is a tuple of args for plot function,
          such as xarray, yarray, 'ro-'. method_list[3] is a dict of kwargs
          for plot function, such as {'label': 'a line', 'linewidth': 2}.

          When method_list[1] is 'twinx' or 'twiny', 'nextcolor' can be set
          in method_list[3] to correct the color order.

          method_list[1] can also be 'revise'. In this situation,
          method_list[2] is a function to revise the axes. It accepts three
          parameters: figure, axesdict, artistdict. axesdict[0] is the
          default axes. When 'twinx' or 'twiny' used in 'data',
          axesdict[twin-order-number] will be assigned to the twin axes.
          artistdict is a dict of all artists already plotted. The keys
          are the order numbers of artists in their method_lists.
          Other kwargs for revise function can be set in method_list[3].

       b. Value of 'layout' is a list of two elements. layout[0] is a
          position rect list for matplotlib.figure.Figure.add_axes, or a
          three digit number for matplotlib.figure.Figure.add_subplot, or
          a instance of :class:`matplotlib.gridspec.GridSpec`. layout[1]
          is a dict of kwargs for Figure.add_axes or Figure.add_subplot.

       c. Value of 'style' is a list of mplstyles. The style will only
          affect this axes except others. Default: [{'axes.grid': True}].

    4. If you want to plot 3D figure, such as 'plot3D', 'plot_surface',
       in :class:`mpl_toolkits.mplot3d.axes3d.Axes3D`.
       First, add projection='3d' to layout[1].
       Then, set method_list[1] to the plot function.
    '''

    if not isinstance(figurestructure, dict):
        raise ValueError("FigureStructure must be a dict. "
                         + "Not %s." % type(figurestructure))
    if 'Style' in figurestructure:
        if isinstance(figurestructure['Style'], list):
            figstyle = _check_styles(figurestructure['Style'])
        else:
            log.error("FigureStructure['Style'] must be a list. "
                      + "Not %s. " % type(figurestructure['Style'])
                      + "Ignore 'Style' setting!")
    if 'figstyle' not in dir() or not figstyle:
        figstyle = Default_FigureStructure['Style']
    if not isinstance(figurestructure['AxesStructures'], list):
        raise ValueError("FigureStructure['AxesStructures'] must be a list. "
                         "Not %s." % type(figurestructure['AxesStructures']))
    log.ddebug("Figure Style: %s" % str(figstyle))
    with style.context(_filter_styles(figstyle)):
        fig = figure(num=num)
        for i, axstructure in enumerate(figurestructure['AxesStructures'], 1):
            log.ddebug("Picking AxesStructure %d ..." % i)
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
            log.error("AxesStructure must contain key: '%s'! " % k
                      + "Ignore this axes.")
            return
        if not isinstance(axstructure[k], list):
            log.error("AxesStructure[%s] must be a list. " % k
                      + "Not %s. " % type(axstructure[k])
                      + "Ignore this axes.")
            return
    # check layout
    layout = axstructure['layout']
    if not(isinstance(layout, list) and len(layout) == 2):
        log.error("AxesStructure['layout'] must be a two elements list. "
                  "Ignore this axes.")
        return
    if not isinstance(layout[0], (int, list, SubplotSpec)):
        log.error("AxesStructure['layout'][0] must be a "
                  "int, list or SubplotSpec. Ignore this axes.")
        return
    # check style
    if 'style' in axstructure:
        if isinstance(axstructure['style'], list):
            axstyle = _check_styles(axstructure['style'])
        else:
            log.error("AxesStructure['style'] must be a list. "
                      + "Not %s. " % type(axstructure['style'])
                      + "Ignore 'style' setting!")
    if 'axstyle' not in dir() or not axstyle:
        axstyle = Default_AxesStructure['style']
    # begin with style
    log.ddebug("Axes Style: %s" % str(axstyle))
    with style.context(_filter_styles(axstyle)):
        # use layout
        try:
            log.ddebug("Adding axes %s ..." % layout[0])
            if isinstance(layout[0], list):
                ax = fig.add_axes(layout[0], **layout[1])
            else:
                ax = fig.add_subplot(layout[0], **layout[1])
        except Exception:
            log.error("Failed to add axes %s!" % layout[0], exc_info=1)
            return
        # use data
        axesdict, artistdict = {0: ax}, {}
        for index, axfunc, dataargs, datakwargs in axstructure['data']:
            if axfunc in ('twinx', 'twiny'):
                log.ddebug("Creating twin axes %s: %s ..." % (index, axfunc))
                try:
                    ax = getattr(ax, axfunc)()
                    if index in axesdict:
                        log.warn("Duplicate index %s!" % index)
                    axesdict[index] = ax
                    if 'nextcolor' in datakwargs:
                        for i in range(datakwargs['nextcolor']):
                            # i=next(ax._get_lines.prop_cycler)
                            i = ax._get_lines.get_next_color()
                except Exception:
                    log.error("Failed to create axes %s!" % index, exc_info=1)
            elif axfunc == 'revise':
                log.ddebug("Revising axes %s ..." % layout[0])
                try:
                    dataargs(fig, axesdict, artistdict, **datakwargs)
                except Exception:
                    log.error("Failed to revise axes %s!"
                              % layout[0], exc_info=1)
            else:
                log.ddebug("Adding artist %s: %s ..." % (index, axfunc))
                try:
                    art = getattr(ax, axfunc)(*dataargs, **datakwargs)
                    if index in artistdict:
                        log.warn("Duplicate index %s!" % index)
                    artistdict[index] = art
                except Exception:
                    log.error("Failed to add artist %s!" % index, exc_info=1)


def _get_mplstyle_library(path):
    available = style.available.copy()
    for path, name in style.core.iter_style_files(path):
        available.append(name)
    return available


STYLE_LIBRARY_PATH = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'mpl-stylelib')
mplstyle_available = _get_mplstyle_library(STYLE_LIBRARY_PATH)


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


def mplshow(fig):
    '''
    Display the figure *fig*.
    '''
    if get_backend() in (
            'nbAgg',
            'nbagg',
            'notebook',
            'module://ipykernel.pylab.backend_inline'):
        return fig
    else:
        return fig.show()


def mplclose(fig):
    '''
    Close the figure *fig*.
    '''
    close(fig)


mplengine = Engine('matplotlib')
mplengine.figure_factory = mplfigure_factory
mplengine.style_available = mplstyle_available
mplengine.show = mplshow
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


mplengine.tool = {
    'get_style_param': get_mplstyle_param,
}
