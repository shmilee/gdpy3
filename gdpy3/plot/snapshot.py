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
from .gfigure import (
    GFigure,
    get_twinx_axesstructures,
    get_pcolor_axesstructures,
)

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
    _FieldFluxFigInfo = {
        '%s_flux' % f: dict(
            title=r'$%s$ on flux surface' % f.replace(
                'phi', '\phi').replace('apara', 'a_{\parallel}'),
            srckey=['fluxdata-%s' % f])
        for f in ['phi', 'apara', 'fluidne']
    }
    _FigInfo = dict(_ProfileFigInfo, **_PdfFigInfo, **_FieldFluxFigInfo)

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
           *hspace*: float, subplot.hspace, default 0.02
           *xlim*: (`left`, `right`), default [0, max(X)]
           *ylabel_rotation*: str or int, default 'vertical'
        2. fieldflux kwargs:
           *plot_method*, *plot_args*, *plot_kwargs*,
           *colorbar*, *grid_alpha*, *surface_contourf*
           keyword arguments are passed on to
           :func:`gdpy3.plot.gfigure.get_pcolor_axesstructures`
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
        elif self.name in self._FieldFluxFigInfo:
            return _set_fieldflux_axesstructures(self, **kwargs)
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


def _set_fieldflux_axesstructures(self, **kwargs):
    '''
    Set phi, apara, fluidne on flux surface axesstructures, calculation
    '''

    fluxdata, = self.figureinfo['key']
    title = self.figureinfo['title']
    try:
        fluxdata = self.dataobj[fluxdata]
        if fluxdata.size == 0:
            log.debug("No data for Figure '%s'." % self.Name)
            return False
        Y, X = fluxdata.shape
        X = np.arange(0, X) / X * 2 * np.pi
        Y = np.arange(0, Y) / Y * 2 * np.pi
    except Exception as exc:
        log.error("Failed to get data of '%s' from %s! %s" %
                  (self.Name, self.dataobj.file, exc))
        return False

    # fix 3d plot_surface cmap
    if 'plot_method' in kwargs and kwargs['plot_method'] == 'plot_surface':
        cmap = self.nginp.tool['get_style_param'](
            self.figurestyle, 'image.cmap')
        if ('plot_kwargs' in kwargs
                and isinstance(kwargs['plot_kwargs'], dict)):
            kwargs['plot_kwargs']['cmap'] = cmap
        else:
            kwargs['plot_kwargs'] = dict(cmap=cmap)

    try:
        axesstructures = get_pcolor_axesstructures(
            X, Y, fluxdata, r'$\zeta$', r'$\theta$', title, **kwargs)
        self.figurestructure['AxesStructures'] = axesstructures
    except Exception as exc:
        log.error("Failed to set AxesStructures of '%s'! %s"
                  % (self.Name, exc))
        return False

    return True
