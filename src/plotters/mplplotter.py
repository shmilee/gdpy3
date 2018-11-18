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
from ..__about__ import __data_path__
from .base import BasePlotter, BasePloTemplate

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
    'layout': ['int, gridspec, tuple, list', {'add_subplot, add_axes kwargs'}],
    'axstyle': [{'axes.grid': True}],
}
'''


def _get_mplstyle_library(path):
    available = matplotlib.style.available.copy()
    for path, name in matplotlib.style.core.iter_style_files(path):
        available.append(name)
    return available


class MatplotlibPlotter(BasePlotter, BasePloTemplate):
    '''
    Use matplotlib to create figures.
    '''
    __slots__ = []
    _STYLE_LIBPATH = os.path.join(__data_path__, 'mpl-stylelib')
    style_available = _get_mplstyle_library(_STYLE_LIBPATH)

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
        return os.path.join(self._STYLE_LIBPATH, sty + '.mplstyle')

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
        # begin with axstyle
        with matplotlib.style.context(self.filter_style(axstyle)):
            # use layout
            axpos, axkws = layout
            try:
                log.debug("Adding axes %s ..." % (axpos,))
                if isinstance(axpos, (int, matplotlib.gridspec.SubplotSpec)):
                    ax = fig.add_subplot(axpos, **axkws)
                elif isinstance(axpos, (tuple, list)):
                    if len(axpos) == 3:
                        ax = fig.add_subplot(*axpos, **axkws)
                    elif len(axpos) == 4:
                        ax = fig.add_axes(axpos, **axkws)
                    else:
                        log.error("Ignore this axes: position tuple or list "
                                  "should have 3 integers or 4 floats.")
                        return
                else:
                    log.error("Ignore this axes: position must be int, tuple"
                              ", list, or matplotlib.gridspec.SubplotSpec")
                    return
            except Exception:
                log.error("Failed to add axes %s!" % (axpos,), exc_info=1)
                return
            # use data
            axesdict, artistdict = {0: ax}, {}
            for index, axfunc, fargs, fkwargs in data:
                if axfunc in ('twinx', 'twiny'):
                    log.debug("Creating twin axes %s: %s ..."
                              % (index, axfunc))
                    try:
                        ax = getattr(ax, axfunc)()
                        if index in axesdict:
                            log.warning("Duplicate index %s!" % index)
                        axesdict[index] = ax
                        if 'nextcolor' in fkwargs:
                            for i in range(fkwargs['nextcolor']):
                                # i=next(ax._get_lines.prop_cycler)
                                i = ax._get_lines.get_next_color()
                    except Exception:
                        log.error("Failed to create axes %s!"
                                  % index, exc_info=1)
                elif axfunc == 'revise':
                    log.debug("Revising axes %s ..." % (axpos,))
                    try:
                        fargs(fig, axesdict, artistdict, **fkwargs)
                    except Exception:
                        log.error("Failed to revise axes %s!"
                                  % (axpos,), exc_info=1)
                else:
                    log.debug("Adding artist %s: %s ..." % (index, axfunc))
                    try:
                        art = getattr(ax, axfunc)(*fargs, **fkwargs)
                        if index in artistdict:
                            log.warning("Duplicate index %s!" % index)
                        artistdict[index] = art
                    except Exception:
                        log.error("Failed to add artist %s!"
                                  % index, exc_info=1)

    def _create_figure(self, num, axesstructures, figstyle):
        '''Create object *fig*.'''
        with matplotlib.style.context(self.filter_style(figstyle)):
            fig = matplotlib.pyplot.figure(num=num)
            for i, axstructure in enumerate(axesstructures, 1):
                log.debug("Picking AxesStructure %d ..." % i)
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

    def _template_line_axstructs(self, LINE, title, xlabel, ylabel,
                                 xlim, ylim, ylabel_rotation, legend_kwargs):
        '''For :meth:`template_line_axstructs`.'''
        log.debug("Getting Axes %s ..." % 111)
        data, layoutkw, addlegend = [], {}, False
        for i, ln in enumerate(LINE, 1):
            if len(ln) == 3:
                data.append([i, 'plot', (ln[0], ln[1]), dict(label=ln[2])])
                addlegend = True
            elif len(ln) == 2:
                data.append([i, 'plot', (ln[0], ln[1]), {}])
        if addlegend:
            i = i + 1
            data.append([i, 'legend', (), legend_kwargs])
        if title:
            layoutkw['title'] = title
        if xlabel:
            layoutkw['xlabel'] = xlabel
        if ylabel:
            if ylabel_rotation is None:
                layoutkw['ylabel'] = ylabel
            else:
                data.append([i + 1, 'set_ylabel', (ylabel,),
                             dict(rotation=ylabel_rotation)])
        if xlim:
            layoutkw['xlim'] = xlim
        if ylim:
            layoutkw['ylim'] = ylim
        return [{'data': data, 'layout': [111, layoutkw]}], []

    def _template_pcolor_axstructs(
            self, X, Y, Z, plot_method, plot_method_args, plot_method_kwargs,
            title, xlabel, ylabel, colorbar, grid_alpha, plot_surface_shadow):
        '''For :meth:`template_pcolor_axstructs`.'''
        import numpy as np
        Zmax = max(abs(Z.max()), abs(Z.min()))
        layoutkw, plotkw, plotarg, order, data = {}, {}, [], 1, []
        if plot_method == 'plot_surface':
            layoutkw = {'projection': '3d', 'zlim': [-Zmax, Zmax]}
            plotkw.update(rstride=1, cstride=1, linewidth=1, antialiased=True,
                          cmap=self.param_from_style('image.cmap'))
            if plot_surface_shadow:
                _offsetd = {'x': np.min(X), 'y': np.max(Y), 'z': -Zmax}
                _limd = {'x': [np.min(X), np.max(X)],
                         'y': [np.min(Y), np.max(Y)], 'z': [-Zmax, Zmax]}
                for x in plot_surface_shadow:
                    order += 1
                    layoutkw['%slim' % x] = _limd[x]
                    data.append([order, 'contourf', (X, Y, Z, 100),
                                 dict(zdir=x, offset=_offsetd[x])])
        if colorbar:
            order += 1
            data.append([order, 'revise',
                         lambda fig, ax, art: fig.colorbar(art[1]), {}])
        if grid_alpha is not None:
            order += 1
            data.append([order, 'grid', (), dict(alpha=grid_alpha)])
        plotarg.extend(plot_method_args)
        if not plot_method_args and plot_method == 'contourf':
            plotarg.extend([100])
        plotkw.update(vmin=-Zmax, vmax=Zmax)
        plotkw.update(plot_method_kwargs)
        data.insert(0,  [1, plot_method, [X, Y, Z] + plotarg, plotkw])
        if title:
            layoutkw['title'] = title
        if xlabel:
            layoutkw['xlabel'] = xlabel
        if ylabel:
            layoutkw['ylabel'] = ylabel
        return [{'data': data, 'layout': [111, layoutkw]}], []

    def _template_sharex_twinx_axstructs(
            self, X, YINFO,
            hspace, title, xlabel, xlim, ylabel_rotation):
        '''For :meth:`template_sharex_twinx_axstructs`.'''
        AxStructs = []
        for row in range(len(YINFO)):
            number = int("%s1%s" % (len(YINFO), row + 1))
            log.debug("Getting Axes %s ..." % number)
            layout = dict(xlim=xlim)
            if row == 0 and title:
                layout['title'] = title
            if row == len(YINFO) - 1:
                if xlabel:
                    layout['xlabel'] = xlabel
            else:
                layout['xticklabels'] = []
            data, i = [], 0
            if len(YINFO[row]['left']) > 0:
                for i, ln in enumerate(YINFO[row]['left'], 1):
                    data.append([i, 'plot', (X, ln[0]), dict(label=ln[1])])
                if 'llegend' in YINFO[row]:
                    legendkw = YINFO[row]['llegend']
                else:
                    legendkw = dict(loc='upper left')
                i = i + 1
                data.append([i, 'legend', (), legendkw])
                if 'lylabel' in YINFO[row]:
                    i = i + 1
                    data.append([i, 'set_ylabel', (YINFO[row]['lylabel'],),
                                 dict(rotation=ylabel_rotation)])
            if len(YINFO[row]['right']) > 0:
                i = i + 1
                data.append(
                    [i, 'twinx', (), dict(nextcolor=len(YINFO[row]['left']))])
                for i, ln in enumerate(YINFO[row]['right'], i + 1):
                    data.append([i, 'plot', (X, ln[0]), dict(label=ln[1])])
                if 'rlegend' in YINFO[row]:
                    legendkw = YINFO[row]['rlegend']
                else:
                    legendkw = dict(loc='upper right')
                i = i + 1
                data.append([i, 'legend', (), legendkw])
                if 'rylabel' in YINFO[row]:
                    i = i + 1
                    data.append([i, 'set_ylabel', (YINFO[row]['rylabel'],),
                                 dict(rotation=ylabel_rotation)])
                data.append([i + 1, 'set_xlim', xlim, {}])
            AxStructs.append({'data': data, 'layout': [number, layout]})
        return AxStructs, [{'figure.subplot.hspace': hspace}]

    def _template_z111p_axstructs(self, zip_results, suptitle):
        '''
        For :meth:`template_z111p_axstructs`.
        '''
        AxStructs = []
        for i, _results in enumerate(zip_results, 0):
            ax, pos = _results
            log.debug("Getting Axes %s ..." % (pos,))
            if isinstance(pos, (int, list, matplotlib.gridspec.SubplotSpec)):
                ax['layout'][0] = pos
            else:
                log.error("`zip_results[%d]`: invalid position!" % i)
                continue
            AxStructs.append(ax)
        if not suptitle:
            return AxStructs, []

        try:
            data = AxStructs[0]['data']

            def addsuptitle(fig, ax, art): return fig.suptitle(suptitle)
            data.append([len(data) + 1, 'revise', addsuptitle, dict()])
        except Exception:
            log.error("Failed to set suptitle: %s!" % suptitle)
        return AxStructs, []
