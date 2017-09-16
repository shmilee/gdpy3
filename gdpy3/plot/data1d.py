# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
Radial-Time figures
-------------------

This module needs radial time data in group 'data1d' get by gdc.

This module provides the :class:`Data1dFigureV110922`.
'''

import numpy as np

from . import tools
from .gfigure import GFigure, log, get_pcolor_axesstructures

__all__ = ['Data1dFigureV110922']


class Data1dFigureV110922(GFigure):
    '''
    A class for pcolormesh figures of Data1d
    '''
    __slots__ = []
    _FigGroup = 'data1d'
    __parakey = [GFigure._paragrp + 'tstep', GFigure._paragrp + 'ndiag']
    _FigInfo = {
        # data1di(0:mpsi,mpdata1d)
        'ion_flux': dict(
            key=['data1d/i-particle-flux'] + __parakey,
            title='thermal ion particle flux'),
        'ion_energy_flux': dict(
            key=['data1d/i-energy-flux'] + __parakey,
            title='thermal ion energy flux'),
        'ion_momentum_flux': dict(
            key=['data1d/i-momentum-flux'] + __parakey,
            title='thermal ion momentum flux'),
        # data1de(0:mpsi,mpdata1d)
        'electron_flux': dict(
            key=['data1d/e-particle-flux'] + __parakey,
            title='electron particle flux'),
        'electron_energy_flux': dict(
            key=['data1d/e-energy-flux'] + __parakey,
            title='electron energy flux'),
        'electron_momentum_flux': dict(
            key=['data1d/e-momentum-flux'] + __parakey,
            title='electron momentum flux'),
        # data1df(0:mpsi,mpdata1d)
        'fast_ion_flux': dict(
            key=['data1d/f-particle-flux'] + __parakey,
            title='fast ion particle flux'),
        'fast_ion_energy_flux': dict(
            key=['data1d/f-energy-flux'] + __parakey,
            title='fast ion energy flux'),
        'fast_ion_momentum_flux': dict(
            key=['data1d/f-momentum-flux'] + __parakey,
            title='fast ion momentum flux'),
        # field00(0:mpsi,nfield)
        'zonal_flow': dict(
            key=['data1d/field00-phi'] + __parakey,
            title='zonal flow'),
        'residual_zonal_flow': dict(
            key=['data1d/field00-phi'] + __parakey,
            title='residual zonal flow'),
        'zonal_current': dict(
            key=['data1d/field00-apara'] + __parakey,
            title='zonal current'),
        'zonal_fluidne': dict(
            key=['data1d/field00-fluidne'] + __parakey,
            title='zonal fluidne'),
        # fieldrms(0:mpsi,nfield)
        'phi_rms': dict(
            key=['data1d/fieldrms-phi'] + __parakey,
            title=r'$\phi rms$'),
        'apara_rms': dict(
            key=['data1d/fieldrms-apara'] + __parakey,
            title=r'$A_{\parallel} rms$'),
        'fluidne_rms': dict(
            key=['data1d/fieldrms-fluidne'] + __parakey,
            title=r'fluidne rms'),
    }

    def __init__(self, dataobj, name,
                 group=_FigGroup, figurestyle=['gdpy3-notebook']):
        if name not in self._FigInfo.keys():
            raise ValueError("'%s' not found in group '%s'!" % (name, group))
        info = self._FigInfo[name]
        super(Data1dFigureV110922, self).__init__(
            dataobj, name, group, info, figurestyle=figurestyle)

    def calculate(self, **kwargs):
        '''
        Get the FigureStructure and calculation results.
        Save them in *figurestructure*, *calculation*.

        Notes
        -----
        1. optional keyword parameters:
           *plot_method*, *plot_args*, *plot_kwargs*,
           *colorbar*, *grid_alpha*, *surface_contourf*
           keyword arguments are passed on to
           :func:`gdpy3.plot.gfigure.get_pcolor_axesstructures`
        2. residual_zonal_flow special keywords:
           *reregion_start*, *region_end*: int,
           in tstep unit, set residual region.
        '''
        log.debug("Get FigureStructure, calculation of '%s' ..." % self.Name)
        self.figurestructure = {
            'Style': self.figurestyle,
            'AxesStructures': [],
        }
        self.calculation = {}

        Zkey, tstep, ndiag = self.figureinfo['key']
        title = self.figureinfo['title']
        try:
            Z = self.dataobj[Zkey]
            if Z.size == 0:
                log.debug("No data for Figure '%s'." % self.Name)
                return False
            tunit = self.dataobj[tstep] * self.dataobj[ndiag]
            Y, X = Z.shape
            X = np.arange(1, X + 1) * tunit
            Y = np.arange(0, Y)
        except Exception:
            log.error("Failed to get data of '%s' from %s!"
                      % (self.Name, self.dataobj.file), exc_info=1)
            return False

        # fix 3d plot_surface cmap
        if ('plot_method' in kwargs
                and kwargs['plot_method'] == 'plot_surface'):
            cmap = self.nginp.tool['get_style_param'](
                self.figurestyle, 'image.cmap')
            if ('plot_kwargs' in kwargs
                    and isinstance(kwargs['plot_kwargs'], dict)):
                kwargs['plot_kwargs']['cmap'] = cmap
            else:
                kwargs['plot_kwargs'] = dict(cmap=cmap)

        try:
            axesstructures = get_pcolor_axesstructures(
                X, Y, Z, r'time($R_0/c_s$)', r'$r$(mpsi)', title, **kwargs)
            self.figurestructure['AxesStructures'] = axesstructures
        except Exception:
            log.error("Failed to set AxesStructures of '%s'!"
                      % self.Name, exc_info=1)
            return False

        # residual zonal flow
        if self.name == 'residual_zonal_flow':
            # set axesstructures, calculation
            return _set_reszf_axesstructures(self, Z, tunit, **kwargs)

        return True


def _set_reszf_axesstructures(self, Z, tunit, **kwargs):
    '''
    Set residual zonal flow axesstructures, calculation
    '''
    dictobj = self.dataobj
    krrhoi, krrho0, istep, krdltr, qiflux, rgiflux = (
        self._paragrp + key for key in
        ['zfkrrhoi', 'zfkrrho0', 'zfistep', 'zfkrdltr', 'qiflux', 'rgiflux'])
    self.figureinfo['zfkey'] = [krrhoi, krrho0, istep,
                                krdltr, qiflux, rgiflux]
    if tools.in_dictobj(dictobj, krrhoi, krrho0,
                        istep, krdltr, qiflux, rgiflux):
        krrhoi, krrho0, istep, krdltr, qiflux, rgiflux = dictobj.get_many(
            krrhoi, krrho0, istep, krdltr, qiflux, rgiflux)
    else:
        return False
    self.calculation.update({'krrhoi': krrhoi, 'krrho0': krrho0,
                             'qiflux': qiflux, 'rgiflux': rgiflux})

    # 1 original
    log.debug("Getting Axes 221 ...")
    axes1 = self.figurestructure['AxesStructures'][0]
    axes1['layout'][0] = 221
    axes1['layout'][1]['title'] = r'$\phi_{p00}, q=%.3f, \epsilon=%.3f$' % (
        qiflux, rgiflux)

    # 2 history, $\Delta r/2$,  $\Delta r/2 + \lambda/2$
    log.debug("Getting Axes 222 ...")
    index = tools.argrelextrema(Z.sum(axis=1))
    if index.size < 3:
        log.warn("Lines of peak less than 3!")
        return False
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
    if ('region_start' in kwargs and 'region_end' in kwargs
            and isinstance(kwargs['region_start'], int)
            and isinstance(kwargs['region_end'], int)
            and kwargs['region_start'] < kwargs['region_end'] < Z1.size):
        idx1, len1 = kwargs['region_start'], kwargs['region_end']
        len1 = len1 - idx1
        idx2, len2 = idx1, len1
    else:
        idx1, len1 = tools.findflat(Z1, 0.0005)
        idx2, len2 = tools.findflat(Z2, 0.0005)
        if len1 == 0:
            idx1, len1 = Z1.size // 2, Z1.size // 4
        if len2 == 0:
            idx2, len2 = Z1.size // 2, Z1.size // 4
    log.parm("Residual region of r=%s: [%s,%s], index: [%s,%s)."
             % (iZ1, time[idx1], time[idx1 + len1 - 1], idx1, idx1 + len1))
    log.parm("Residual region of r=%s: [%s,%s], index: [%s,%s)."
             % (iZ2, time[idx2], time[idx2 + len2 - 1], idx2, idx2 + len2))
    res1, res2 = sum(Z1[idx1:idx1 + len1]) / len1, \
        sum(Z2[idx2:idx2 + len2]) / len2
    axes2 = {
        'layout': [222, dict(title=r'normalized $\phi_{p00}$, '
                                   r'$k_r\rho_i=%.4f$,'
                                   r'$k_r\rho_0=%.4f$' % (krrhoi, krrho0),
                             xlim=[time[0], time[-1] + tunit],
                             xlabel=r'time($R_0/c_s$)',)],
        'data': [
            [1, 'plot', (time, Z1), dict(
                label=r'$r=%s, \phi_{res}=%.6f$' % (iZ1, abs(res1)))],
            [2, 'plot', (time, Z2), dict(
                label=r'$r=%s, \phi_{res}=%.6f$' % (iZ2, abs(res2)))],
            [3, 'plot', ([time[idx1], time[idx1 + len1 - 1]],
                         [Z1[idx1], Z1[idx1 + len1 - 1]], 'v--'), dict()],
            [4, 'plot', ([time[idx2], time[idx2 + len2 - 1]],
                         [Z2[idx2], Z2[idx2 + len2 - 1]], '^--'), dict()],
            [5, 'legend', (), dict()]
        ],
    }
    self.figurestructure['AxesStructures'].append(axes2)
    self.calculation.update({'ZFres1': abs(res1), 'ZFres2': abs(res2)})

    # 3 gamma
    log.debug("Getting Axes 223 ...")
    logZ1 = np.log(abs(tools.savgol_golay_filter(Z1 - res1, 47, 3)))
    logZ2 = np.log(abs(tools.savgol_golay_filter(Z2 - res2, 47, 3)))
    xlim = [time[0], time[max(idx1, idx2)] + tunit]
    idx1 = [i for i in tools.argrelextrema(logZ1, m='max') if i < idx1]
    idx2 = [i for i in tools.argrelextrema(logZ2, m='max') if i < idx2]
    tfit1, tfit2 = [time[i] for i in idx1], [time[i] for i in idx2]
    lzfit1, lzfit2 = [logZ1[i] for i in idx1], [logZ2[i] for i in idx2]
    if tfit1:
        result, line1 = tools.fitline(tfit1, lzfit1, 1, info='%s peak' % iZ1)
        gamma1 = result[0][0]
    else:
        line1, gamma1 = [], 0
    if tfit2:
        result, line2 = tools.fitline(tfit2, lzfit2, 1, info='%s peak' % iZ2)
        gamma2 = result[0][0]
    else:
        line2, gamma2 = [], 0
    axes3 = {
        'layout': [223, dict(
            xlim=xlim,
            xlabel=r'time($R_0/c_s$)',
            ylabel=r'log(abs(smooth($\phi_{p00} - \phi_{res}$)))')],
        'data': [
            [1, 'plot', (time, logZ1), dict(label=r'$r=%s$' % iZ1)],
            [2, 'plot', (time, logZ2), dict(label=r'$r=%s$' % iZ2)],
            [3, 'plot', (tfit1, line1, 'v--'),
                dict(label=r'$\gamma_{%s}=%.6f$' % (iZ1, gamma1))],
            [4, 'plot', (tfit2, line2, '^--'),
                dict(label=r'$\gamma_{%s}=%.6f$' % (iZ2, gamma2))],
            [5, 'legend', (), dict()]
        ],
    }
    self.figurestructure['AxesStructures'].append(axes3)
    self.calculation.update({'GAMgamma1': gamma1, 'GAMgamma2': gamma2})

    # 4 FFT, omega
    log.debug("Getting Axes 224 ...")
    f1, a1, p1 = tools.fft(tunit, Z1 - res1)
    f2, a2, p2 = tools.fft(tunit, Z2 - res2)
    index = int(time.size / 2)
    omega1 = f1[index + np.argmax(p1[index:])]
    omega2 = f2[index + np.argmax(p2[index:])]
    xlim = 4 * max(omega1, omega2)
    axes4 = {
        'layout': [224, dict(
            xlim=[-xlim, xlim],
            xlabel=r'$\omega$($c_s/R_0$)',
            ylabel=r'FFT($\phi_{p00} - \phi_{res}$)')],
        'data': [
                [1, 'plot', (f1, p1), dict(label=r'$r=%s$' % iZ1)],
                [2, 'plot', (f2, p2), dict(label=r'$r=%s$' % iZ2)],
                [3, 'axvline', (omega1,), dict(
                    ls='--', label=r'$\omega_{%s}=%.6f$' % (iZ1, omega1))],
                [4, 'axvline', (omega2,), dict(
                    ls=':', label=r'$\omega_{%s}=%.6f$' % (iZ2, omega2))],
                [5, 'legend', (), dict()]
        ],
    }
    self.figurestructure['AxesStructures'].append(axes4)
    self.calculation.update({'GAMomega1': omega1, 'GAMomega2': omega2})

    return True
