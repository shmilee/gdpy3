# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
This module provides the :class:`GFigure`, which contains
all the plot elements, calculation results, figure methods.
'''

import logging

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

    def calculate(self, **kwargs):
        '''
        Get the FigureStructure and calculation results.
        Define this function in derived class.
        '''
        log.error('Define this function in derived class.')
        raise

    def draw(self, num=None, redraw=False, recalculate=False, **kwargs):
        '''
        convert *figurestructure* to Figure instance *figure*

        Parameters
        ----------
        num: integer or string
            pass to *nginp*.figure_factory method
        redraw: bool
            redraw the figure
        recalculate: bool
            recalculate the figurestructure
            When recalculate is True, redraw will also be True.
        kwargs: pass to *calculate* method
        '''
        if (not self.figurestructure
                or not self.figurestructure['AxesStructures']):
            recalculate = True
        if recalculate:
            self.calculate(**kwargs)
        if recalculate or not self.figure:
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
