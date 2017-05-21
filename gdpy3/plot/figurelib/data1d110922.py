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
    'residual_zonal_flow': dict(
        key='field00-phi',
        title='residual zonal flow'),
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

    log.debug("Get FigureStructure '%s/%s' ..." % (Group, name))

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
        return None, None

    Zmax = max(abs(Z.max()), abs(Z.min()))
    tunit = dictobj[tstep] * dictobj[ndiag]
    Y, X = Z.shape
    X = np.arange(1, X + 1) * tunit
    X, Y = np.meshgrid(X, range(0, Y))

    if name == 'residual_zonal_flow':
        # residual zonal flow
        axesstructures, calculation = __get_reszf_axesstructures(
            dictobj, X, Y, Z, Zmax, tunit, figurestyle)
    else:
        # others
        axesstructures = [{
            'data': [
                [1, 'pcolormesh', (X, Y, Z), dict(
                    label='rtime', vmin=-Zmax, vmax=Zmax)],
            ],
            'layout': [
                111,
                dict(title=__FigInfo[name]['title'],
                     xlabel=r'time($R_0/c_s$)', ylabel='radial')
            ],
            'revise': tools.colorbar_revise_function('rtime'),
        }]
        calculation = None

    figurestructure = {
        'Style': figurestyle,
        'AxesStructures': axesstructures,
    }
    return figurestructure, calculation


