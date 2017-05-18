# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import logging
from . import tools
from . import enginelib
from . import figurelib

__all__ = ['GtcFigures']

log = logging.getLogger('gdp')


FigureMoudleMapDict = {
    '110922': {
        figurelib.data1d110922.Group: figurelib.data1d110922,
        figurelib.history110922.Group: figurelib.history110922,
    }
}


class GtcFigures(object):
    '''
    All GTC figures.

    Attributes
    ----------
        dictobj: a dictionary-like object
            instance of :class:`gdpy3.read.readnpz.ReadNpz`
        figure_factory: function
            use FigureStructure to get Figure instance
            set by *engine*
        figures: tuple
            Names of figure objects, grouped by figurelib Groups
            Format: Group/names -> Names
        version: str
            gtc code version, default is '110922'
    '''
    __slots__ = ['dictobj', 'figure_factory', 'figures', 'version']

    def __init__(self, dictobj, engine='mpl', version='110922'):
        if tools.is_dictobj(dictobj):
            self.dictobj = dictobj
        else:
            raise ValueError("'dictobj' must be a ReadNpz or ReadHdf5 object."
                             " Not %s." % type(dictobj))

        self.figure_factory = enginelib.get_figure_factory(engine)
        if not self.figure_factory:
            log.warn("Use default plot engine 'matplotlib'.")
            self.figure_factory = enginelib.get_figure_factory('mpl')

        # version
        if version in FigureMoudleMapDict:
            self.version = version
        else:
            log.debug("GTC version '%s' not supported! Use '%s'."
                      % (version, '110922'))
            self.version = '110922'
        if tools.in_dictobj(dictobj, 'version'):
            dataversion = dictobj['version']
        else:
            raise KeyError("Key '%s' is needed!" % 'version')
        if dataversion != self.version:
            raise ValueError("GTC version in '%s' doesn't match GTC figures!"
                             % dictobj.file)

        # all Names
        self.figures = list()
        for Group, Module in FigureMoudleMapDict[self.version].items():
            self.figures.extend([Group + '/' + name
                                 for name in Module.Figures])
        self.figures = tuple(self.figures)

    def get_figure(self, Name, figurestyle=[]):
        '''
        Get the figure by Name.
        Return figure instance and calculation results.
        '''

        # check
        if Name not in self.figures:
            log.error("'%s' is not in the Figure Names!" % Name)
            return None, None
        Group = os.path.dirname(Name)
        name = os.path.basename(Name)
        if Group not in FigureMoudleMapDict[self.version]:
            log.error("Figure Group '%s' not found!" % Group)
            return None, None

        # figurestyle
        if not figurestyle:
            figurestyle = ['gdpy3-notebook']
        for i, style in enumerate(figurestyle):
            if isinstance(style, str):
                figurestyle[i] = tools.mplstylelib(style)

        # FigureStructure
        log.info("Plotting figure '%s' ..." % Name)
        Module = FigureMoudleMapDict[self.version][Group]
        figurestructure, calculation = Module.get_figurestructure(
            self.dictobj, name, figurestyle=figurestyle)

        # get figure instance
        if figurestructure:
            return self.figure_factory(figurestructure), calculation
        else:
            return None, None
