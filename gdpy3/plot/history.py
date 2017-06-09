#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r'''
History figures
-------------------

This module needs history diagnosis data in group 'history' get by gdr.

This module provides the :class:`HistoryFigureV110922`.
'''

import logging
import numpy as np

from . import tools
from .gfigure import GFigure

__all__ = ['HistoryFigureV110922']

log = logging.getLogger('gdp')


class HistoryFigureV110922(GFigure):
    '''
    A class for figures of History
    '''
    __slots__ = []
    _FigGroup = 'history'
    _ModeFigInfo = {
        'fieldmode%s_%s' % (i, f): dict(
            index=i - 1,
            field=f,
            key=['history/ndstep',
                 'history/fieldmode-%s-real' % f,
                 'history/fieldmode-%s-imag' % f,
                 ] + [
                GFigure._paragrp + k for k in
                ('tstep', 'ndiag', 'nmodes', 'mmodes',
                 'qiflux', 'rgiflux', 'rho0')])
        for i in range(1, 9) for f in ['phi', 'apara', 'fluidne']
    }
    _FigInfo = dict(_ModeFigInfo)

    def __init__(self, dataobj, name,
                 group=_FigGroup, figurestyle=['gdpy3-notebook']):
        if name not in self._FigInfo.keys():
            raise ValueError("'%s' not found in group '%s'!" % (name, group))
        info = self._FigInfo[name]
        super(HistoryFigureV110922, self).__init__(
            dataobj, name, group, info, figurestyle=figurestyle)

    def calculate(self, **kwargs):
        '''
        Get the FigureStructure and calculation results.
        Save them in *figurestructure*, *calculation*.

        Notes
        -----
        1. fieldmode kwargs:
         region_start, region_end: int, in tstep unit 
        '''
        log.debug("Get FigureStructure, calculation of '%s' ..." % self.Name)
        self.figurestructure = {
            'Style': self.figurestyle,
            'AxesStructures': [],
        }
        self.calculation = {}

        if self.name in self._ModeFigInfo:
            return _set_fieldmode_axesstructures(self, **kwargs)
        else:
            return False


# field modes: phi, apara, fluidne. 1-8
def _set_fieldmode_axesstructures(self, **kwargs):
    '''
    Set field modes axesstructures, calculation
    '''

    # check key, get data
    index = self.figureinfo['index']
    field = self.figureinfo['field']
    (ndstep, real, imag, tstep, ndiag,
     nmodes, mmodes, qiflux, rgiflux, rho0) = self.figureinfo['key']
    try:
        (ndstep, tstep, ndiag, qiflux, rgiflux, rho0) = \
            self.gtcdataobj.get_many(ndstep, tstep, ndiag,
                                     qiflux, rgiflux, rho0)
        yreal = self.gtcdataobj[real][index]
        yimag = self.gtcdataobj[imag][index]
        n = self.gtcdataobj[nmodes][index]
        m = self.gtcdataobj[mmodes][index]
        time = np.arange(1, ndstep + 1) * tstep * ndiag
        kthetarhoi = n * qiflux / rgiflux * rho0
    except Exception as exc:
        log.error("Failed to get data '%s' from %s! %s" %
                  (name, dictobj.file, exc))
        return False

    # 1 original
    log.debug("Getting Axes 221 ...")
    axes1 = {
        'data': [
                [1, 'plot', (time, yreal), dict(label='real component')],
                [2, 'plot', (time, yimag), dict(label='imag component')],
                [3, 'legend', (), dict(loc='upper left')],
        ],
        'layout': [
            221,
            dict(title='%s: n=%d, m=%d' % (field, n, m),
                 xlabel=r'time($R_0/c_s$)',
                 xlim=[0, np.max(time)])
        ],
    }
    self.figurestructure['AxesStructures'].append(axes1)
    self.calculation.update({'n': n, 'm': m, 'kthetarhoi': kthetarhoi})

    # 2 log(amplitude), growth rate
    log.debug("Getting Axes 222 ...")
    ya = np.sqrt(yreal**2 + yimag**2)
    if ya.any():
        logya = tools.savgol_golay_filter(np.log(ya), 51, 3, nodebug=True)
    else:
        # all zeros
        logya = ya
    # find growth region1
    if ('region_start' in kwargs and 'region_end' in kwargs
            and isinstance(kwargs['region_start'], int)
            and isinstance(kwargs['region_end'], int)
            and kwargs['region_start'] < kwargs['region_end'] < ndstep):
        reg1, reg2 = kwargs['region_start'], kwargs['region_end']
        region_len = reg2 - reg1
    else:
        reg1, region_len = tools.findgrowth(logya, 1e-4)
        if region_len == 0:
            reg1, region_len = 0, ndstep // 4
        reg2 = reg1 + region_len
        log.info("Growth region index: (%s,%s)" % (reg1, reg2))
    log.debug("Find growth region: [%s,%s]." % (time[reg1], time[reg2 - 1]))
    # polyfit region1
    result, line1 = tools.fitline(
        time[reg1:reg2], logya[reg1:reg2], 1,
        info='[%s,%s] growth region' % (time[reg1], time[reg2 - 1]))
    growth1 = result[0][0]
    # find growth region2
    reg3, reg4 = tools.findflat(np.gradient(logya), 1e-4)
    if reg4 == 0:
        reg3 = int(reg1 + 0.5 * region_len)
        reg4 = int(reg1 + 0.9 * region_len)
    else:
        reg3, reg4 = reg3, reg3 + reg4
    # polyfit region2
    if reg4 - reg3 > 1:
        result, line2 = tools.fitline(
            time[reg3:reg4], logya[reg3:reg4], 1,
            info='[%s,%s] growth region' % (time[reg3], time[reg4 - 1]))
        growth2 = result[0][0]
    else:
        reg3, reg4 = reg1, reg2
        line2, growth2 = line1, growth1
    axes2 = {
        'data': [
                [1, 'plot', (time, logya), dict()],
                [2, 'plot', (time[reg1:reg2], line1),
                    dict(label=r'Fitting, $\gamma=%.6f$' % growth1)],
                [3, 'plot', (time[reg3:reg4], line2, '--'),
                    dict(label=r'Fitting, $\gamma=%.6f$' % growth2)],
                [4, 'legend', (), dict(loc='lower right')],
        ],
        'layout': [
            222,
            dict(title=r'smooth(log(amplitude)), $k_{\theta}\rho_i$=%.6f'
                 % kthetarhoi,
                 xlabel=r'time($R_0/c_s$)',
                 xlim=[0, np.max(time)])
        ],
    }
    self.figurestructure['AxesStructures'].append(axes2)
    self.calculation.update({'growth_long': growth1, 'growth_short': growth2})

    # 3 amplitude normalized by growth rate, real frequency
    log.debug("Getting Axes 223 ...")
    normreal = tools.savgol_golay_filter(
        np.divide(yreal, np.exp(growth1 * time)), 47, 3)
    index = [i for i in tools.argrelextrema(normreal, m='both')
             if reg1 + 0.1 * region_len <= i < reg1 + 0.9 * region_len]
    log.debug("real argrelextrema: %s" % index)
    if len(index) >= 2:
        reg3, reg4, nT1 = index[0], index[-1], (len(index) - 1) / 2
        omega1 = 2 * np.pi * nT1 / (time[reg4] - time[reg3])
    else:
        reg3, reg4, nT1 = reg1, reg2, 0
        omega1 = 0
    normimag = tools.savgol_golay_filter(
        np.divide(yimag, np.exp(growth1 * time)), 47, 3)
    index = [i for i in tools.argrelextrema(normimag, m='both')
             if reg1 + 0.1 * region_len <= i < reg1 + 0.9 * region_len]
    log.debug("imag argrelextrema: %s" % index)
    if len(index) >= 2:
        reg5, reg6, nT2 = index[0], index[-1], (len(index) - 1) / 2
        omega2 = 2 * np.pi * nT2 / (time[reg6] - time[reg5])
    else:
        reg5, reg6, nT2 = reg1, reg2, 0
        omega2 = 0
    axes3 = {
        'data': [
                [1, 'plot', (time, normreal), dict(label='real component')],
                [2, 'plot', (time, normimag), dict(label='imag component')],
                [3, 'axvspan', (time[reg1], time[reg2 - 1]),
                    dict(alpha=0.12, label='(224) FFT region')],
                [4, 'plot', ((time[reg3], time[reg4]),
                             (normreal[reg3], normreal[reg4]), 'D--'),
                    dict(markersize=5, label=r'$\omega=%.6f,nT=%.1f$'
                         % (omega1, nT1))],
                [5, 'plot', ((time[reg5], time[reg6]),
                             (normimag[reg5], normimag[reg6]), 'D--'),
                    dict(markersize=5, label=r'$\omega=%.6f,nT=%.1f$'
                         % (omega2, nT2))],
                [6, 'legend', (), dict()],
        ],
        'layout': [
            223,
            dict(xlabel=r'time($R_0/c_s$)',
                 ylabel='smooth normalized amplitude',
                 xlim=[0, np.max(time)])
        ],
    }
    ymin = min(min(normreal[reg3:reg4]), min(normimag[reg5:reg6]))
    ymax = max(max(normreal[reg3:reg4]), max(normimag[reg5:reg6]))
    if (min(min(normreal), min(normimag)) < 20 * ymin
            or max(max(normreal), max(normimag)) > 20 * ymax):
        axes3['layout'][1]['ylim'] = [3 * ymin, 3 * ymax]
    self.figurestructure['AxesStructures'].append(axes3)
    self.calculation.update({'omega1': omega1, 'omega2': omega2})

    # 4 FFT, real frequency, calculate by real or imag in growth region
    log.debug("Getting Axes 224 ...")
    fft_f, fft_ar, fft_pr = tools.fft(tstep * ndiag, normreal[reg1:reg2])
    fft_f1, fft_ai, fft_pi = tools.fft(tstep * ndiag, normimag[reg1:reg2])
    index = int(region_len / 2)
    index = index + np.argmax(fft_pr[index:])
    log.debug("Get frequency: %s, %s" % (index, fft_f[index]))
    omega3, xlim = fft_f[index], 4 * abs(fft_f[index])
    if omega3 == 0:
        xlim = 0.5
    axes4 = {
        'data': [
                [1, 'plot', (fft_f, fft_pr), dict()],
                [2, 'plot', (fft_f, fft_pi), dict()],
                [3, 'axvline', (omega3,),
                    dict(ls='--', label=r'$\omega=%.6f$' % omega3)],
                [4, 'legend', (), dict()]
        ],
        'layout': [
            224,
            dict(xlabel=r'$\omega$($c_s/R_0$)',
                 xlim=[-xlim, xlim])
        ],
    }
    self.figurestructure['AxesStructures'].append(axes4)
    self.calculation.update({'omega3': omega3})
