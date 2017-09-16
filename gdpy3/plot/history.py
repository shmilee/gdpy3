# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
History figures
-------------------

This module needs history diagnosis data in group 'history' get by gdc.

This module provides the :class:`HistoryFigureV110922`.
'''

import numpy as np

from . import tools
from .gfigure import GFigure, log, get_twinx_axesstructures

__all__ = ['HistoryFigureV110922']


class HistoryFigureV110922(GFigure):
    '''
    A class for figures of History
    '''
    __slots__ = []
    _FigGroup = 'history'
    _ParticleFigInfo = {
        '%s%s' % (p, twin[0]): dict(
            xlabel=r'time($R_0/c_s$)',
            title='particle %s' % p + twin[0].replace('_', ' '),
            twinx=twin[1],
            key=['history/ndstep', 'history/%s' % p]
            + [GFigure._paragrp + k for k in ('tstep', 'ndiag')])
        for p in ['ion', 'electron', 'fastion']
        for twin in [
            ('', [
                dict(left=[(0, r'density $\delta f$')],
                     right=[(1, r'entropy $\delta f^2$')],
                     lylabel=r'$\delta f$', rylabel=r'$\delta f^2$'),
                dict(left=[(2, r'flow u')], right=[(3, r'$\delta u$')],
                     lylabel='u', rylabel=r'$\delta u$'),
                dict(left=[(4, r'energy $E-1.5$')],
                     right=[(5, r'entropy $\delta E$')],
                     lylabel=r'$E$', rylabel=r'$\delta E$'),
            ]),
            ('_flux', [
                dict(left=[(6, 'particle flux')], right=[],
                     lylabel='', rylabel=''),
                dict(left=[(7, 'momentum flux')], right=[],
                     lylabel='', rylabel=''),
                dict(left=[(8, 'energy flux')], right=[],
                     lylabel='', rylabel=''),
            ]),
        ]
    }
    _FieldFigInfo = {
        'field_%s' % f: dict(
            xlabel=r'time($R_0/c_s$)',
            title=r'$%s (\theta=\zeta=0), %s00 (i=iflux)$' % (f, f),
            twinx=[dict(left=[(0, '$%s$' % f)], right=[(3, '$%s RMS$' % f)],
                        lylabel='$%s$' % f, rylabel='$RMS$'),
                   dict(left=[(1, '$%s00$' % f)],
                        right=[(2, '$%s00 RMS$' % f)],
                        lylabel='$%s00$' % f, rylabel='$RMS$')],
            key=['history/ndstep', 'history/fieldtime-%s' % f]
            + [GFigure._paragrp + k for k in ('tstep', 'ndiag')])
        for f in ['phi', 'apara', 'fluidne']
    }
    _ModeFigInfo = {
        'mode%s_%s' % (i, f): dict(
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
    _FigInfo = dict(_ParticleFigInfo, **_FieldFigInfo, **_ModeFigInfo)

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
        2. fieldtime, particle kwargs:
           hspace: float, subplot.hspace, default 0.01
           xlim: (`left`, `right`), default [0, max(time)]
           ylabel_rotation: str or int, default 'vertical'
        '''
        log.debug("Get FigureStructure, calculation of '%s' ..." % self.Name)
        self.figurestructure = {
            'Style': self.figurestyle,
            'AxesStructures': [],
        }
        self.calculation = {}

        if (self.name in self._ParticleFigInfo
                or self.name in self._FieldFigInfo):
            if 'hspace' in kwargs and isinstance(kwargs['hspace'], float):
                hspace = kwargs['hspace']
            else:
                hspace = 0.01
            self.figurestructure['Style'] = self.figurestyle + \
                [{'figure.subplot.hspace': hspace}]
            return _set_particle_or_fieldtime_axesstructures(self, **kwargs)
        elif self.name in self._ModeFigInfo:
            return _set_fieldmode_axesstructures(self, **kwargs)
        else:
            return False


def __replace_str(field):
    '''
    replace phi -> \phi, apara -> a_{\parallel}, etc
    '''
    strmap = (
        ('phi00', 'phi_{p00}'),
        ('apara00', 'a_{\parallel 00}'),
        ('fluidne00', 'fluidne_{00}'),
        ('phi', '\phi'),
        ('apara', 'a_{\parallel}'),
    )
    result = field
    for i, j in strmap:
        result = result.replace(i, j)
    return result


# particle: ion, electron, fastion
# field time: phi, phip00, apara, apara00, fluidne, fluidne00
def _set_particle_or_fieldtime_axesstructures(self, **kwargs):
    '''
    Set particle(ion, electron, fastion) or
    field(phi, apara, fluidne) time axesstructures, calculation
    '''

    # check key, get data
    xlabel = self.figureinfo['xlabel']
    if self.name in self._ParticleFigInfo:
        title = self.figureinfo['title']
        twinx = self.figureinfo['twinx']
    else:
        title = __replace_str(self.figureinfo['title'])
        twinx = []
        for axinfo in self.figureinfo['twinx']:
            newinfo = {}
            for k, v in axinfo.items():
                if k in ('left', 'right'):
                    newinfo[k] = [(i[0], __replace_str(i[1])) for i in v]
                elif k in ('lylabel', 'rylabel'):
                    newinfo[k] = __replace_str(v)
                else:
                    newinfo[k] = v
            twinx.append(newinfo)

    # ydata: partdata or fieldtime
    ndstep, ydata, tstep, ndiag = self.figureinfo['key']
    try:
        ndstep, ydata, tstep, ndiag = \
            self.dataobj.get_many(ndstep, ydata, tstep, ndiag)
        if ydata.size == 0:
            log.debug("No data for Figure '%s'." % self.Name)
            return False
        time = np.arange(1, ndstep + 1) * tstep * ndiag
    except Exception:
        log.error("Failed to get data of '%s' from %s!"
                  % (self.Name, self.dataobj.file), exc_info=1)
        return False

    if 'xlim' not in kwargs:
        kwargs['xlim'] = [0, np.max(time)]

    try:
        axesstructures = get_twinx_axesstructures(
            time, ydata, xlabel, title, twinx, **kwargs)
        self.figurestructure['AxesStructures'] = axesstructures
    except Exception:
        log.error("Failed to set AxesStructures of '%s'!"
                  % self.Name, exc_info=1)
        return False
    # self.calculation.update({})

    return True


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
            self.dataobj.get_many(ndstep, tstep, ndiag,
                                  qiflux, rgiflux, rho0)
        yreal = self.dataobj[real][index]
        yimag = self.dataobj[imag][index]
        n = self.dataobj[nmodes][index]
        m = self.dataobj[mmodes][index]
        time = np.arange(1, ndstep + 1) * tstep * ndiag
        kthetarhoi = n * qiflux / rgiflux * rho0
    except Exception:
        log.error("Failed to get data of '%s' from %s!"
                  % (self.Name, self.dataobj.file), exc_info=1)
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
            dict(title='$%s: n=%d, m=%d$' % (__replace_str(field), n, m),
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
    log.parm("Find growth region: [%s,%s], index: [%s,%s)."
             % (time[reg1], time[reg2 - 1], reg1, reg2))
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
    log.parm("Real argrelextrema: %s" % index)
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
    log.parm("Imag argrelextrema: %s" % index)
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
    log.parm("Get frequency: %s, %s" % (index, fft_f[index]))
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

    return True
