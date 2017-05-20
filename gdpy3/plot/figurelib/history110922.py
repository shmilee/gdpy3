# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r'''
History figures
-------------------

This module needs history diagnosis data in group 'history' get by gdr.
'''

import os
import logging
import numpy as np
from gdpy3.plot import tools

__all__ = ['Group' 'Figures' 'get_figurestructure']

log = logging.getLogger('gdp')


__ver = '110922'
__FigInfo = dict()
# field modes: phi, apara, fluidne. 1-8
__ModeFigInfo = {
    'fieldmode%s_%s' % (i, f):
    dict(index=i - 1, field=f,
         real='fieldmode-%s-real' % f, imag='fieldmode-%s-imag' % f)
    for i in range(1, 9) for f in ['phi', 'apara', 'fluidne']
}
__FigInfo.update(__ModeFigInfo)

__keysgrp = 'history/'
__paragrp = 'gtcout/'

Group = 'history'
Figures = tuple(__FigInfo.keys())


# field modes: phi, apara, fluidne. 1-8
def __getax_fieldmode(dictobj, name):
    '''
    Return field modes axesstructures, calculation
    '''

    # check key, get data
    index = __ModeFigInfo[name]['index']
    field = __ModeFigInfo[name]['field']
    real = __keysgrp + __ModeFigInfo[name]['real']
    imag = __keysgrp + __ModeFigInfo[name]['imag']
    tstep, ndiag, nmodes, mmodes, qiflux, rgiflux, rho0 = (
        __paragrp + key for key in
        ('tstep', 'ndiag', 'nmodes', 'mmodes', 'qiflux', 'rgiflux', 'rho0'))
    ndstep = __keysgrp + 'ndstep'
    try:
        yreal = dictobj[real][index]
        yimag = dictobj[imag][index]
        (tstep, ndiag, nmodes, mmodes, qiflux, rgiflux, rho0, ndstep) = \
            dictobj.get_many(tstep, ndiag, nmodes, mmodes,
                             qiflux, rgiflux, rho0, ndstep)
        time = np.arange(1, ndstep + 1) * tstep * ndiag
        n = nmodes[index]
        m = mmodes[index]
        kthetarhoi = n * qiflux / rgiflux * rho0
    except Exception as exc:
        log.error("Failed to get data '%s' from %s! %s" %
                  (name, dictobj.file, exc))
        return None, None

    # 1 original
    axes1 = {
        'data': [
                [1, 'plot', (time, yreal), dict(label='real component')],
                [2, 'plot', (time, yimag), dict(label='imag component')],
                [3, 'legend', (), dict(loc='upper left')],
        ],
        'layout': [
            221,
            dict(title='n=%d, m=%d' % (n, m),
                 xlabel=r'time($R_0/c_s$)',
                 xlim=[0, np.max(time)])
        ],
    }

    # 2 log(amplitude), growth rate
    ya = np.sqrt(yreal**2 + yimag**2)
    logya = tools.savgol_golay_filter(np.log(ya), 47, 3)
    # find growth region
    tmpga = [1 if g > 0 else -ndstep for g in np.gradient(logya)]
    region_len = tools.max_subarray(tmpga)
    for region_start in range(ndstep):
        if sum(tmpga[region_start:region_start + region_len]) == region_len:
            break
    # [0,1] -> [0.05,0.95], resist smooth
    region_start = int(region_start + 0.05 * region_len)
    region_len = int(0.9 * region_len)
    reg1, reg2 = region_start, region_start + region_len
    log.debug("Find growth region: [%s,%s]." % (time[reg1], time[reg2 - 1]))
    # polyfit [0,1] or [0.5,0.9]*growth_region
    result, line1 = tools.fitline(time[reg1:reg2], logya[reg1:reg2], 1,
                                  info='[0,1] growth region')
    growth1 = result[0][0]
    reg3 = int(reg1 + 0.5 * region_len)
    reg4 = int(reg1 + 0.9 * region_len)
    result, line2 = tools.fitline(time[reg3:reg4], logya[reg3:reg4], 1,
                                  info='[0.5,0.9] growth region')
    growth2 = result[0][0]
    axes2 = {
        'data': [
                [1, 'plot', (time, logya), dict()],
                [2, 'plot', (time[reg1:reg2], line1),
                    dict(label=r'Fitting, $\gamma=%.6f$' % growth1)],
                [3, 'plot', (time[reg3:reg4], line2),
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

    # 3 amplitude normalized by growth rate, real frequency
    normreal = tools.savgol_golay_filter(
        np.divide(yreal, np.exp(growth2 * time)), 47, 3)
    normimag = tools.savgol_golay_filter(
        np.divide(yimag, np.exp(growth2 * time)), 47, 3)
    index = [i for i in tools.argrelextrema(normreal, m='both')
             if reg1 + 0.1 * region_len <= i < reg1 + 0.9 * region_len]
    log.debug("real argrelextrema: %s" % index)
    if len(index) >= 2:
        reg3, reg4 = index[0], index[-1]
        omega1 = np.pi * (len(index) - 1) / (time[reg4] - time[reg3])
    else:
        reg3, reg4 = reg1, reg2
        omega1 = 0
    index = [i for i in tools.argrelextrema(normimag, m='both')
             if reg1 + 0.1 * region_len <= i < reg1 + 0.9 * region_len]
    log.debug("imag argrelextrema: %s" % index)
    if len(index) >= 2:
        reg5, reg6, nT = index[0], index[-1], (len(index) - 1) / 2
        omega2 = 2 * np.pi * nT / (time[reg6] - time[reg5])
    else:
        reg5, reg6, nT = reg1, reg2, 0
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
                         % (omega1, nT))],
                [5, 'plot', ((time[reg5], time[reg6]),
                             (normimag[reg5], normimag[reg6]), 'D--'),
                    dict(markersize=5, label=r'$\omega=%.6f,nT=%.1f$'
                         % (omega2, nT))],
                [6, 'legend', (), dict(loc='best')],
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

    # 4 FFT, real frequency, calculate by real or imag in growth region
    fft_f, fft_ar, fft_pr = tools.fft(tstep * ndiag, normreal[reg1:reg2])
    fft_f1, fft_ai, fft_pi = tools.fft(tstep * ndiag, normimag[reg1:reg2])
    index = int(region_len / 2)
    index = index + np.argmax(fft_pr[index:])
    log.debug("Get frequency: %s, %s" % (index, fft_f[index]))
    omega3, xlim = fft_f[index], 4 * abs(fft_f[index])
    axes4 = {
        'data': [
                [1, 'plot', (fft_f, fft_pr), dict()],
                [2, 'plot', (fft_f, fft_pi), dict()],
                [3, 'axvline', (omega3,),
                    dict(ls='--', label=r'$\omega=%.6f$' % omega3)],
                [4, 'legend', (), dict(loc='best')]
        ],
        'layout': [
            224,
            dict(xlabel=r'$\omega$($c_s/R_0$)',
                 xlim=[-xlim, xlim])
        ],
    }

    calculation = {'n': n, 'm': m, 'kthetarhoi': kthetarhoi,
                   'growth_long': growth1, 'growth_short': growth2,
                   'omega1': omega1, 'omega2': omega2, 'omega3': omega3}
    return [axes1, axes2, axes3, axes4], calculation


def get_figurestructure(dictobj, name, figurestyle=[]):
    '''
    Get the FigureStructure by name.
    Return FigureStructure and calculation results.

    Parameters
    ----------
    dictobj: a dictionary-like object
        instance of :class:`gdpy3.read.readnpz.ReadNpz`, etc.
    name: figure name
    figurestyle: a list of mplstyles
    '''

    # check name
    if name not in Figures:
        log.error("'%s' is not in the '%s' Figures!" % (name, Group))
        return None, None

    log.debug("Get FigureStructure '%s/%s' ..." % (Group, name))

    # axesstructures
    axesstructures, calculation = None, None
    try:
        if name in __ModeFigInfo:
            axesstructures, calculation = __getax_fieldmode(dictobj, name)
            figurestyle += [{'axes.grid.which': 'both'}]
        elif name in 'TODO':
            pass
    except Exception as exc:
        log.error("Failed to get FigureStructure: %s" % exc)
    if not axesstructures:
        return None, None

    figurestructure = {
        'Style': figurestyle,
        'AxesStructures': axesstructures,
    }
    return figurestructure, calculation
