# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Residual zonal flow Cores.
'''

import re
import numpy as np
from ..core import DigCore, LayCore, log
from .data1d import Field00FigInfo
from .. import tools

__all__ = ['Data1dRZFDigCoreV110922', 'Data1dRZFLayCoreV110922']


class Data1dRZFDigCoreV110922(DigCore):
    '''
    Residual zonal flow
    datakeys: gtc/zfkrrhoi, gtc/zfkrrho0, gtc/zfistep, gtc/zfkrdltr
    '''
    __slots__ = []
    itemspattern = ['^(?P<section>gtc)\.out$', '[^/]+/(?P<section>gtc)\.out$']
    default_section = 'gtc'

    def _convert(self):
        '''Read 'gtc.out'.'''
        with self.rawloader.get(self.files) as f:
            log.ddebug("Read file '%s'." % self.files)
            outdata = f.read()
        sd = {}
        numpat = r'[-+]?\d+[\.]?\d*[eE]?[-+]?\d*'
        # only residual zonal flow(zf) case, second occurence match
        pat = (r'\*{6}\s+k_r\*rhoi=\s*?(?P<zfkrrhoi>' + numpat + r'?)\s*?,'
               + r'\s+k_r\*rho0=\s*?(?P<zfkrrho0>' + numpat + r'?)\s+?\*{6}$'
               + r'\s*istep=\s*?(?P<zfistep>' + numpat + r'?)\s*.+$'
               + r'\s*\*{5}\s+k_r\*dlt_r=\s*?(?P<zfkrdltr>'
               + numpat + r'?)\s+?\*{5}')
        mdata = [m.groupdict() for m in re.finditer(pat, outdata, re.M)]
        if len(mdata) == 2 and len(mdata[1]) == 4:
            log.debug("Filling datakeys: %s ..." %
                      str([key for key, val in mdata[1].items()]))
            sd.update({key: int(val) if val.isdigit() else float(val)
                       for key, val in mdata[1].items()})
        return sd


class ResidualZFFigInfo(Field00FigInfo):
    '''Figure of residual zonal flow'''
    __slots__ = []
    figurenums = ['residual_zonal_flow']
    numpattern = r'^residual_zonal_(?P<flow>flow)$'

    def __init__(self, fignum, scope, groups):
        super(ResidualZFFigInfo, self).__init__(fignum, scope, groups)
        self.extrakey = ['gtc/%s' % k for k in
                         ['tstep', 'ndiag', 'zfkrrhoi', 'zfkrrho0',
                          'zfistep', 'zfkrdltr', 'qiflux', 'rgiflux']]
        self.template = 'template_z111p_axstructs'

    def calculate(self, data, **kwargs):
        '''
        kwargs
        ------
        *kwargs* of residual zonal flow:
            *reregion_start*, *region_end*: int
                in tstep unit, set residual region.
        *kwargs* passed on to :meth:`plotter.template_pcolor_axstructs`:
            *plot_method*, *plot_method_args*, *plot_method_kwargs*,
            *colorbar*, *grid_alpha*, *plot_surface_shadow*
        '''
        title = r'$\phi_{p00}, q=%.3f, \epsilon=%.3f$' % (
            data['gtc/qiflux'], data['gtc/rgiflux'])
        title = r'%s, $k_r\rho_i=%.4f, k_r\rho_0=%.4f$' % (
            title, data['gtc/zfkrrhoi'], data['gtc/zfkrrho0'])
        super(ResidualZFFigInfo, self).calculate(data, **kwargs)
        # 1
        ax1_calc = self.calculation
        self.calculation = {
            'zip_results': [('template_pcolor_axstructs', 221, ax1_calc)],
            'suptitle': title,
            'krrhoi': data['gtc/zfkrrhoi'], 'krrho0': data['gtc/zfkrrho0'],
            'qiflux': data['gtc/qiflux'], 'rgiflux': data['gtc/rgiflux'],
        }
        if len(ax1_calc['Z']) == 0:
            return
        # 2 history, $\Delta r/2$,  $\Delta r/2 + \lambda/2$
        Z = ax1_calc['Z']
        istep = data['gtc/zfistep']
        tunit = data['gtc/tstep'] * data['gtc/ndiag']
        index = tools.argrelextrema(Z.sum(axis=1))
        if index.size < 3:
            log.warn("Lines of peak less than 3!")
            return
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
        log.parm("Residual region of r=%s: [%s,%s], index: [%s,%s)." % (
            iZ1, time[idx1], time[idx1 + len1 - 1], idx1, idx1 + len1))
        log.parm("Residual region of r=%s: [%s,%s], index: [%s,%s)." % (
            iZ2, time[idx2], time[idx2 + len2 - 1], idx2, idx2 + len2))
        res1, res2 = sum(Z1[idx1:idx1 + len1]) / len1, \
            sum(Z2[idx2:idx2 + len2]) / len2
        ax2_calc = dict(
            LINE=[
                (time, Z1, r'$r=%s, \phi_{res}=%.6f$' % (iZ1, abs(res1))),
                (time, Z2, r'$r=%s, \phi_{res}=%.6f$' % (iZ2, abs(res2))),
                ([time[idx1], time[idx1 + len1 - 1]],
                 [Z1[idx1], Z1[idx1 + len1 - 1]]),
                ([time[idx2], time[idx2 + len2 - 1]],
                 [Z2[idx2], Z2[idx2 + len2 - 1]]),
            ],
            title=r'normalized $\phi_{p00}$',
            xlim=[time[0], time[-1] + tunit], xlabel=r'time($R_0/c_s$)',
        )
        # 3 gamma
        logZ1 = np.log(abs(tools.savgol_golay_filter(Z1 - res1, 47, 3)))
        logZ2 = np.log(abs(tools.savgol_golay_filter(Z2 - res2, 47, 3)))
        xlim = [time[0], time[max(idx1, idx2)] + tunit]
        idx1 = [i for i in tools.argrelextrema(logZ1, m='max') if i < idx1]
        idx2 = [i for i in tools.argrelextrema(logZ2, m='max') if i < idx2]
        tfit1, tfit2 = [time[i] for i in idx1], [time[i] for i in idx2]
        lzfit1, lzfit2 = [logZ1[i] for i in idx1], [logZ2[i] for i in idx2]
        if tfit1:
            result, line1 = tools.fitline(
                tfit1, lzfit1, 1, info='%s peak' % iZ1)
            gamma1 = result[0][0]
        else:
            line1, gamma1 = [], 0
        if tfit2:
            result, line2 = tools.fitline(
                tfit2, lzfit2, 1, info='%s peak' % iZ2)
            gamma2 = result[0][0]
        else:
            line2, gamma2 = [], 0
        ax3_calc = dict(
            LINE=[(time, logZ1, r'$r=%s$' % iZ1),
                  (time, logZ2, r'$r=%s$' % iZ2),
                  (tfit1, line1, r'$\gamma_{%s}=%.6f$' % (iZ1, gamma1)),
                  (tfit2, line2, r'$\gamma_{%s}=%.6f$' % (iZ2, gamma2)), ],
            title=r'normalized $\phi_{p00}$', xlabel=r'time($R_0/c_s$)',
            xlim=xlim, ylabel=r'log(abs(smooth($\phi_{p00} - \phi_{res}$)))',
        )
        # 4 FFT, omega
        f1, a1, p1 = tools.fft(tunit, Z1 - res1)
        f2, a2, p2 = tools.fft(tunit, Z2 - res2)
        index = int(time.size / 2)
        omega1 = f1[index + np.argmax(p1[index:])]
        omega2 = f2[index + np.argmax(p2[index:])]
        xlim = 4 * max(omega1, omega2)
        ax4_calc = dict(
            LINE=[
                (f1, p1, r'$r=%s$' % iZ1),
                (f2, p2, r'$r=%s$' % iZ2),
            ],
            title=r'$\omega_{%s}=%.6f$, $\omega_{%s}=%.6f$' % (
                iZ1, omega1, iZ2, omega2),
            xlabel=r'$\omega$($c_s/R_0$)',
            ylabel=r'FFT($\phi_{p00} - \phi_{res}$)',
            xlim=[-xlim, xlim],
        )
        self.calculation['zip_results'].extend([
            ('template_line_axstructs', 222, ax2_calc),
            ('template_line_axstructs', 223, ax3_calc),
            ('template_line_axstructs', 224, ax4_calc)])
        self.calculation.update({
            'ZFres1': abs(res1), 'ZFres2': abs(res2),
            'GAMgamma1': gamma1, 'GAMgamma2': gamma2,
            'GAMomega1': omega1, 'GAMomega2': omega2
        })


class Data1dRZFLayCoreV110922(LayCore):
    '''
    Residual zonal flow
    fignum: data1d/residual_zonal_flow
    '''
    __slots__ = []
    itemspattern = ['^(?P<section>data1d)$']
    default_section = 'data1d'
    figinfoclasses = [ResidualZFFigInfo]
