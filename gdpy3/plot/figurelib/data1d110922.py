# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r'''
Radial-Time figures
-------------------

Group: str of group name
Figures: tuple names of FigureStructure
get_figurestructure: function to get FigureStructure by a name

This module needs radial time data in group 'data1d' get by gdr.
'''

import os
import logging
import numpy as np
from gdpy3.plot import tools

__all__ = ['Group' 'Figures' 'get_figurestructure']

log = logging.getLogger('gdp')


__ver = '110922'
__FigInfo = {
    # data1di(0:mpsi,mpdata1d)
    'ion_flux': dict(
        key='i-particle-flux',
        title='thermal ion particle flux'),
    'ion_energy_flux': dict(
        key='i-energy-flux',
        title='thermal ion energy flux'),
    'ion_momentum_flux': dict(
        key='i-momentum-flux',
        title='thermal ion momentum flux'),
    # data1de(0:mpsi,mpdata1d)
    'electron_flux': dict(
        key='e-particle-flux',
        title='electron particle flux'),
    'electron_energy_flux': dict(
        key='e-energy-flux',
        title='electron energy flux'),
    'electron_momentum_flux': dict(
        key='e-momentum-flux',
        title='electron momentum flux'),
    # data1df(0:mpsi,mpdata1d)
    'fast_ion_flux': dict(
        key='f-particle-flux',
        title='fast ion particle flux'),
    'fast_ion_energy_flux': dict(
        key='f-energy-flux',
        title='fast ion energy flux'),
    'fast_ion_momentum_flux': dict(
        key='f-momentum-flux',
        title='fast ion momentum flux'),
    # field00(0:mpsi,nfield)
    'zonal_flow': dict(
        key='field00-phi',
        title='zonal flow'),
    'zonal_current': dict(
        key='field00-apara',
        title='zonal current'),
    'zonal_fluidne': dict(
        key='field00-fluidne',
        title='zonal fluidne'),
    # fieldrms(0:mpsi,nfield)
    'phi_rms': dict(
        key='fieldrms-phi',
        title=r'$\phi rms$'),
    'apara_rms': dict(
        key='fieldrms-apara',
        title=r'$A_{\parallel} rms$'),
    'fluidne_rms': dict(
        key='fieldrms-fluidne',
        title=r'fluidne rms'),
}
__keysgrp = 'data1d/'
__paragrp = 'gtcout/'

Group = 'data1d'
Figures = tuple(__FigInfo.keys())


def get_figurestructure(dictobj, name, figurestyle=[]):
    '''
    Get the FigureStructure by name.
    Return FigureStructure and calculation results.

    Parameters
    ----------
    dictobj: a dictionary-like object
        instance of :class:`gdpy3.read.readnpz.ReadNpz`, 
        :class:`gdpy3.read.readhdf5.ReadHdf5` or
        :class:`gdpy3.read.readraw.ReadRaw`
    name: figure name
    figurestyle: a list of mplstyles
    '''

    # check name
    if name not in Figures:
        log.error("'%s' is not in the '%s' Figures!" % (name, Group))
        return None, None
    # check key, get axdata
    Zkey = __keysgrp + __FigInfo[name]['key']
    tstep = __paragrp + 'tstep'
    ndiag = __paragrp + 'ndiag'
    if tools.in_dictobj(dictobj, Zkey, tstep, ndiag):
        Z = dictobj[Zkey]
        if Z.size == 0:
            log.debug("No data for Figure '%s/%s'." % (Group, name))
            return None, None
        else:
            tunit = dictobj[tstep] * dictobj[ndiag]
            Y, X = Z.shape
            X = np.arange(1, X + 1) * tunit
            X, Y = np.meshgrid(X, range(0, Y))
    else:
        return None, None

    log.debug("Get FigureStructure '%s/%s' ..." % (Group, name))
    figurestructure = {
        'Style': figurestyle,
        'AxesStructures': [{
            'data': [
                [1, 'pcolormesh', (X, Y, Z), dict(
                    cmap='jet', label='rtime')],
            ],
            'layout': [
                111,
                dict(title=__FigInfo[name]['title'],
                     xlabel=r'time($R_0/c_s$)', ylabel='radial')
            ],
            'revise': tools.colorbar_revise_function(label='rtime'),
        }]
    }
    calculation = None
    return figurestructure, calculation
