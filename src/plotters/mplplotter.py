# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains matplotlib plotter class. A simple wrapper for matplotlib.
'''

import os
import matplotlib
import matplotlib.style
import matplotlib.pyplot
import mpl_toolkits.mplot3d

from ..glogger import getGLogger
from .base import BasePlotter

__all__ = ['MatplotlibPlotter']
log = getGLogger('P')

_Mpl_Axes_Structure = '''
{
    'data': [
        [1, 'Axes plot func', (args,), {'kwargs'}],
        [2, 'plot', (xarray, yarray, 'ro-'), {'label': 'line'}],
        [4, 'legend', (), dict(loc='upper right')],
        [8, 'twinx or twiny', (), dict(nextcolor='int')],
        # def revise_func(fig, axesdict, artistdict, **kw)
        [9, 'revise', revise_func, {'kw'}],
    ],
    'layout': ['int, gridspec, list', {'add_subplot, add_axes kwargs'}],
    'axstyle': [{'axes.grid': True}],
}
'''


class MatplotlibPlotter(BasePlotter):
    '''
    Use matplotlib to create figures.
    '''
    __slots__ = []

    def __get_mplstyle_library(path):
        available = matplotlib.style.available.copy()
        for path, name in matplotlib.style.core.iter_style_files(path):
            available.append(name)
        return available

    __STYLE_LIBPATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'mpl-stylelib')
    style_available = __get_mplstyle_library(__STYLE_LIBPATH)

    def __init__(self, name):
        super(MatplotlibPlotter, self).__init__(
            name, style=['gdpy3-notebook'], example_axes=_Mpl_Axes_Structure)

    def _check_style(self, sty):
        '''Check single style *sty*.'''
        if sty in self.style_available:
            return True
        try:
            with matplotlib.style.context(sty):
                pass
            return True
        except Exception as exc:
            log.error("Ignore style '%s': %s" % (sty, exc))
            return False

    def _filter_style(self, sty):
        '''Change *sty* str to absolute path.'''
        return os.path.join(self.__STYLE_LIBPATH, sty + '.mplstyle')

    def _param_from_style(self, param):
        if param in matplotlib.rcParams:
            with matplotlib.style.context(self.filter_style(self.style)):
                return matplotlib.rcParams[param]
        else:
            log.error("Invalid param '%s' for matplotlib.rcParams!" % param)
            return None

    def _add_axes(self, fig, data, layout, axstyle):
        '''
        Add axes to *fig*: `matplotlib.figure.Figure` instance
        '''
        # recheck layout
        if not isinstance(
                layout[0], (int, list, matplotlib.gridspec.SubplotSpec)):
            log.error("AxesStructure['layout'][0] must be a int, list, or "
                      "matplotlib.gridspec.SubplotSpec. Ignore this axes.")
            return
        # begin with axstyle
        with matplotlib.style.context(self.filter_style(axstyle)):
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
            for index, axfunc, fargs, fkwargs in data:
                if axfunc in ('twinx', 'twiny'):
                    log.ddebug("Creating twin axes %s: %s ..."
                               % (index, axfunc))
                    try:
                        ax = getattr(ax, axfunc)()
                        if index in axesdict:
                            log.warn("Duplicate index %s!" % index)
                        axesdict[index] = ax
                        if 'nextcolor' in fkwargs:
                            for i in range(fkwargs['nextcolor']):
                                # i=next(ax._get_lines.prop_cycler)
                                i = ax._get_lines.get_next_color()
                    except Exception:
                        log.error("Failed to create axes %s!"
                                  % index, exc_info=1)
                elif axfunc == 'revise':
                    log.ddebug("Revising axes %s ..." % layout[0])
                    try:
                        fargs(fig, axesdict, artistdict, **fkwargs)
                    except Exception:
                        log.error("Failed to revise axes %s!"
                                  % layout[0], exc_info=1)
                else:
                    log.ddebug("Adding artist %s: %s ..." % (index, axfunc))
                    try:
                        art = getattr(ax, axfunc)(*fargs, **fkwargs)
                        if index in artistdict:
                            log.warn("Duplicate index %s!" % index)
                        artistdict[index] = art
                    except Exception:
                        log.error("Failed to add artist %s!"
                                  % index, exc_info=1)

    def _create_figure(self, num, axesstructures, figstyle):
        '''Create object *fig*.'''
        with matplotlib.style.context(self.filter_style(figstyle)):
            fig = matplotlib.pyplot.figure(num=num)
            for i, axstructure in enumerate(axesstructures, 1):
                log.ddebug("Picking AxesStructure %d ..." % i)
                self.add_axes(fig, axstructure)
        return fig

    def _show_figure(self, fig):
        '''Display *fig*.'''
        if matplotlib.get_backend() in (
                'nbAgg',
                'nbagg',
                'notebook',
                'module://ipykernel.pylab.backend_inline'):
            return fig
        else:
            return fig.show()

    def _close_figure(self, fig):
        '''Close *fig*.'''
        matplotlib.pyplot.close(fig)
        fig.clf()

    def _save_figure(self, fig, fpath, **kwargs):
        '''Save *fig* to *fpath*.'''
        fig.savefig(fpath, **kwargs)
