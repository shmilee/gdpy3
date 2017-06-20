# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r'''
Snapshot figures
----------------

This module needs data in group 'snapshot' get by gdr.

This module provides the :class:`SnapshotFigureV110922`.
'''

import logging
import numpy as np

from . import tools
from .gfigure import GFigure

__all__ = ['SnapshotFigureV110922']

log = logging.getLogger('gdp')


class SnapshotFigureV110922(GFigure):
    '''
    A class for figures of snapshot
    '''
    __slots__ = []
    _FigGroup = 'snapshot'
    _ProfileFigInfo = {
        '%s_%s' % (p, d[0]): dict(
            index=d[1], title=d[2],
            srckey=['mpsi+1', '%s-profile' % p])
        for p in ['ion', 'electron', 'fastion']
        for d in [
            ['density', [0, 1],
                [r'%s density full f' % p, r'%s density $\delta f$' % p]],
            ['flow', [2, 3],
                [r'%s flow full f' % p, r'%s flow $\delta f$' % p]],
            ['energy', [4, 5],
                [r'%s energy full f' % p, r'%s energy $\delta f$' % p]],
        ]
    }
    _FigInfo = dict(_ProfileFigInfo)

    def __init__(self, dataobj, name,
                 group=None, figurestyle=['gdpy3-notebook']):
        if name not in self._FigInfo.keys():
            raise ValueError("'%s' not found in group '%s'!" % (name, group))
        info = self._FigInfo[name].copy()
        info['key'] = [group + '/' + k for k in info['srckey']]
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

        if self.name in self._ProfileFigInfo:
            return _set_profile_axesstructures(self, **kwargs)
        else:
            return False


def _set_profile_axesstructures(self, **kwargs):
    '''
    Set profile axesstructures, calculation
    '''

    # check key, get data
    index = self.figureinfo['index']
    title = self.figureinfo['title']
    if len(index) != len(title):
        log.error("Invalid figure info!")
        return False
    else:
        length = len(index)
    mpsi1, profile = self.figureinfo['key']
    try:
        mpsi1, profile = self.dataobj.get_many(mpsi1, profile)
        ypro = [profile[:, index[i]] for i in range(length)]
    except Exception as exc:
        log.error("Failed to get data of '%s' from %s! %s" %
                  (self.Name, self.dataobj.file, exc))
        return False

    for i in range(length):
        number = int("%s1%s" % (length, i + 1))
        log.debug("Getting Axes %s ..." % number)
        axes = {
            'data': [
                [1, 'plot', (range(mpsi1), ypro[i]), dict(label=title[i])],
                [2, 'legend', (), dict()],
            ],
            'layout': [
                number, dict(xlabel='radial (mpsi)',
                             xlim=[0, mpsi1],
                             **{'title': title[i] if i == 0 else ''})
            ],
        }
        self.figurestructure['AxesStructures'].append(axes)

    return True
