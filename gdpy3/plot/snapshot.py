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
from .gfigure import GFigure, get_twinx_axesstructures

__all__ = ['SnapshotFigureV110922']

log = logging.getLogger('gdp')


class SnapshotFigureV110922(GFigure):
    '''
    A class for figures of snapshot
    '''
    __slots__ = []
    _FigGroup = 'snapshot'
    _ProfileFigInfo = {
        '%s_profile' % p: dict(
            xlabel='r (mpsi)',
            title='%s profile' % p,
            twinx=[
                dict(left=[(0, 'density f')],
                     right=[(1, r'density $\delta f$')],
                     lylabel='$f$', rylabel=r'$\delta f$'),
                dict(left=[(2, 'flow f')], right=[(3, r'flow $\delta f$')],
                     lylabel='$f$', rylabel=r'$\delta f$'),
                dict(left=[(4, 'energy f')],
                     right=[(5, r'energy $\delta f$')],
                     lylabel='$f$', rylabel=r'$\delta f$'),
            ],
            srckey=['mpsi+1', '%s-profile' % p])
        for p in ['ion', 'electron', 'fastion']
    }
    _PdfFigInfo = {
        '%s_pdf' % p: dict(
            xlabel='nvgrid',
            title='%s pdf' % p,
            twinx=[
                dict(left=[(0, 'energy f')],
                     right=[(1, r'energy $\delta f$')],
                     lylabel='$f$', rylabel=r'$\delta f$'),
                dict(left=[(2, 'pitch angle f')],
                     right=[(3, r'pitch angle $\delta f$')],
                     lylabel='$f$', rylabel=r'$\delta f$'),
            ],
            srckey=['nvgrid', '%s-pdf' % p])
        for p in ['ion', 'electron', 'fastion']
    }
    _FigInfo = dict(_ProfileFigInfo, **_PdfFigInfo)

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
        1. profile, pdf kwargs:
           hspace: float, subplot.hspace, default 0.02
           xlim: (`left`, `right`), default [0, max(X)]
           ylabel_rotation: str or int, default 'vertical'
        '''
        log.debug("Get FigureStructure, calculation of '%s' ..." % self.Name)
        self.figurestructure = {
            'Style': self.figurestyle,
            'AxesStructures': [],
        }
        self.calculation = {}

        if self.name in self._ProfileFigInfo or self.name in self._PdfFigInfo:
            if 'hspace' in kwargs and isinstance(kwargs['hspace'], float):
                hspace = kwargs['hspace']
            else:
                hspace = 0.02
            self.figurestructure['Style'] = self.figurestyle + \
                [{'figure.subplot.hspace': hspace}]
            return _set_profile_or_pdf_axesstructures(self, **kwargs)
        else:
            return False


def _set_profile_or_pdf_axesstructures(self, **kwargs):
    '''
    Set particle profile, pdf axesstructures, calculation
    '''

    # check key, get data
    xlabel = self.figureinfo['xlabel']
    title = self.figureinfo['title']
    twinx = self.figureinfo['twinx']
    # when x='mpsi+1', ydata='profile'
    # when x='nvgrid', ydata='pdf'
    x, ydata = self.figureinfo['key']
    try:
        time = ' (istep=%d)' % int(self.group.replace('snap', ''))
        title = title + time
        x, ydata = self.dataobj.get_many(x, ydata)
        if ydata.size == 0:
            log.debug("No data for Figure '%s'." % self.Name)
            return False
        X = np.arange(x)
        Ydata = ydata.T
    except Exception as exc:
        log.error("Failed to get data of '%s' from %s! %s" %
                  (self.Name, self.dataobj.file, exc))
        return False

    if 'xlim' not in kwargs:
        kwargs['xlim'] = [0, np.max(X)]

    try:
        axesstructures = get_twinx_axesstructures(
            X, Ydata, xlabel, title, twinx, **kwargs)
        self.figurestructure['AxesStructures'] = axesstructures
    except Exception as exc:
        log.error("Failed to set AxesStructures of '%s'! %s"
                  % (self.Name, exc))
        return False

    return True
