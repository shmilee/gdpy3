# -*- coding: utf-8 -*-

# Copyright (c) 2021 shmilee

'''
Residual zonal flow Cores.
'''

import numpy as np
from ..cores.digger import Digger, dlog
from .. import tools
from .history import field_tex_str
from .data1d import _Data1dDigger

_all_Converters = []
_all_Diggers = ['HistoryRZFDigger']
__all__ = _all_Converters + _all_Diggers


class HistoryRZFDigger(Digger):
    '''phi_p00 history'''
    __slots__ = ['_fstr00']
    itemspattern = [r'^(?P<s>history)/fieldtime-phi$']
    commonpattern = ['history/ndstep', 'gtc/tstep', 'gtc/ndiag',
                     'gtc/rzf_bstep', 'gtc/rzf_kr', 'gtc/rho0',
                     'data1d/field00-phi']
    post_template = 'tmpl_z111p'

    def _set_fignum(self, numseed=None):
        self._fignum = 'residual_zf'
        self._fstr00 = field_tex_str['phi00']
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *ipsi*: int
            select psi in data1d results, 0<ipsi<mpsi, defalut mpis//2
        *norm*: bool
            normalize phi_p00 by phi_p00[bstep] or not, default True
        *res_time*: [t0, t1]
            set residual time, t0<=time[x0:x1]<=t1
        '''
        ndstep, tstep, ndiag = self.pckloader.get_many(*self.extrakeys[:3])
        dt = tstep * ndiag
        time = np.around(np.arange(0, ndstep) * dt, 8)
        hist = self.pckloader.get(self.srckeys[0])
        bstep, kr, rho0 = self.pckloader.get_many(*self.extrakeys[3:6])
        dat1d = self.pckloader.get(self.extrakeys[6])
        krrho0 = kr*rho0
        if bstep % ndiag == 0:
            bindex = bstep // ndiag
            dlog.debug('bindex=%d' % bindex)
        else:
            bindex = bstep // ndiag + 1
            dlog.warning('bindex=bstep/ndiag=%.3f=%d' % (bstep/ndiag, bindex))
        while hist[1, bindex] == 0:
            bindex += 1
            dlog.warning('data[bindex]==0, ++bindex=%d!' % bindex)
        # cutoff data
        time = time[bindex:]
        hiszf = hist[1, bindex:]
        d1dzf = dat1d[:, bindex:]
        # select data1d
        mpsi = dat1d.shape[0] - 1
        ipsi = int(kwargs.get('ipsi', mpsi//2))
        s1dzf = d1dzf[ipsi]
        # norm
        norm = bool(kwargs.get('norm', True))
        if norm:
            hiszf = hiszf/hiszf[0]
            s1dzf = s1dzf/s1dzf[0]
        # find residual index
        start, end = None, None
        if 'res_time' in kwargs:
            start, end = kwargs['res_time']
            index = np.where((time >= start) & (time <= end))[0]
            if index.size > 0:
                start, end = index[0], index[-1]
                # dlog.debug('res_time_end(1): %s ' % time[end])
            else:
                dlog.warning('Cannot set residual time: %s <= time <= %s!'
                             % (start, end))
                start, end = None, None
        # dlog.debug('growth_time: start=%s ' % start)
        if start is None:
            start, region_len = tools.findflat(hiszf, 5e-4)
            if region_len == 0:
                start = hiszf.size // 2
                region_len = max(hiszf.size // 4, 2)
            end = start + region_len - 1
            # dlog.debug('res_time_end(2): %s ' % time[end])
        dlog.parm("Find residual time: [%s,%s], index: [%s,%s]."
                  % (time[start], time[end], start, end))
        if self.kwoptions is None:
            self.kwoptions = dict(
                ipsi=dict(widget='IntSlider',
                          rangee=(0, mpsi, 1),
                          value=ipsi,
                          description='ipsi:'),
                norm=dict(widget='Checkbox',
                          value=norm,
                          description='normalize phi_p00:'),
                res_time=dict(widget='FloatRangeSlider',
                              rangee=[time[0], time[-1], dt],
                              value=[time[start], time[end]],
                              description='residual time:'))
        restime = [time[start], time[end]]
        acckwargs = {ipsi: ipsi, 'norm': norm, 'res_time': restime}
        # 1 res
        hisres = hiszf[start:end].sum()/(end-start)
        hisres_err = hiszf[start:end].std()
        s1dres = s1dzf[start:end].sum()/(end-start)
        s1dres_err = s1dzf[start:end].std()
        # 2 gamma
        mx = time[:start]
        hisgamma, hisfity = self.__gamma(hiszf[:start], mx, hisres, 'history')
        s1dgamma, s1dfity = self.__gamma(s1dzf[:start], mx, s1dres, 'data1d')
        # 3 w
        hiscosy, i1, i2, nT1, hisomega = self.__omega(
            hiszf[:start], mx, hisres, hisgamma[0], hisgamma[1], 'history')
        s1dcosy, i3, i4, nT2, s1domega = self.__omega(
            s1dzf[:start], mx, s1dres, s1dgamma[0], s1dgamma[1], 'data1d')
        # 4 FFT
        _tf1, _, _pf1 = tools.fft(mx[1]-mx[0], hiscosy)
        _tf2, _, _pf2 = tools.fft(mx[1]-mx[0], s1dcosy)
        index = np.argmax(_pf1)
        omega1 = _tf1[index]
        dlog.parm("Get history frequency: %s, %.6f" % (index, omega1))
        index = np.argmax(_pf2)
        omega2 = _tf2[index]
        dlog.parm("Get data1d frequency: %s, %.6f" % (index, omega2))
        return dict(
            time=time,
            hiszf=hiszf,
            d1dzf=d1dzf, Ypsi=np.array(range(0, mpsi+1)),
            s1dzf=s1dzf, ipsi=ipsi,
            zfstr=r'$%s$' % self._fstr00,
            krrho0=krrho0,
            hisres=hisres, hisres_err=hisres_err,
            s1dres=s1dres, s1dres_err=s1dres_err, restime=restime,
            hisgamma=hisgamma, hisfity=hisfity,
            s1dgamma=s1dgamma, s1dfity=s1dfity, gammatime=mx,
            hiscosy=hiscosy, hisomega=hisomega, hisnT=nT1,
            his_ot=[mx[i1], mx[i2]], his_oy=[hiscosy[i1], hiscosy[i2]],
            s1dcosy=s1dcosy, s1domega=s1domega, s1dnT=nT2,
            s1d_ot=[mx[i3], mx[i4]], s1d_oy=[s1dcosy[i3], s1dcosy[i4]],
            his4tx=_tf1, his4power=_pf1, his4omega=omega1,
            s1d4tx=_tf2, s1d4power=_pf2, s1d4omega=omega2,
        ), acckwargs

    def __gamma(self, zf, t, res, info):
        def f(x, a, b):
            return (zf[0]-res) * np.exp(-a*(x-t[0]+1e-25)**b)+res
        i = tools.argrelextrema(zf, m='max')
        i = np.insert(i, 0, 0)
        gamma, pcov, fity = tools.curve_fit(f, t[i], zf[i], fitX=t)
        dlog.parm("Get %s gamma: (%.6f, %.6f)" % (info, gamma[0], gamma[1]))
        return gamma, fity

    def __omega(self, zf, t, res, g0, g1, info):
        cosy = (zf-res) * np.exp(g0*(t-t[0]+1e-25)**(g1))+res
        #my = tools.savgolay_filter(cosy, info='smooth zonal flow')
        index = tools.argrelextrema(cosy, m='both')
        if len(index) >= 2:
            idx1, idx2, nT = index[0], index[-1], (len(index) - 1) / 2
            omega = 2 * np.pi * nT / (t[idx2] - t[idx1])
        else:
            idx1, idx2, nT, omega = 0, 1, 0, 0
        dlog.parm("Get %s omega: %.6f" % (info, omega))
        return cosy, idx1, idx2, nT, omega

    def _post_dig(self, results):
        r = results
        ax1 = dict(X=r['time'], Y=r['Ypsi'], Z=r['d1dzf'],
                   title=r'%s, $k_r\rho_0=%.6f$' % (r['zfstr'], r['krrho0']),
                   xlabel=r'time($R_0/c_s$)', ylabel=r'mpsi')
        g1, g2 = r['hisgamma']
        g3, g4 = r['s1dgamma']
        ax2 = dict(LINE=[
            (r['time'], r['hiszf'], 'i=iflux'),
            (r['time'], r['s1dzf'], 'i=%d' % r['ipsi']),
            (r['restime'], [r['hisres'], r['hisres']],
                r'$R(iflux)=%.4f$' % r['hisres']),
            (r['restime'], [r['s1dres'], r['s1dres']],
                r'$R(%d)=%.4f$' % (r['ipsi'], r['s1dres'])),
            (r['gammatime'], r['hisfity'],
                r'i=iflux, $e^{-%.4f t^{%.4f}}$' % (g1, g2)),
            (r['gammatime'], r['s1dfity'],
                r'i=%d, $e^{-%.4f t^{%.4f}}$' % (r['ipsi'], g3, g4))],
            title=r['zfstr'] + r', residual $R$, damping $\gamma$',
            xlim=r['time'][[0, -1]], xlabel=r'time($R_0/c_s$)',
            legend_kwargs=dict(loc='upper right'),
        )
        ax3 = dict(LINE=[
            (r['gammatime'], r['hiscosy'], 'i=iflux'),
            (r['gammatime'], r['s1dcosy'], 'i=%d' % r['ipsi']),
            (r['his_ot'], r['his_oy'],
                r'$\omega=%.6f, nT=%.1f$' % (r['hisomega'], r['hisnT'])),
            (r['s1d_ot'], r['s1d_oy'],
                r'$\omega=%.6f, nT=%.1f$' % (r['s1domega'], r['s1dnT']))],
            title=r'%s remove damping' % r['zfstr'],
            xlim=r['gammatime'][[0, -1]], xlabel=r'time($R_0/c_s$)',
        )
        maxp1, maxp2 = max(r['his4power']), max(r['s1d4power'])
        ax4 = dict(LINE=[
            (r['his4tx'], r['his4power'], 'i=iflux'),
            (r['s1d4tx'], r['s1d4power'], 'i=%d' % r['ipsi']),
            ([r['his4omega'], r['his4omega']], [0, maxp1],
                r'$\omega(iflux)=%.6f$' % r['his4omega']),
            ([r['s1d4omega'], r['s1d4omega']], [0, maxp2],
                r'$\omega(%d)=%.6f$' % (r['ipsi'], r['his4omega']))],
            title='FFT ax3, power spectral',  xlabel=r'$\omega$($c_s/R_0$)')

        return dict(zip_results=[
            ('tmpl_contourf', 221, ax1), ('tmpl_line', 222, ax2),
            ('tmpl_line', 223, ax3), ('tmpl_line', 224, ax4),
        ])
