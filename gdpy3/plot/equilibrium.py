# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
Equilibrium figures
-------------------

This module needs data in group 'equilibrium' get by gdc.

This module provides the :class:`EquilibriumFigureV110922`.
'''

import numpy as np

from . import tools
from .gfigure import (
    GFigure,
    log,
    get_twinx_axesstructures,
    get_pcolor_axesstructures,
)

__all__ = ['EquilibriumFigureV110922']


class EquilibriumFigureV110922(GFigure):
    '''
    A class for figures of equilibrium
    '''
    __slots__ = []
    _FigGroup = 'equilibrium'
    _FigInfo = dict()  # TODO

    def __init__(self, dataobj, name,
                 group=_FigGroup, figurestyle=['gdpy3-notebook']):
        if name not in self._FigInfo.keys():
            raise ValueError("'%s' not found in group '%s'!" % (name, group))
        info = self._FigInfo[name]
        super(SnapshotFigureV110922, self).__init__(
            dataobj, name, group, info, figurestyle=figurestyle)

    def calculate(self, **kwargs):
        '''
        Get the FigureStructure and calculation results.
        Save them in *figurestructure*, *calculation*.

        Notes
        -----
        '''
        log.debug("Get FigureStructure, calculation of '%s' ..." % self.Name)
        self.figurestructure = {
            'Style': self.figurestyle,
            'AxesStructures': [],
        }
        self.calculation = {}

        if self.name in self._FigInfo:
            return _set__axesstructures(self, **kwargs)
        elif self.name in self._FigInfo:
            return _set__axesstructures(self, **kwargs)
        else:
            return False