def __get_reszf_axesstructures(dictobj, X, Y, Z, Zmax, tunit, figurestyle):
    '''
    Return residual zonal flow axesstructures, calculation
    '''
    krrhoi, krrho0, istep, krdltr = (
        __paragrp + key
        for key in ['zfkrrhoi', 'zfkrrho0', 'zfistep', 'zfkrdltr'])
    if tools.in_dictobj(dictobj, krrhoi, krrho0, istep, krdltr):
        krrhoi, krrho0, istep, krdltr = dictobj.get_many(
            krrhoi, krrho0, istep, krdltr)
    else:
        return [], None

    # 1 original
    log.debug("Getting Axes 221 ...")
    axes1 = {
        'layout': [221, dict(title=r'residual zonal flow, $\phi_{p00}$',
                             xlabel=r'time($R_0/c_s$)',
                             ylabel='radial',
                             projection='3d',
                             )],
        'data': [
            [1, 'plot_surface', (X, Y, Z),
                dict(cmap=tools.mplcmap(figurestyle),
                     rstride=1, cstride=1, linewidth=1,
                     vmin=-Zmax, vmax=Zmax,
                     antialiased=True, label='phi00')
             ],
        ],
        'revise': tools.colorbar_revise_function('phi00', grid_alpha=0.5),
    }

    # 2 history, $\Delta r/2$,  $\Delta r/2 + \lambda/2$
    log.debug("Getting Axes 222 ...")
    index = tools.argrelextrema(Z.sum(axis=1))
    i = int(len(index) / 2)
    iZ1, iZ2 = index[i], index[i + 1]
    Z1, Z2 = Z[iZ1, :], Z[iZ2, :]
    # skip data before istep, maybe zeros
    for i in range(0, Z1.size):
        if Z1[i] != 0:
            break
    if i != istep:
        log.warn("Find nozero in '%s', before istep: '%s'!" % (i, istep))
    time = np.arange(istep, Z1.size) * tunit
    Z1, Z2 = Z1[istep:] / abs(Z1[istep]), Z2[istep:] / abs(Z2[istep])
    # find residual region
    idx1, len1 = tools.findflat(Z1, 0.0005)
    idx2, len2 = tools.findflat(Z2, 0.0005)
    log.debug("Flat region: [%s,%s], [%s,%s]."
              % (time[idx1], time[idx1 + len1 - 1],
                 time[idx2], time[idx2 + len2 - 1]))
    res1, res2 = sum(Z1[idx1:idx1 + len1]) / len1, \
        sum(Z2[idx2:idx2 + len2]) / len2
    axes2 = {
        'layout': [222, dict(title=r'normalized $\phi_{p00}$, '
                                   r'$k_r\rho_i=%.4f$,'
                                   r'$k_r\rho_0=%.4f$' % (krrhoi, krrho0),
                             xlim=[time[0], time[-1]],
                             xlabel=r'time($R_0/c_s$)',)],
        'data': [
            [1, 'plot', (time, Z1), dict(
                label=r'$r=%s, \phi_{res}=%.6f$' % (iZ1, abs(res1)))],
            [2, 'plot', (time, Z2), dict(
                label=r'$r=%s, \phi_{res}=%.6f$' % (iZ2, abs(res2)))],
            [3, 'plot', (time[idx1:idx1 + len1],
                         Z1[idx1:idx1 + len1], '--'), dict()],
            [4, 'plot', (time[idx2:idx2 + len2],
                         Z2[idx2:idx2 + len2], '--'), dict()],
            [5, 'legend', (), dict()]
        ],
    }

    # 3 gamma
    log.debug("Getting Axes 223 ...")
    logZ1 = np.log(abs(tools.savgol_golay_filter(Z1 - res1, 47, 3)))
    logZ2 = np.log(abs(tools.savgol_golay_filter(Z2 - res2, 47, 3)))
    idx1 = [i for i in tools.argrelextrema(logZ1, m='max') if i < idx1]
    idx2 = [i for i in tools.argrelextrema(logZ2, m='max') if i < idx2]
    tfit = [time[i] for i in idx1] + [time[i] for i in idx2]
    lzfit = [logZ1[i] for i in idx1] + [logZ2[i] for i in idx2]
    if tfit:
        result, line = tools.fitline(tfit, lzfit, 1, info='all max')
        gamma1 = result[0][0]
    else:
        line, gamma1 = [], 0
    tfitpart = [time[i] for i in idx1[int(len(idx1) / 2):]] \
        + [time[i] for i in idx2[int(len(idx2) / 2):]]
    lzfitpart = [logZ1[i] for i in idx1[int(len(idx1) / 2):]] \
        + [logZ2[i] for i in idx2[int(len(idx2) / 2):]]
    if tfitpart:
        result, linepart = tools.fitline(
            tfitpart, lzfitpart, 1, info='part max')
        gamma2 = result[0][0]
    else:
        linepart, gamma2 = [], 0

    axes3 = {
        'layout': [223, dict(
            xlabel=r'time($R_0/c_s$)',
            ylabel=r'log(abs(smooth($\phi_{p00} - \phi_{res}$)))')],
        'data': [
            [1, 'plot', (time, logZ1), dict(label=r'$r=%s$' % iZ1)],
            [2, 'plot', (time, logZ2), dict(label=r'$r=%s$' % iZ2)],
            [3, 'plot', (tfit, line, '--'),
                dict(label=r'$\gamma=%.6f$' % gamma1)],
            [4, 'plot', (tfitpart, linepart, 'v--'),
                dict(label=r'$\gamma=%.6f$' % gamma2)],
            [5, 'legend', (), dict()]
        ],
    }

    # 4 FFT, omega
    log.debug("Getting Axes 224 ...")
    f1, a1, p1 = tools.fft(tunit, Z1 - res1)
    f2, a2, p2 = tools.fft(tunit, Z2 - res2)
    index = int(time.size / 2)
    omega1 = f1[index + np.argmax(p1[index:])]
    omega2 = f2[index + np.argmax(p2[index:])]
    axes4 = {
        'layout': [224, dict(
            xlabel=r'$\omega$($c_s/R_0$)',
            ylabel=r'FFT($\phi_{p00} - \phi_{res}$)')],
        'data': [
                [1, 'plot', (f1, p1), dict()],
                [2, 'plot', (f2, p2), dict()],
                [3, 'axvline', (omega1,), dict(
                    ls='--', label=r'$r=%s, \omega=%.6f$' % (iZ1, omega1))],
                [4, 'axvline', (omega2,), dict(
                    ls=':', label=r'$r=%s, \omega=%.6f$' % (iZ2, omega2))],
                [4, 'legend', (), dict()]
        ],
    }

    calculation = {'ZFres1': abs(res1), 'ZFres2': abs(res2),
                   'GAMomega1': omega1, 'GAMomega2': omega2,
                   'GAMgamma1': gamma1, 'GAMgamma2': gamma2}
    return [axes1, axes2, axes3, axes4], calculation
