# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import re
import logging
from . import tools
from . import data1d, history

__all__ = ['GCase']

log = logging.getLogger('gdp')


_FigGroupClassMap = {
    '110922': {
        'data1d': data1d.Data1dFigureV110922,
        'history': history.HistoryFigureV110922,
    }
}
_SnapPattern = re.compile(r'^snap\d{5}$')


class GCase(object):
    '''
    All figures in a GTC case.

    Attributes
    ----------
    datafile: str
        path of .npz or hdf5 file
    dataobj: :class:`gdpy3.read.readnpz.ReadNpz` instance
        a dictionary-like object of *datafile*
    version: str
        gtc code version, read from *datafile*
    gfigure_available: tuple
        Names of available gfigures in this case,
        based on datagroups in *dataobj*,
        format: group/name -> Name
    gfigure_enabled: set
        Names of enabled gfigure objects
    gfigure_ploted: set
        Names of drawed gfigure objects
    gfigurelib: dict
        libaray of enabled or ploted gfigure objects
        format: {Name: gfigureobj}
    '''
    __slots__ = ['datafile', 'dataobj', 'version',
                 'gfigure_available', 'gfigure_enabled',
                 'gfigure_ploted', 'gfigurelib',
                 ]

    def __init__(self, dataobj,
                 default_enable=[], figurestyle=['gdpy3-notebook']):
        if tools.is_dictobj(dataobj):
            self.dataobj = dataobj
            self.datafile = dataobj.file
        else:
            raise ValueError("'dataobj' must be a ReadNpz object."
                             " Not %s." % type(dataobj))
        # version
        if tools.in_dictobj(dataobj, 'version'):
            self.version = dataobj['version']
        else:
            raise KeyError("Key '%s' not in %s!"
                           % ('version', dataobj.file))
        if self.version not in _FigGroupClassMap:
            raise ValueError("GTC version in '%s' doesn't supported!"
                             % dataobj.file)
        # gfigure_available
        gfigure_available = []
        for grp in dataobj.datagroups:
            if grp in _FigGroupClassMap[self.version]:
                cls = _FigGroupClassMap[self.version][grp]
                gfigure_available.extend(cls.get_members())
            # elif _SnapPattern.match(grp):
            #    cls = _FigGroupClassMap[self.version]['snapshot']
            #    cls._FigGroup = grp
            #    gfigure_available.extend(cls.get_members())
            else:
                pass
        self.gfigure_available = tuple(gfigure_available)
        # gfigure enabled ploted, gfigurelib
        self.gfigure_enabled = set()
        self.gfigurelib = {}
        if isinstance(default_enable, list):
            self.enable(*default_enable, figurestyle=figurestyle)
        else:
            self.enable(default_enable, figurestyle=figurestyle)
        self.gfigure_ploted = set()

    def enable(self, *patterns, figurestyle=['gdpy3-notebook']):
        '''
        Enable gfigure objects.

        Parameters
        ----------
        patterns: string or compiled pattern
        figurestyle: default is gdpy3-notebook
        '''
        figstodo = []
        for name in patterns:
            if isinstance(name, str) and name in self.gfigure_available:
                if name not in figstodo:
                    figstodo.append(name)
            else:
                try:
                    pat = re.compile(name)
                except Exception as exc:
                    log.warn("Failed to pattern '%s': %s" % (name, exc))
                else:
                    for member in self.gfigure_available:
                        if pat.match(member) and member not in figstodo:
                            figstodo.append(member)
        if figstodo:
            log.debug("Gfigures to enable:\n%s" % figstodo)
        for member in figstodo:
            if member in self.gfigure_enabled:
                continue
            log.info("Enable gfigure '%s' ..." % member)
            grp = os.path.dirname(member)
            name = os.path.basename(member)
            if grp in _FigGroupClassMap[self.version]:
                cls = _FigGroupClassMap[self.version][grp]
            # elif _SnapPattern.match(grp):
            #    cls = _FigGroupClassMap[self.version]['snapshot']
            #    cls._FigGroup = grp
            #    gfigure_available.extend(cls.get_members())
            else:
                pass
            try:
                gf = cls(self.dataobj, name, group=grp,
                         figurestyle=figurestyle)
            except Exception as exc:
                log.error("Gfigure '%s' not passed: %s" % (member, exc))
            else:
                self.gfigurelib[member] = gf
                self.gfigure_enabled.add(member)

    def disable(self, *patterns):
        '''
        Disable gfigure objects.

        Parameters
        ----------
        patterns: string or compiled pattern
        '''
        figstodo = []
        for name in patterns:
            if isinstance(name, str) and name in self.gfigure_enabled:
                if name not in figstodo:
                    figstodo.append(name)
            else:
                try:
                    pat = re.compile(name)
                except Exception as exc:
                    log.warn("Failed to pattern '%s': %s" % (name, exc))
                else:
                    for member in self.gfigure_enabled:
                        if pat.match(member) and member not in figstodo:
                            figstodo.append(member)
        if figstodo:
            log.debug("Gfigures to disable:\n%s" % figstodo)
        for member in figstodo:
            gf = self.__getitem__(member)
            log.info("Disable gfigure '%s' ..." % member)
            gf.close()
            gf.figurestructure = {}
            gf.calculation = {}
            del gf
            if member in self.gfigure_ploted:
                self.gfigure_ploted.remove(member)
            if member in self.gfigure_enabled:
                self.gfigure_enabled.remove(member)

    def plot(self, Name, show=True, **kwargs):
        '''
        Plot gfigure *Name*.

        Parameters
        ----------
        Name: str
        show: bool
            Show the figure if *show* is True.
        kwargs:
            1) ``figurestyle``, ``engine`` for gfigure
            2) pass to gfigure.draw method
               ``num``, ``redraw``, ``recalculate``,
            3) and some kwargs for gfigure.calculate method
        '''
        gf = self.__getitem__(Name)
        if not gf:
            return False
        try:
            if 'figurestyle' in kwargs:
                gf.figurestyle = kwargs['figurestyle']
            if 'engine' in kwargs:
                gf.engine = kwargs['engine']
            log.info("Plotting gfigure '%s' ..." % Name)
            gf.draw(**kwargs)
        except Exception as exc:
            log.error("Failed to plot gfigure '%s': %s" % (Name, exc))
            return False
        else:
            if gf.figure:
                self.gfigure_ploted.add(Name)
                if show:
                    return gf.show()
                return True
            else:
                log.error("Failed to plot gfigure '%s': %s" % (Name, exc))
                return False

    def __getitem__(self, Name):
        if Name not in self.gfigure_available:
            log.error("Gfigure '%s' not available!" % Name)
            return False
        if Name not in self.gfigure_enabled:
            self.enable(Name)
            if Name not in self.gfigure_enabled:
                return False
        return self.gfigurelib[Name]

    def get(self, Name):
        '''
        Get gfigure object by *Name*, synonym for :meth:`__getitem__`.
        '''
        self.__getitem__(Name)

    def find(self, *keys):
        '''
        Find gfigures which contain *keys in *gfigure_available*.
        '''
        result = self.gfigure_available
        for key in keys:
            key = str(key)
            result = tuple(
                filter(lambda k: True if key in k else False, result))
        return tuple(result)
