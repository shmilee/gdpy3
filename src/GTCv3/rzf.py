# -*- coding: utf-8 -*-

# Copyright (c) 2021 shmilee

'''
Residual zonal flow Cores.
'''

import numpy as np
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog
from .. import tools
from .data1d import _Data1dDigger

_all_Converters = ['Data1dDensityConverter']
_all_Diggers = ['Data1dDensityDigger', 'HistoryRZFDigger']
__all__ = _all_Converters + _all_Diggers


class Data1dDensityConverter(Converter):
    '''
    Radial Time Density of Particles

    Source:  module shmilee_diag, ddensity(0:mpsi,2,nspecies).
       The 2d array is density[r,time].
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = ['^(?P<section>data1d)_density\.out$',
                    '.*/(?P<section>data1d)_density\.out$']
    _datakeys = (
        # 1. parameters
        'ndstep', 'mpsi+1', 'nspecies', 'nhybrid',
        # 2. data
        'i-density', 'e-density', 'f-density')

    def _convert(self):
        '''Read 'data1d_density.out'.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd, outsd = {}, {}
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:4]))
        for i, key in enumerate(self._datakeys[:4]):
            sd.update({key: int(outdata[i].strip())})

        outdata = np.array([float(n.strip()) for n in outdata[4:]])
        ndata = sd['mpsi+1'] * sd['nspecies']
        if len(outdata) // ndata != sd['ndstep']:
            clog.debug("Filling datakeys: %s ..." % 'ndstep')
            sd.update({'ndstep': len(outdata) // ndata})
            outdata = outdata[:sd['ndstep'] * ndata]
        # reshape outdata
        outdata = outdata.reshape((ndata, sd['ndstep']), order='F')
        # fill data
        clog.debug("Filling datakeys: %s ..." % 'i-density')
        index0, index1 = 0, sd['mpsi+1']
        outsd.update({'i-density': outdata[index0:index1, :]})
        if sd['nspecies'] > 1 and sd['nhybrid'] > 0:
            clog.debug("Filling datakeys: %s ..." % 'e-density')
            index0, index1 = index1, index1 + sd['mpsi+1']
            outsd.update({'e-density': outdata[index0:index1, :]})
        if ((sd['nspecies'] == 2 and sd['nhybrid'] == 0) or
                (sd['nspecies'] == 3 and sd['nhybrid'] > 0)):
            clog.debug("Filling datakeys: %s ..." % 'f-density')
            index0, index1 = index1, index1 + sd['mpsi+1']
            outsd.update({'f-density': outdata[index0:index1, :]})

        # outsd.update(sd) Duplicate keys in Data1dConverter
        return outsd


class Data1dDensityDigger(_Data1dDigger):
    '''density of ion, electron, fastion.'''
    __slots__ = ['particle']
    itemspattern = ['^(?P<s>data1d)/(?P<particle>(?:i|e|f))-density']
    commonpattern = ['gtc/tstep', 'gtc/ndiag']
    post_template = ('tmpl_z111p', 'tmpl_contourf', 'tmpl_sharextwinx')
    __particles = dict(i='ion', e='electron', f='fastion')

    def _set_fignum(self, numseed=None):
        self.particle = self.__particles[self.section[1]]
        self._fignum = '%s_density' % self.particle
        self.kwoptions = None

    def _get_title(self):
        return r'%s $\delta n(r,t)$' % self.particle

    def _dig(self, kwargs):
        results, acckwargs = super(Data1dDensityDigger, self)._dig(kwargs)
        # X, Y, X, ylabel, title
        X, Z = results['X'], results['Z']
        index = [tools.argrelextrema(Z[:, i]) for i in range(Z.shape[1])]
        extrema = [np.abs(Z[index[i], i]).mean() for i in range(Z.shape[1])]
        results['extrema'] = np.array(extrema)
        return results, acckwargs

    def _post_dig(self, results):
        r = results
        lb = r'%s $\delta n(r)$, amplitude $A$' % self.particle
        ax = {'left': [], 'right': [(r['extrema'], lb)], 'rylabel': r'$A$'}
        zip_results = [
            ('tmpl_contourf', 111, dict(
                X=r['X'], Y=r['Y'], Z=r['Z'], title=r['title'],
                xlabel=r'time($R_0/c_s$)', ylabel=r['ylabel'])),
            ('tmpl_sharextwinx', 111, dict(
                X=r['X'], YINFO=[ax],
                xlim=[r['X'][0], r['X'][-1]]))
        ]
        return dict(zip_results=zip_results)


class HistoryRZFDigger(Digger):
    '''phi_p00 history'''
    __slots__ = []
    itemspattern = [r'^(?P<s>history)/fieldtime-phi$']
    commonpattern = ['history/ndstep', 'gtc/tstep', 'gtc/ndiag',
                     # backward compatibility v110922
                     'gtc/(?:rzf_bstep|zfistep)', 'gtc/(?:rzf_kr|zfkrrho0)',
                     'gtc/rho0', 'data1d/field00-phi']
    post_template = (
        'tmpl_z111p', 'tmpl_contourf', 'tmpl_line', 'tmpl_sharextwinx')

    def _set_fignum(self, numseed=None):
        self._fignum = 'residual_zf'
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *ipsi*: int
            select psi in data1d results, 0<ipsi<mpsi, defalut mpis//2
        *nside*: int
            average 2*nside+1 points around *ipsi*, default 0
        *norm*: bool
            normalize phi_p00 by max(phi_p00) or not, default True
        *res_time*: [t0, t1]
            set residual time, t0<=time[x0:x1]<=t1
        *use_ra*: bool
            use psi or r/a, default False
        *npeakdel*: int
            rm *npeakdel* points from edge in axes 4, default 1
        *savsmooth*: bool
            use savgolay_filter to smooth results in axes 4 if True,
            or use average to smooth. defalut False
        '''
        ndstep, tstep, ndiag = self.pckloader.get_many(*self.extrakeys[:3])
        dt = tstep * ndiag
        _time = np.around(np.arange(0, ndstep) * dt, 8)
        _hist = self.pckloader.get(self.srckeys[0])
        bstep, kr, rho0 = self.pckloader.get_many(*self.extrakeys[3:6])
        _dat1d = self.pckloader.get(self.extrakeys[6])
        krrho0 = kr*rho0 if self.extrakeys[4] == 'gtc/rzf_kr' else kr
        if bstep % ndiag == 0:
            bindex = bstep // ndiag
            dlog.parm('bindex=%d' % bindex)
        else:
            bindex = bstep // ndiag + 1
            dlog.warning('bindex=bstep/ndiag=%.3f=%d' % (bstep/ndiag, bindex))
        maxidx, minidx = np.argmax(_hist[1]), np.argmin(_hist[1])
        if abs(_hist[1, maxidx]) < abs(_hist[1, minidx]):
            maxidx = minidx
        elif abs(_hist[1, maxidx]) == abs(_hist[1, minidx]):
            maxidx = max(maxidx, minidx)
        dlog.parm('maxindex=%d' % maxidx)
        if maxidx < bindex:
            dlog.warning('Shift bindex -> maxindex:%d!' % maxidx)
            bindex = maxidx
        elif maxidx > bindex:
            dlog.warning('maxindex:%d is bigger than bindex!' % maxidx)
        # cutoff data
        time = _time[bindex:]
        hiszf = _hist[1, bindex:]
        d1dzf = _dat1d[:, bindex:]
        maxidx -= bindex
        # select data1d
        mpsi = _dat1d.shape[0] - 1
        ipsi = int(kwargs.get('ipsi', mpsi//2))
        nside = int(kwargs.get('nside', 0))
        s1dzf = d1dzf[ipsi-nside:ipsi+nside+1].mean(axis=0)
        dlog.parm('Points beside bindex: %s, %s'
                  % (_hist[1, bindex-1:bindex+2], _dat1d[ipsi, bindex-1:bindex+2]))
        # norm
        norm = bool(kwargs.get('norm', True))
        if norm:
            hiszf = hiszf/hiszf[maxidx]
            s1dzf = s1dzf/s1dzf[maxidx]
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
            start, region_len = tools.findflat(hiszf, 5e-4*hiszf[maxidx])
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
                          value=mpsi//2,
                          description='ipsi:'),
                nside=dict(widget='IntSlider',
                           rangee=(0, mpsi//2, 1),
                           value=0,
                           description='nside:'),
                norm=dict(widget='Checkbox',
                          value=True,
                          description='normalize phi_p00:'),
                res_time=dict(widget='FloatRangeSlider',
                              rangee=[time[0], time[-1], dt],
                              value=[time[start], time[end]],
                              description='residual time:'),
                use_ra=dict(widget='Checkbox',
                            value=False,
                            description='Y: r/a'),
                npeakdel=dict(widget='IntSlider',
                              rangee=(0, 3, 1),
                              value=1,
                              description='npeak to rm:'),
                savsmooth=dict(widget='Checkbox',
                               value=False,
                               description='smooth: savgolay'))
        restime = [time[start], time[end]]
        npeakdel = max(min(int(kwargs.get('npeakdel', 1)), 3), 0)
        savsmooth = bool(kwargs.get('savsmooth', False))
        acckwargs = {'ipsi': ipsi, 'nside': nside, 'norm': norm,
                     'res_time': restime, 'use_ra': False,
                     'npeakdel': npeakdel, 'savsmooth': savsmooth}
        # 1 res
        hisres = hiszf[start:end].sum()/(end-start)
        hisres_err = hiszf[start:end].std()
        s1dres = s1dzf[start:end].sum()/(end-start)
        s1dres_err = s1dzf[start:end].std()
        dlog.parm("Get history, data1d residual: %.6f, %.6f"
                  % (hisres, s1dres))
        # 2 gamma
        mx = time[maxidx:start]
        hisgamma, hisfity = self.__gamma(
            hiszf[maxidx:start], mx, hisres, 'history')
        s1dgamma, s1dfity = self.__gamma(
            s1dzf[maxidx:start], mx, s1dres, 'data1d')
        # 3 w
        hiscosy, i1, i2, nT1, hisomega = self.__omega(
            hiszf[maxidx:start], mx, hisres, hisgamma[0], hisgamma[1], 'history')
        s1dcosy, i3, i4, nT2, s1domega = self.__omega(
            s1dzf[maxidx:start], mx, s1dres, s1dgamma[0], s1dgamma[1], 'data1d')
        # use_ra, arr2 [1,mpsi-1]
        Y1, y1label, ir = np.array(range(0, mpsi+1)), r'mpsi', None
        if kwargs.get('use_ra', False):
            try:
                arr2, a = self.pckloader.get_many('gtc/arr2', 'gtc/a_minor')
                Y1 = arr2[:, 1] / a  # index [0, mpsi-2]
            except Exception:
                dlog.warning("Cannot use r/a!", exc_info=1)
            else:
                y1label = r'$r/a$'
                acckwargs['use_ra'] = True
                ir = Y1[ipsi-1]
                # update d1dzf
                d1dzf = d1dzf[1:mpsi, :]
        # 4. res vs Y1/ipsi
        idx = tools.argrelextrema(d1dzf[:, maxidx])
        if npeakdel > 0 and idx.size - npeakdel*2 >= 2:
            idx = idx[npeakdel:-npeakdel]
        if not (ipsi in idx or ipsi-1 in idx):  # use_ra F/T
            if acckwargs['use_ra']:
                idx = np.insert(idx, 0, ipsi-1)
            else:
                idx = np.insert(idx, 0, ipsi)
            idx.sort()
        X4res = Y1[idx]
        _res = [d1dzf[i-nside:i+nside+1].mean(axis=0) for i in idx]
        N = end - start
        Yd1dres = np.array([abs(l[start:end].sum()/N) for l in _res])
        Yd1dmax = np.array([abs(l[maxidx]) for l in _res])
        if savsmooth:
            Yd1dresflt = tools.savgolay_filter(Yd1dres)
            Yd1dmaxflt = tools.savgolay_filter(Yd1dmax)
        else:
            Yd1dresflt = self.__average_filter(Yd1dres)
            Yd1dmaxflt = self.__average_filter(Yd1dmax)
        if norm:
            Yd1dres = np.array(Yd1dres/Yd1dmax)
            Yd1dmax = np.ones(len(idx))
            Yd1dresflt = Yd1dresflt/Yd1dmaxflt
            Yd1dmaxflt = Yd1dmax
        if acckwargs['use_ra']:
            idx = np.where(X4res == ir)[0][0]
        else:
            idx = np.where(X4res == ipsi)[0][0]
        s1dresflt = Yd1dresflt[idx]
        timemid = time[time.size//2]
        d1dzfmax = d1dzf[:, maxidx]/np.abs(d1dzf[:, maxidx]).max() * \
            0.372 * (timemid - time[0]) + timemid
        return dict(
            time=time, norm=norm,
            hiszf=hiszf,
            d1dzf=d1dzf, Y1=Y1, y1label=y1label,
            timemid=timemid, d1dzfmax=d1dzfmax,
            s1dzf=s1dzf, ipsi=ipsi, ir=ir,
            krrho0=krrho0,
            hisres=hisres, hisres_err=hisres_err,
            s1dres=s1dres, s1dres_err=s1dres_err, restime=restime,
            hisgamma=hisgamma, hisfity=hisfity,
            s1dgamma=s1dgamma, s1dfity=s1dfity, gammatime=mx,
            # 3
            hiscosy=hiscosy, hisomega=hisomega, hisnT=nT1,
            his_ot=[mx[i1], mx[i2]], his_oy=[hiscosy[i1], hiscosy[i2]],
            s1dcosy=s1dcosy, s1domega=s1domega, s1dnT=nT2,
            s1d_ot=[mx[i3], mx[i4]], s1d_oy=[s1dcosy[i3], s1dcosy[i4]],
            # 4
            Yd1dres=Yd1dres, Yd1dmax=Yd1dmax, X4res=X4res,
            Yd1dmaxflt=Yd1dmaxflt, Yd1dresflt=Yd1dresflt, s1dresflt=s1dresflt,
        ), acckwargs

    def __average_filter(self, arr):
        b = [None]*arr.size
        for i in range(arr.size):
            if i == 0:
                b[i] = (arr[i]+arr[i+1])/2.0
            elif i == arr.size-1:
                b[i] = (arr[i]+arr[i-1])/2.0
            else:
                b[i] = (arr[i-1]+2*arr[i]+arr[i+1])/4.0
        return np.array(b)

    def __gamma(self, zf, t, res, info):
        def f(x, a, b):
            return (zf[0]-res) * np.exp(-a*(x)**b)+res
        if zf[0]-res > 0:
            i = tools.argrelextrema(zf, m='max')
        else:
            i = tools.argrelextrema(zf, m='min')
        i = np.insert(i, 0, 0)
        _t = t[i] - t[0]
        _t[0] += 1e-25
        gamma, pcov, fity = tools.curve_fit(f, _t, zf[i], fitX=t-t[0])
        dlog.parm("Get %s gamma: (%.6f, %.6f)" % (info, gamma[0], gamma[1]))
        return gamma, fity

    def __omega(self, zf, t, res, g0, g1, info):
        cosy = (zf-res) * np.exp(g0*(t-t[0])**(g1))
        # my = tools.savgolay_filter(cosy, info='smooth zonal flow') # mess data
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
        fstr = r'\phi_{p00}'
        rzfstr = r'\widehat{\phi}_{p00}' if r['norm'] else fstr
        ax1 = dict(X=r['time'], Y=r['Y1'], Z=r['d1dzf'],
                   title=r'$%s, k_r\rho_0=%.6f$' % (fstr, r['krrho0']),
                   xlabel=r'time($R_0/c_s$)', ylabel=r['y1label'])
        ax1_1 = dict(LINE=[
            ([r['timemid'], r['timemid']], r['Y1'][[0, -1]]),
            (r['d1dzfmax'], r['Y1'], r'max vs r')])
        g1, g2 = r['hisgamma']
        g3, g4 = r['s1dgamma']
        ir = (r'$r=%.4f a$' % r['ir']) if r['ir'] is not None else ''
        ax2 = dict(LINE=[
            (r['time'], r['hiszf'], 'i=iflux'),
            (r['time'], r['s1dzf'], 'i=%d, %s' % (r['ipsi'], ir)),
            (r['restime'], [r['hisres'], r['hisres']],
                r'$Res(iflux)=%.4f$' % r['hisres']),
            (r['restime'], [r['s1dres'], r['s1dres']],
                r'$Res(%d)=%.4f$' % (r['ipsi'], r['s1dres'])),
            (r['gammatime'], r['hisfity'],
                r'i=iflux, $e^{-%.4f t^{%.4f}}$' % (g1, g2)),
            (r['gammatime'], r['s1dfity'],
                r'i=%d, $e^{-%.4f t^{%.4f}}$' % (r['ipsi'], g3, g4))],
            title=r'$%s$, residual $Res$, damping $\gamma$' % rzfstr,
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
            title=r'$%s$ remove damping, residual' % rzfstr,
            xlim=r['gammatime'][[0, -1]], xlabel=r'time($R_0/c_s$)',
        )
        LIM = 37.2
        cymin = max(r['hiscosy'].min(), r['s1dcosy'].min(), -LIM)
        cymax = min(r['hiscosy'].max(), r['s1dcosy'].max(), LIM)
        if cymax == LIM or cymin == -LIM or cymax - cymin >= LIM:
            dlog.warning('Set ax3 ylim!')
            ax3['ylim'] = [cymin, cymax]
        if ir:
            _lb = r'Res(%s)=%.4f' % (ir, r['s1dresflt'])
        else:
            _lb = r'Res(%d)=%.4f' % (r['ipsi'], r['s1dresflt'])
        ax4 = dict(
            YINFO=[{
                'left': [(r['Yd1dres'], r'$Res$'),
                         (r['Yd1dresflt'], r'$smooth\ %s$' % _lb)],
                'right': [(r['Yd1dmax'], r'$Max$'),
                          (r['Yd1dmaxflt'], r'$smooth\ Max$')], }],
            X=r['X4res'], xlabel=r['y1label'],
            title=r'residual $\left|%s\right|$' % rzfstr)
        return dict(zip_results=[
            ('tmpl_contourf', 221, ax1), ('tmpl_line', 221, ax1_1),
            ('tmpl_line', 222, ax2), ('tmpl_line', 223, ax3),
            ('tmpl_sharextwinx', 224, ax4),
        ])
