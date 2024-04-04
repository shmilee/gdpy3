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
from .gtc import Ndigits_tstep

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
    post_template = ('tmpl_z111p', 'tmpl_contourf',
                     'tmpl_line', 'tmpl_sharextwinx')
    __particles = dict(i='ion', e='electron', f='fastion')

    def _set_fignum(self, numseed=None):
        self.particle = self.__particles[self.section[1]]
        self._fignum = '%s_density' % self.particle
        self.kwoptions = None

    def _get_title(self):
        return r'%s $\delta n(r,t)$' % self.particle

    def _dig(self, kwargs):
        '''*t*: float
            set nearest time for density(t), defalut time(rzf_bstep) or time/2
        '''
        results, acckwargs = super(Data1dDensityDigger, self)._dig(kwargs)
        # X, Y, X, ylabel, title
        X, Z = results['X'], results['Z']
        yl, xl = Z.shape
        # find bstep
        ndiag = self.pckloader.get('gtc/ndiag')
        if 'gtc/rzf_bstep' in self.pckloader:
            idx = self.pckloader.get('gtc/rzf_bstep')
            idx = idx//ndiag if idx < xl else xl//2
        elif 'gtc/zfistep' in self.pckloader:
            idx = self.pckloader.get('gtc/zfistep')
            idx = idx//ndiag if idx < xl else xl//2
        else:
            idx = xl//2
        if 't' not in self.kwoptions:
            self.kwoptions['t'] = dict(widget='FloatSlider',
                                       rangee=(X[0], X[-1], X[1]-X[0]),
                                       value=X[idx],
                                       description='select t:')
        if 't' in kwargs:
            t = float(kwargs.get('t'))
            idx = (np.abs(X-t)).argmin()
        results['t'] = X[idx]
        acckwargs['t'] = X[idx]
        results['dnt'] = Z[:, idx-2:idx+2].mean(axis=1)
        index = tools.argrelextrema(results['dnt'])
        extrema = [np.abs(Z[index, i]).mean() for i in range(xl)]
        results['extrema'] = np.array(extrema)
        return results, acckwargs

    def _post_dig(self, results):
        r = results
        dnt = r['dnt']/max(r['dnt'].max(), abs(r['dnt'].min()))
        A = min(abs(r['t']-r['X'][0]), abs(r['X'][-1]-r['t']))
        dnt = r['t'] + 0.66*A*dnt
        lb = r'%s $<\delta n(r)>(t)$, amplitude $A$' % self.particle
        yinfo = {'left': [], 'right': [(r['extrema'], lb)], 'rylabel': r'$A$'}
        zip_results = [
            ('tmpl_contourf', 111, dict(
                X=r['X'], Y=r['Y'], Z=r['Z'], title=r['title'],
                xlabel=r'time($R_0/c_s$)', ylabel=r['ylabel'])),
            ('tmpl_line', 111, dict(LINE=[
                ([], []), ([r['t'], r['t']], r['Y'][[0, -1]]),
                (dnt, r['Y'], r'$\delta n(r,t=%.3f)$' % r['t'])],
                legend_kwargs={'loc': 'lower center'})),
            ('tmpl_sharextwinx', 111, dict(
                X=r['X'], YINFO=[yinfo],
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
        *p00rms*: bool
            use phi00rms instead of phi00 in history data or not, default False
        *ipsi*: int
            select psi in data1d results, 0<ipsi<mpsi, defalut mpsi//2
        *nside*: int
            average 2*nside+1 points around *ipsi*, default 1
        *norm*: bool
            normalize phi_p00 by max(phi_p00) or not, default True
        *res_time*: [t0, t1]
            set residual time, t0<=time[x0:x1]<=t1
        *use_ra*: bool
            use psi or r/a, default False
        *npeakselect*: int
            plot 2*npeakselect+1 peaks around *ipsi* in axes 4, default 3, max 12
        *npeakside*: int
            use 2*npeakside+1 peaks around *ipsi*
            to calculate RMSE, Delta of residual in axes 4, defalut 1, max 5
        *savsmooth*: bool
            use savgolay_filter to smooth results in axes 4 if True,
            or use average to smooth. defalut False
        '''
        ndstep, tstep, ndiag = self.pckloader.get_many(*self.extrakeys[:3])
        tstep = round(tstep, Ndigits_tstep)
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
        p00rms = bool(kwargs.get('p00rms', False))
        _hisidx = 2 if p00rms else 1
        maxidx, minidx = np.argmax(_hist[_hisidx]), np.argmin(_hist[_hisidx])
        if abs(_hist[_hisidx, maxidx]) < abs(_hist[_hisidx, minidx]):
            maxidx = minidx
        elif abs(_hist[_hisidx, maxidx]) == abs(_hist[_hisidx, minidx]):
            maxidx = max(maxidx, minidx)
        dlog.parm('maxindex=%d' % maxidx)
        if maxidx < bindex:
            dlog.warning('Shift bindex -> maxindex:%d!' % maxidx)
            bindex = maxidx
        elif maxidx > bindex:
            dlog.warning('maxindex:%d is bigger than bindex!' % maxidx)
        # cutoff data
        time = _time[bindex:]
        hiszf = _hist[_hisidx, bindex:]
        d1dzf = _dat1d[:, bindex:]
        maxidx -= bindex
        # select data1d
        mpsi = _dat1d.shape[0] - 1
        ipsi = int(kwargs.get('ipsi', mpsi//2))
        nside = int(kwargs.get('nside', 1))
        s1dzf = d1dzf[ipsi-nside:ipsi+nside+1].mean(axis=0)
        dlog.parm('Points beside bindex: %s, %s'
                  % (_hist[_hisidx, bindex-1:bindex+2], _dat1d[ipsi, bindex-1:bindex+2]))
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
                if start <= maxidx:
                    dlog.warning("The res_time range may be too long/wide!")
                    start = maxidx + 2
                    if end <= start:
                        end = start + 1
            else:
                dlog.warning('Cannot set residual time: %s <= time <= %s!'
                             % (start, end))
                start, end = None, None
        if start is None:
            start, region_len = tools.findflat(hiszf, 5e-4*hiszf[maxidx])
            if region_len == 0 or start <= maxidx:
                start = maxidx + hiszf[maxidx:].size // 2
                region_len = max(hiszf[maxidx:].size // 4, 2)
            end = start + region_len - 1
            # dlog.debug('res_time_end(2): %s ' % time[end])
        dlog.parm("Find residual time: [%s,%s], index: [%s,%s]."
                  % (time[start], time[end], start, end))
        if self.kwoptions is None:
            self.kwoptions = dict(
                p00rms=dict(widget='Checkbox',
                            value=False,
                            description='use phi00_RMS:'),
                ipsi=dict(widget='IntSlider',
                          rangee=(0, mpsi, 1),
                          value=mpsi//2,
                          description='ipsi:'),
                nside=dict(widget='IntSlider',
                           rangee=(0, mpsi//2, 1),
                           value=1,
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
                npeakselect=dict(widget='IntSlider',
                                 rangee=(0, 12, 1),
                                 value=3,
                                 description='npeak to plot:'),
                npeakside=dict(widget='IntSlider',
                               rangee=(0, 5, 1),
                               value=1,
                               description='npeak used to cal RMSE:'),
                savsmooth=dict(widget='Checkbox',
                               value=False,
                               description='smooth: savgolay'))
        restime = [time[start], time[end]]
        npeakselect = max(min(int(kwargs.get('npeakselect', 3)), 12), 0)
        npeakside = max(min(int(kwargs.get('npeakside', 1)), 5), 0)
        savsmooth = bool(kwargs.get('savsmooth', False))
        acckwargs = {'p00rms': p00rms, 'ipsi': ipsi, 'nside': nside,
                     'norm': norm, 'res_time': restime, 'use_ra': False,
                     'npeakselect': npeakselect, 'npeakside': npeakside,
                     'savsmooth': savsmooth}
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
        idx = tools.argrelextrema(
            d1dzf[:, maxidx:maxidx+nside+1].mean(axis=1))
        add_ipsi, ipsi_use = True, None
        # print(ipsi, ':::', idx)
        ipsi_side = range(1, max(2, nside)+1)
        for ii in [ipsi] + list(np.array([
                (ipsi-i, ipsi+i) for i in ipsi_side]).flatten()):
            if ii in idx:
                add_ipsi = False
                ipsi_use = ii
                break
        if add_ipsi:
            # use_ra F/T
            if acckwargs['use_ra']:
                ipsi_use = ipsi-1
            else:
                ipsi_use = ipsi
            idx = np.insert(idx, 0, ipsi_use)
            idx.sort()
        ipsi_idx = np.where(idx == ipsi_use)[0][0]
        if ipsi_idx-npeakselect >= 0 and ipsi_idx+npeakselect+1 <= idx.size:
            idx = idx[ipsi_idx-npeakselect:ipsi_idx+npeakselect+1]
            ipsi_idx = np.where(idx == ipsi_use)[0][0]
        else:
            dlog.warning("Cannot set npeakselect >= Npeak/2, use all!")
        # print(idx)
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
            Yd1dres = Yd1dres/Yd1dmax
            Yd1dres[Yd1dres > 1.0] = 1.0
            Yd1dmax = np.ones(len(idx))
            Yd1dresflt = Yd1dresflt/Yd1dmaxflt
            Yd1dresflt[Yd1dresflt > 1.0] = 1.0
            Yd1dmaxflt = Yd1dmax
        s1dresflt = Yd1dresflt[ipsi_idx]
        timemid = time[time.size//2]
        d1dzfmax = d1dzf[:, maxidx]/np.abs(d1dzf[:, maxidx]).max() * \
            0.372 * (timemid - time[0]) + timemid
        if ipsi_idx - npeakside >= 0 and ipsi_idx + npeakside + 1 <= len(idx):
            slc = range(ipsi_idx-npeakside, ipsi_idx+npeakside+1)  # select
            Yd1dresrmse = np.sqrt(np.mean((Yd1dresflt[slc]-Yd1dres[slc])**2))
            Yd1dresfltdelta = Yd1dresflt[slc].max() - Yd1dresflt[slc].min()
        else:
            dlog.warning("Cannot set 2*npeakside+1 > Npeak, only use *ipsi*!")
            slc = [ipsi_idx]
            Yd1dresrmse = np.abs(s1dresflt - Yd1dres[ipsi_idx])
            Yd1dresfltdelta = 0.0
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
            Yd1dresrmse=Yd1dresrmse, Yd1dresfltdelta=Yd1dresfltdelta,
            Yd1dresfltslc=np.array(slc),
        ), acckwargs

    def __average_filter(self, arr):
        if arr.size >= 3:
            b = []
            for i in range(arr.size):
                if i == 0:
                    b.append((arr[i]+arr[i+1])/2.0)
                elif i == arr.size-1:
                    b.append((arr[i]+arr[i-1])/2.0)
                else:
                    b.append((arr[i-1]+2*arr[i]+arr[i+1])/4.0)
            return np.array(b)
        else:
            return arr

    def __gamma(self, zf, t, res, info):
        try:
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
        except Exception:
            dlog.warning("Failed to get fitting gamma!", exc_info=1)
            gamma = np.array([0.0, 0.0])
            fity = np.zeros(len(t))
        dlog.parm("Get %s gamma: (%.6f, %.6f)" % (info, gamma[0], gamma[1]))
        return gamma, fity

    def __omega(self, zf, t, res, g0, g1, info):
        try:
            cosy = (zf-res) * np.exp(g0*(t-t[0])**(g1))
            # my = tools.savgolay_filter(cosy, info='smooth zonal flow') # mess data
            index = tools.argrelextrema(cosy, m='both')
            if len(index) >= 2:
                idx1, idx2, nT = index[0], index[-1], (len(index) - 1) / 2
                omega = 2 * np.pi * nT / (t[idx2] - t[idx1])
            else:
                raise ('No enough period!')
        except Exception:
            dlog.warning("Failed to get omega!", exc_info=1)
            cosy, idx1, idx2, nT, omega = zf-res, 0, 1, 0, 0
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
            (r['time'], r['hiszf'], 'history'),
            (r['time'], r['s1dzf'], 'i=%d, %s' % (r['ipsi'], ir)),
            (r['restime'], [r['hisres'], r['hisres']],
                r'$Res(history)=%.4f$' % r['hisres']),
            (r['restime'], [r['s1dres'], r['s1dres']],
                r'$Res(%d)=%.4f$' % (r['ipsi'], r['s1dres'])),
            (r['gammatime'], r['hisfity'],
                r'history, $e^{-%.4f t^{%.4f}}$' % (g1, g2)),
            (r['gammatime'], r['s1dfity'],
                r'i=%d, $e^{-%.4f t^{%.4f}}$' % (r['ipsi'], g3, g4))],
            title=r'$%s$, residual $Res$, damping $\gamma$' % rzfstr,
            xlim=r['time'][[0, -1]], xlabel=r'time($R_0/c_s$)',
            legend_kwargs=dict(loc='upper right'),
        )
        ax3 = dict(LINE=[
            (r['gammatime'], r['hiscosy'], 'history'),
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
        # Yd1dresfltslc
        slc_x = r['X4res'][r['Yd1dresfltslc']]
        slc_y = r['Yd1dresflt'][r['Yd1dresfltslc']]
        slc_lb = r'$RMSE=%.6f, \Delta=%.6f$' % (
            r['Yd1dresrmse'], r['Yd1dresfltdelta'])
        ax4 = dict(
            YINFO=[{
                'left': [(r['Yd1dres'], r'$Res$'),
                         (r['Yd1dresflt'], r'$smooth\ %s$' % _lb),
                         (slc_x, slc_y, slc_lb)],
                'right': [(r['Yd1dmax'], r'$Max$'),
                          (r['Yd1dmaxflt'], r'$smooth\ Max$')],
                'rlegend': dict(loc='lower right'), }],
            X=r['X4res'], xlabel=r['y1label'],
            title=r'residual $\left|%s\right|$' % rzfstr)
        return dict(zip_results=[
            ('tmpl_contourf', 221, ax1), ('tmpl_line', 221, ax1_1),
            ('tmpl_line', 222, ax2), ('tmpl_line', 223, ax3),
            ('tmpl_sharextwinx', 224, ax4),
        ])
