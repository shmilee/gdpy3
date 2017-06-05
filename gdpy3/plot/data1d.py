# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r'''
Radial-Time figures
-------------------

This module needs radial time data in group 'data1d' get by gdr.

This module provides the :class:`Data1dFigureV110922`.
'''

import os
import logging
import numpy as np

from . import tools
from .gfigure import GFigure

__all__ = ['Data1dFigureV110922']

log = logging.getLogger('gdp')


class Data1dFigureV110922(GFigure):
    '''
    A class for pcolormesh figures of Data1d
    '''
    __slots__ = []
    ver = '110922'
    __paragrp = 'gtcout/'
    __keysgrp = 'data1d/'
    __FigInfo = {
        # data1di(0:mpsi,mpdata1d)
        'ion_flux': dict(
            key='i-particle-flux', title='thermal ion particle flux'),
        'ion_energy_flux': dict(
            key='i-energy-flux', title='thermal ion energy flux'),
        'ion_momentum_flux': dict(
            key='i-momentum-flux', title='thermal ion momentum flux'),
        # data1de(0:mpsi,mpdata1d)
        'electron_flux': dict(
            key='e-particle-flux', title='electron particle flux'),
        'electron_energy_flux': dict(
            key='e-energy-flux', title='electron energy flux'),
        'electron_momentum_flux': dict(
            key='e-momentum-flux', title='electron momentum flux'),
        # data1df(0:mpsi,mpdata1d)
        'fast_ion_flux': dict(
            key='f-particle-flux', title='fast ion particle flux'),
        'fast_ion_energy_flux': dict(
            key='f-energy-flux', title='fast ion energy flux'),
        'fast_ion_momentum_flux': dict(
            key='f-momentum-flux', title='fast ion momentum flux'),
        # field00(0:mpsi,nfield)
        'zonal_flow': dict(
            key='field00-phi', title='zonal flow'),
        'zonal_current': dict(
            key='field00-apara', title='zonal current'),
        'zonal_fluidne': dict(
            key='field00-fluidne', title='zonal fluidne'),
        # fieldrms(0:mpsi,nfield)
        'phi_rms': dict(
            key='fieldrms-phi', title=r'$\phi rms$'),
        'apara_rms': dict(
            key='fieldrms-apara', title=r'$A_{\parallel} rms$'),
        'fluidne_rms': dict(
            key='fieldrms-fluidne', title=r'fluidne rms'),
    }

    def __init__(self, name, dataobj, figurestyle=['gdpy3-notebook']):
        grp = 'data1d'
        if name not in self.__FigInfo.keys():
            raise ValueError("'%s' not found in group '%s'!" % (name, grp))
        keys = [self.__keysgrp + self.__FigInfo[name]['key']]
        super(Data1dFigureV110922, self).__init__(
            name, grp, dataobj, keys, figurestyle=figurestyle)

    def calculate(self, **kwargs):
        '''
        Get the FigureStructure and calculation results.
        Save them in *figurestructure*, *calculation*.

        Notes
        -----
        required parameters:
            *name*, *gtcdataobj*, *figurestyle* of instance
        optional parameters:
            plot_method: 'pcolormesh', 'plot_surface'
            default 'pcolormesh'
        return:
            True: success
            False: get empty figure
        '''
        log.debug("Get FigureStructure, calculation of '%s' ..." % self.Name)
        self.figurestructure = {
            'Style': self.figurestyle,
            'AxesStructures': [],
        }
        self.calculation = {}

        Zkey = self.figurekeys[0]
        tstep, ndiag = self.__paragrp + 'tstep', self.__paragrp + 'ndiag'
        if tools.in_dictobj(self.gtcdataobj, Zkey, tstep, ndiag):
            Z = self.gtcdataobj[Zkey]
            if Z.size == 0:
                Z = None
            else:
                Zmax = max(abs(Z.max()), abs(Z.min()))
                tunit = self.gtcdataobj[tstep] * self.gtcdataobj[ndiag]
                Y, X = Z.shape
                X = np.arange(1, X + 1) * tunit
                X, Y = np.meshgrid(X, range(0, Y))
        else:
            Z = None
        if Z is None:
            log.debug("No data for Figure '%s'." % self.Name)
            return False

        if ('plot_method' in kwargs
                and kwargs['plot_method'] in ('pcolormesh', 'plot_surface')):
            plot_method = kwargs['plot_method']
        else:
            plot_method = 'pcolormesh'
        addlayoutdict, adddatadict = {}, {}
        # fix 3d
        if plot_method == 'plot_surface':
            addlayoutdict = {'projection': '3d'}
            adddatadict = dict(
                rstride=1, cstride=1, linewidth=1, antialiased=True,
                cmap=self.nginp.tool['get_style_param'](
                    self.figurestyle, 'image.cmap')
            )

        self.figurestructure['AxesStructures'] = [{
            'data': [
                [1, plot_method, (X, Y, Z), dict(
                    label='rtime', vmin=-Zmax, vmax=Zmax,
                    **adddatadict)],
            ],
            'layout': [
                111,
                dict(title=self.__FigInfo[self.name]['title'],
                     xlabel=r'time($R_0/c_s$)', ylabel='radial',
                     **addlayoutdict)
            ],
            'revise': self.nginp.tool['get_colorbar_revise_func']('rtime'),
        }]
        return True
