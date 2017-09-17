# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
This module provides the :class:`GFigure`, which contains
all the plot elements, calculation results, figure methods.
'''

import numpy as np

from . import tools
from .enginelib import engine_available, default_engine, get_engine

__all__ = ['GFigure']

log = tools.getGLogger('P')


class GFigure(object):
    '''
    A figure-like object with lazy-plotting of figures.

    Attributes
    ----------
    dataobj: :class:`gdpy3.convert.NpzLoader` instance
        a dictionary-like object
    name: str
    group: str
    Name: str, *group*-*name*
    figureinfo: dict
        keys in *dataobj* and title etc. used in this figure
    figurestructure: dict
        dict container for all plot elements
    calculation: dict
        dict container for all calculation results
    engine: name of the plot engine
        default 'matplotlib'
    nginp: instance of :class:`gdpy3.plot.enginelib.base.Engine`
        plot engine, set by *engine*
    figurestyle: list
        mplstyles used in *figurestructure*
    figure: Figure instance
        the real figure

    Parameters
    ----------
    dataobj, name, group, figureinfo
    engine, figurestyle
    '''
    __slots__ = ['name', 'group', '__dataobj', '__figureinfo',
                 '__figurestructure', '__calculation',
                 '__engine', '__nginp',
                 '__figurestyle', 'figure']

    _paragrp = 'gtc/'
    _FigGroup = 'group'
    _FigInfo = {'name': dict(key=[])}

    def __init__(self, dataobj, name, group, figureinfo,
                 engine=default_engine, figurestyle=[]):
        self.dataobj = dataobj
        self.name = name
        self.group = group
        self.figureinfo = figureinfo
        self.figurestructure = {}
        self.calculation = {}
        self.engine = engine
        self.figurestyle = figurestyle
        self.figure = None

    @classmethod
    def get_members(cls, group=None):
        if not group:
            group = cls._FigGroup
        return tuple(sorted(group + '/' + n for n in cls._FigInfo.keys()))

    @property
    def Name(self):
        return self. group + '/' + self.name

    @property
    def dataobj(self):
        return self.__dataobj

    @dataobj.setter
    def dataobj(self, obj):
        if tools.is_dictobj(obj):
            self.__dataobj = obj
        else:
            raise ValueError("'dataobj' must be a NpzLoader instance."
                             " Not %s." % type(obj))

    @property
    def figureinfo(self):
        return self.__figureinfo

    @figureinfo.setter
    def figureinfo(self, info):
        if not isinstance(info, dict):
            raise ValueError("'figureinfo' must be a dict."
                             " Not %s." % type(info))
        else:
            if 'key' in info and isinstance(info['key'], list):
                if tools.in_dictobj(self.dataobj, *info['key']):
                    self.__figureinfo = info
                else:
                    raise ValueError("Some keys are invalid!")
            else:
                raise ValueError("figureinfo['key'] must be a list!")

    @property
    def figurestructure(self):
        return self.__figurestructure

    @figurestructure.setter
    def figurestructure(self, structure):
        if isinstance(structure, dict):
            self.__figurestructure = structure
        else:
            log.error("'FigureStructure' must be a dict."
                      " Not %s." % type(structure))

    @property
    def calculation(self):
        return self.__calculation

    @calculation.setter
    def calculation(self, calresult):
        if isinstance(calresult, dict):
            self.__calculation = calresult
        else:
            log.error("'calculation result' must be a dict."
                      " Not %s." % type(calresult))

    @property
    def engine(self):
        return self.__engine

    @engine.setter
    def engine(self, eng):
        if eng in engine_available:
            self.__engine = eng
        else:
            log.error("Plot engine '%s' not found in '%s'! Use default '%s'!"
                      % (eng, engine_available, default_engine))
            self.__engine = default_engine
        self.__nginp = get_engine(self.__engine)

    @property
    def nginp(self):
        return self.__nginp

    @property
    def figurestyle(self):
        return self.__figurestyle

    @figurestyle.setter
    def figurestyle(self, styles):
        if not isinstance(styles, list):
            log.error("'figurestyle' must be a list. Not %s." % type(styles))
            self.__figurestyle = []
        else:
            self.__figurestyle = styles
        self.figurestructure['Style'] = self.__figurestyle

    def calculate(self, **kwargs):
        '''
        Get the FigureStructure and calculation results.
        Define this function in derived class.
        '''
        log.error('Define this function in derived class.')
        raise

    def draw(self, num=None, redraw=False, recal=False, **kwargs):
        '''
        convert *figurestructure* to Figure instance *figure*

        Parameters
        ----------
        num: integer or string
            pass to *nginp*.figure_factory method
        redraw: bool
            redraw the figure
        recal: bool
            recalculate the figurestructure
            When recal is True, redraw will also be True.
        kwargs: pass to *calculate* method
        '''
        if ('AxesStructures' not in self.figurestructure
                or not self.figurestructure['AxesStructures']):
            recal = True
        if recal:
            self.calculate(**kwargs)
        if recal or not self.figure:
            redraw = True
        if redraw:
            self.close()
            log.debug("Drawing figure '%s' ..." % self.Name)
            self.figure = self.nginp.figure_factory(
                self.figurestructure, num=num)

    def plot(self, **kwargs):
        '''
        plot this figure -- synonym for :meth:`draw`.
        '''
        self.draw(**kwargs)

    def close(self):
        '''
        Close this figure
        '''
        if self.figure:
            self.nginp.close(self.figure)
        self.figure = None

    def show(self, **kwargs):
        '''
        display this figure
        '''
        if not self.figure:
            self.plot(**kwargs)
        return self.nginp.show(self.figure)

    def savefig(self, fname, **kwargs):
        '''
        Save the current figure.
        '''
        if not self.figure:
            log.error("Figure %s is not plotted!" % self.Name)
            return
        if self.engine == 'matplotlib':
            log.info("Save figure to %s ..." % fname)
            self.figure.savefig(fname, **kwargs)
        else:
            log.warn("Engine %s doesn't support save method!" % self.engine)


def get_twinx_axesstructures(X, YS, xlabel, title, twinx, **kwargs):
    '''
    Get a list of axesstructure.

    .. code::

               title
             +--------+
      ylabel | axes 1 | ylabel
             +--------+
      ylabel | axes 2 | ylabel
             +--------+
               xlabel

    Parameters
    ----------

    X: 1 dimension array
    YS: 2 dimension array, len(X) == YS.shape[1]
    xlabel: str
    title: str
    twinx: list, all info for the axes

    kwargs:
        xlim: (`left`, `right`), default [min(X), max(X)]
        ylabel_rotation: str or int, default 'vertical'

    Notes
    -----

    Form of *twinx*.

    .. code:: python

        twinx = [
            # axes 1
            dict(left=[(index1, label1), (index2, label2)],
                 right=[(index3, label3)],
                 llegend=dict(loc='upper left'), # optional
                 rlegend=dict(loc='upper right'), # optional
                 lylabel='left ylabel',
                 rylabel='right ylabel'),
            # axes 2
            dict(left=[(0, 'phi')], right=[(2, 'phi rms')],
                 lylabel='field',
                 rylabel='rms')]

    twinx[0]['left'][0]: (index, label) of ydata in YS

    twinx[0]['right']: can be empty

    twinx[0]['llegend']: optional kwargs for legend

    twinx[1]['rylabel']: right ylabel in axes 2
    '''

    # check
    if not isinstance(X, (list, np.ndarray)):
        log.error("`X` array must be list or numpy.ndarray!")
        return []
    if not isinstance(YS, np.ndarray):
        log.error("`YS` array must be numpy.ndarray!")
        return []
    if len(X) != YS.shape[1]:
        log.error("Invalid `X`, `YS` array length!")
        return []

    if 'xlim' in kwargs and len(kwargs['xlim']) == 2:
        xlim = kwargs['xlim']
    else:
        xlim = [np.min(X), np.max(X)]
    if ('ylabel_rotation' in kwargs
            and isinstance(kwargs['ylabel_rotation'], (int, 'str'))):
        yl_rotation = kwargs['ylabel_rotation']
    else:
        yl_rotation = 'vertical'

    axesstructure = []
    for row in range(len(twinx)):
        number = int("%s1%s" % (len(twinx), row + 1))
        log.debug("Getting Axes %s ..." % number)
        layout = dict(xlim=xlim)
        if row == 0:
            layout['title'] = title
        if row == len(twinx) - 1:
            layout['xlabel'] = xlabel
        else:
            layout['xticklabels'] = []
        data = []
        for i, left in enumerate(twinx[row]['left'], 1):
            data.append(
                [i, 'plot', (X, YS[left[0]]), dict(label=left[1])])
        if 'llegend' in twinx[row]:
            legendkw = twinx[row]['llegend']
        else:
            legendkw = dict(loc='upper left')
        data.extend([
            [i + 1, 'set_ylabel', (twinx[row]['lylabel'],),
                dict(rotation=yl_rotation)],
            [i + 2, 'legend', (), legendkw],
        ])
        if len(twinx[row]['right']) > 0:
            data.append(
                [i + 3, 'twinx', (), dict(nextcolor=len(twinx[row]['left']))])
            for i, right in enumerate(twinx[row]['right'], i + 4):
                data.append(
                    [i, 'plot', (X, YS[right[0]]), dict(label=right[1])])
            if 'rlegend' in twinx[row]:
                legendkw = twinx[row]['rlegend']
            else:
                legendkw = dict(loc='upper right')
            data.extend([
                [i + 1, 'set_ylabel', (twinx[row]['rylabel'],),
                    dict(rotation=yl_rotation)],
                [i + 2, 'legend', (), legendkw],
                [i + 3, 'set_xlim', xlim, {}],
            ])
        axesstructure.append({'data': data, 'layout': [number, layout]})

    return axesstructure


def get_pcolor_axesstructures(X, Y, Z, xlabel, ylabel, title, **kwargs):
    '''
    Get a axesstructure for pcolor, pcolormesh, contourf or plot_surface.

    Parameters
    ----------
    X, Y: 1 or 2 dimension numpy.ndarray
    Z: 2 dimension numpy.ndarray
    xlabel, ylabel, title: str

    kwargs:
        *plot_method*: str, 'pcolor', 'pcolormesh', 'contourf', 'plot_surface'
                     default 'pcolormesh'
        *plot_args*: list, optional args for *plot_method*,
                   like 'N', chosen levels for contourf, default 100
        *plot_kwargs*: dict, optional kwargs for *plot_method*,
                     like 'cmap', useful for plot_surface, default 'jet'
        *colorbar*: bool, add colorbar or not, default True
        *grid_alpha*: float, [0.0, 1.0], transparency of grid
                    use this when 'grid.alpha' in style has no effect
        *surface_contourf*: list of ['x', 'y', 'z'], default ['z']
                          add contourf in a surface plot
    '''

    # check
    for _x, _X in [('X', X), ('Y', Y), ('Z', Z)]:
        if not isinstance(_X, np.ndarray):
            log.error("`%s` array must be numpy.ndarray!" % _x)
            return []
    if len(X.shape) == 1 and len(Y.shape) == 1:
        # X, Y: 1 dimension
        if (len(Y), len(X)) != Z.shape:
            log.error("Invalid `X`, `Y` length or `Z` shape!")
            return []
        XX, YY = np.meshgrid(X, Y)
    elif len(X.shape) == 2 and len(Y.shape) == 2:
        # X, Y: 2 dimension
        if not (X.shape == Y.shape == Z.shape):
            log.error("Invalid `X`, `Y` or `Z` shape!")
            return []
        XX, YY = X, Y
    else:
        log.error("Invalid `X`, `Y` dimension!")
        return []

    if ('plot_method' in kwargs
            and kwargs['plot_method'] in (
                'pcolor', 'pcolormesh', 'contourf', 'plot_surface')):
        plot_method = kwargs['plot_method']
    else:
        plot_method = 'pcolormesh'
    # pre
    Zmax = max(abs(Z.max()), abs(Z.min()))
    addlayoutkw, addplotkw, addplotarg, order, adddata = {}, {}, [], 1, []
    if plot_method == 'plot_surface':
        addlayoutkw = {'projection': '3d', 'zlim': [-Zmax, Zmax]}
        addplotkw = dict(rstride=1, cstride=1, linewidth=1,
                         antialiased=True, cmap='jet')
        if 'surface_contourf' in kwargs:
            surface_contourf = kwargs['surface_contourf']
        else:
            surface_contourf = ['z']
        _offsetd = {'x': np.min(X), 'y': np.max(Y), 'z': -Zmax}
        _limd = {'x': ('xlim', [np.min(X), np.max(X)]),
                 'y': ('ylim', [np.min(Y), np.max(Y)]),
                 'z': ('zlim', [-Zmax, Zmax])}
        for x in surface_contourf:
            if x in _offsetd.keys():
                order += 1
                addlayoutkw[_limd[x][0]] = _limd[x][1]
                adddata.append([order, 'contourf', (XX, YY, Z, 100),
                                dict(zdir=x, offset=_offsetd[x])])
    if 'plot_args' in kwargs and isinstance(kwargs['plot_args'], list):
        addplotarg.extend(kwargs['plot_args'])
    else:
        if plot_method == 'contourf':
            addplotarg.extend([100])
    if 'plot_kwargs' in kwargs and isinstance(kwargs['plot_kwargs'], dict):
        addplotkw.update(kwargs['plot_kwargs'])
    if not ('colorbar' in kwargs and not kwargs['colorbar']):
        order += 1
        adddata.append([order, 'revise',
                        lambda fig, ax, art: fig.colorbar(art[1]), {}])
    if 'grid_alpha' in kwargs and isinstance(kwargs['grid_alpha'], float):
        order += 1
        adddata.append([order, 'grid', (), dict(alpha=kwargs['grid_alpha'])])

    axesstructure = [{
        'data': [
            [1, plot_method, [XX, YY, Z] + addplotarg,
                dict(vmin=-Zmax, vmax=Zmax, **addplotkw)],
        ] + adddata,
        'layout': [
            111,
            dict(title=title, xlabel=xlabel, ylabel=ylabel, **addlayoutkw)
        ],
    }]

    return axesstructure
