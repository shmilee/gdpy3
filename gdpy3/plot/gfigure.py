# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
This module provides the :class:`GFigure`, which contains
all the plot elements, calculation results, figure methods.
'''

import logging
import numpy as np

from . import tools
from .enginelib import engine_available, default_engine, get_engine

__all__ = ['GFigure']

log = logging.getLogger('gdp')


class GFigure(object):
    '''
    A figure-like object with lazy-plotting of figures.

    Attributes
    ----------
    dataobj: :class:`gdpy3.read.readnpz.ReadNpz` instance
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

    _paragrp = 'gtcout/'
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
            raise ValueError("'dataobj' must be a ReadNpz instance."
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
        return False
    if not isinstance(YS, np.ndarray):
        log.error("`YS` array must be numpy.ndarray!")
        return False
    if len(X) != YS.shape[1]:
        log.error("Invalid `X`, `YS` array length!")
        return False

    if 'xlim' in kwargs and len(kwargs['xlim']) == 2:
        xlim = kwargs['xlim']
    else:
        xlim = [np.min(X), np.max(X)]

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
            [i + 1, 'set_ylabel', (twinx[row]['lylabel'],), {}],
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
                [i + 1, 'set_ylabel', (twinx[row]['rylabel'],), {}],
                [i + 2, 'legend', (), legendkw],
                [i + 3, 'set_xlim', xlim, {}],
            ])
        axesstructure.append({'data': data, 'layout': [number, layout]})

    return axesstructure
