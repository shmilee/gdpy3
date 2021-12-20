# -*- coding: utf-8 -*-

# Copyright (c) 2019-2021 shmilee

'''
Source fortran code:

v3.14-22-g5a68f08d
------------------

snapshot.F90, subroutine snap_phi_zeta_psi
  do idx=1,msnap_nj
        j_list(idx)=idx*mtdiag/msnap_nj
  enddo
  mzeach=min(1536,mtheta(mpsi/2))/mtoroidal
  ......
  write(fdum,'("phi_dir/phi_zeta_psi_snap",i5.5,"_tor",i4.4,".out")')nsnap,myrank_toroidal
  if(myrank_toroidal==0)then
    ! parameters: shape of data; all selected j, last one is mtdiag
    write(iopotential,101)mzeach,mpsi+1, msnap_nj, j_list(:msnap_nj)
  endif
  write(iopotential,102)phiflux
'''

import numpy as np

from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog
from .snapshot import (
    _snap_get_timestr,
    SnapshotFieldSpectrumDigger, SnapshotFieldmDigger
)
from .. import tools

_all_Converters = ['SnapPhiZetaPsiConverter']
_all_Diggers = ['SnapPhiZetaPsiDigger', 'SnapPhiCorrLenDigger',
                'SnapPhiSpectrumDigger', 'SnapPhiTimeSpectrumDigger',
                'SnapPhiFieldnDigger']
__all__ = _all_Converters + _all_Diggers


class SnapPhiZetaPsiConverter(Converter):
    '''
    Snapshot phi(zeta,psi) Data

    Shape os array data is (mzeach*mtoroidal,mpsi+1)
    '''
    __slot__ = []
    nitems = '+'
    itemspattern = ['^phi_dir/phi_zeta_psi_(?P<section>snap\d{5})_tor\d{4}\.out$',
                    '.*/phi_dir/phi_zeta_psi_(?P<section>snap\d{5})_tor\d{4}\.out$']
    _short_files_subs = (0, '^(.*psi_snap\d{5}_tor)\d{4}\.out$', r'\1*.out')
    _datakeys = (
        # 1. parameters
        'mzeach', 'msnap_nj', 'j_list',
        'mpsi+1',
        # 2. phi(zeta,psi,msnap_nj), nj<=36
        r'phi_zeta_psi_%d'
    )

    @property
    def groupnote(self):
        return '%s/phi_zeta_psi' % self._group

    def _convert(self):
        '''Read 'phi_dir/phi_zeta_psi_snap%05d_tor%04d.out'.'''
        phi = []
        # tor0000.out
        f = self.files[0]
        with self.rawloader.get(f) as fid:
            # parameters
            mzeach, mpsi1, nj = (int(fid.readline()) for j in range(3))
            shape = (mzeach, mpsi1, nj)
            j_list = [int(fid.readline()) for j in range(nj)]
            # data
            outdata = np.array([float(n.strip()) for n in fid.readlines()])
            phi.extend(outdata.reshape(shape, order='F'))
        # tor0001.out ...
        for f in self.files[1:]:
            with self.rawloader.get(f) as fid:
                outdata = np.array([float(n.strip()) for n in fid.readlines()])
                phi.extend(outdata.reshape(shape, order='F'))
        phi = np.array(phi)
        mtoroidal = len(self.files)
        assert phi.shape == (mzeach*mtoroidal, mpsi1, nj)
        # 1. parameters
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:3]))
        sd = dict(mzeach=mzeach, msnap_nj=nj, j_list=j_list)
        # 2. data
        for idx, j in enumerate(j_list):
            key = self._datakeys[-1] % j
            clog.debug("Filling datakeys: %s ..." % key)
            sd[key] = phi[:, :, idx]
        return sd


class SnapPhiZetaPsiDigger(Digger):
    '''phi(zeta,psi) at theta=j/mtdiag*2pi'''
    __slots__ = ['_part', 'theta', 'timestr']
    nitems = '+'
    itemspattern = ['^(?P<section>snap\d{5})/phi_zeta_psi_(?P<j>\d+)',
                    '^(?P<section>snap\d{5})/j_list']
    commonpattern = ['gtc/tstep', 'gtc/arr2', 'gtc/a_minor']
    post_template = 'tmpl_contourf'

    def _set_fignum(self, numseed=None):
        j_list = self.pckloader.get(self.srckeys[1])
        j = int(self.section[1])
        assert j in j_list
        # j_list[-1] is mtdiag
        self._part = j / j_list[-1]
        self._fignum = 'phi_%03d_zeta_psi' % round(self._part*360)
        self.theta = r'$\theta=%.3f=%g^\circ$' % (
            round(self._part*2*np.pi, ndigits=3), self._part*360)
        self.timestr = _snap_get_timestr(self.group, self.pckloader)
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *use_ra*: bool
            use psi or r/a, default False
        '''
        Z = self.pckloader.get(self.srckeys[0])
        y, x = Z.shape
        if self.kwoptions is None:
            self.kwoptions = dict(
                use_ra=dict(widget='Checkbox',
                            value=False,
                            description='X: r/a'))
        # use_ra, arr2 [1,mpsi-1], so y0>=1, y1<=mpsi
        if kwargs.get('use_ra', False):
            try:
                arr2, a = self.pckloader.get_many('gtc/arr2', 'gtc/a_minor')
                rr = arr2[:, 1] / a  # index [0, mpsi-2]
                x0 = 1
                x1 = x - 1
                X = rr[x0-1:x1-1]
                Z = Z[:, x0:x1]
            except Exception:
                dlog.warning("Cannot use r/a!", exc_info=1)
            else:
                title = r'$\phi(\zeta,r)$, %s, %s' % (self.theta, self.timestr)
                xlabel = r'$r/a$'
                acckwargs = dict(use_ra=True)
        else:
            title = r'$\phi(\zeta,\psi)$, %s, %s' % (self.theta, self.timestr)
            xlabel = r'$\psi$(mpsi)'
            acckwargs = dict(use_ra=False)
            X = np.arange(0, x)
        return dict(X=X, Y=np.arange(0, y) / y * 2 * np.pi, Z=Z,
                    xlabel=xlabel, ylabel=r'$\zeta$', title=title), acckwargs

    def _post_dig(self, results):
        return results


class BreakDigDoc(Digger):
    pass


class SnapPhiCorrLenDigger(BreakDigDoc, SnapPhiZetaPsiDigger):
    '''phi(zeta,psi) correlation (d_zeta, d_psi) at at theta=j/mtdiag*2pi'''
    __slots__ = []
    post_template = ('tmpl_z111p', 'tmpl_contourf', 'tmpl_line')

    def _set_fignum(self, numseed=None):
        super(SnapPhiCorrLenDigger, self)._set_fignum(numseed=numseed)
        self._fignum = 'phi_%03d_corrlen' % round(self._part*360)
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *mdpsi*, *mdzeta*: int
            set dpsi dzeta range, max mpsi//2, mzeta//2
        *use_ra*: bool
            use psi or r/a, default True
        '''
        Z = self.pckloader.get(self.srckeys[0])
        y, x = Z.shape
        # use_ra, arr2 [1,mpsi-1], so y0>=1, y1<=mpsi
        if kwargs.get('use_ra', True):
            try:
                arr2, a = self.pckloader.get_many('gtc/arr2', 'gtc/a_minor')
                rr = arr2[:, 1] / a  # index [0, mpsi-2]
                Z = Z[:, 1:x-1]
                y, x = Z.shape
            except Exception:
                dlog.warning("Cannot use r/a!", exc_info=1)
                use_ra = False
            else:
                use_ra = True
        else:
            use_ra = False
        # if Z size is too large, cal corr will be very slow
        max_x, max_y = 400, 1536
        step_x = round(x/max_x) if x > max_x else 1
        step_y = round(y/max_y) if y > max_y else 1
        if step_x != 1 or step_y != 1:
            if use_ra:
                rr = rr[::step_x]
            Z = Z[::step_y, ::step_x]
            dlog.parm('Too large data of phi(zeta,psi), slice it: %s -> %s'
                      % ((y, x), Z.shape))
            y, x = Z.shape
        else:
            dlog.parm('Data shape of phi(zeta,psi) is %s.' % ((y, x),))
        maxmdpsi, maxmdzeta = int(x/2+1), int(y/2+1)
        mdpsi, mdzeta = kwargs.get('mdpsi', None), kwargs.get('mdzeta', None)
        if not (isinstance(mdpsi, int) and mdpsi <= maxmdpsi):
            mdpsi = x // 2
        if not (isinstance(mdzeta, int) and mdzeta <= maxmdzeta):
            Zz = Z[:, int(Z.argmax(axis=1).mean())]
            Zz = tools.savgolay_filter(Zz, info='phi(zeta)')
            index = (np.diff(np.sign(np.gradient(Zz))) < 0).nonzero()[0]
            mdzeta = int(np.diff(index).mean())
            # print(Zz,index)
            # print('---------------')
            #print(mdzeta, mdzeta < y//32, y//8)
            mdzeta *= 4 if mdzeta < y//32 else 3
            mdzeta = min(mdzeta, y//8)
        acckwargs = dict(mdpsi=mdpsi, mdzeta=mdzeta, use_ra=use_ra)
        dlog.parm("Use dpsi dzeta range: mdpsi=%s, mdzeta=%s. "
                  "Maximal mdpsi=%s, mdzeta=%s"
                  % (mdpsi, mdzeta, maxmdpsi, maxmdzeta))
        if self.kwoptions is None:
            self.kwoptions = dict(
                mdpsi=dict(
                    widget='IntSlider',
                    rangee=(1, maxmdpsi, 1),
                    value=mdpsi,
                    description='mdpsi:'),
                mdzeta=dict(
                    widget='IntSlider',
                    rangee=(1, maxmdzeta, 1),
                    value=mdzeta,
                    description='mdzeta:'),
                use_ra=dict(widget='Checkbox',
                            value=True,
                            description='X: r/a'))
        Xpsi = np.arange(0, mdpsi) * step_x
        Y = np.arange(0, mdzeta) * step_y / y * 2 * np.pi
        if use_ra:
            # print(rr, rr.size, Z.shape, step_x)
            title1 = r'Correlation $\phi(\Delta\zeta,\Delta r)$, %s, %s' % (
                self.theta, self.timestr)
            xlabel = r'$\Delta r/a$'
            tau, vdz, X = tools.correlation(
                Z, 0, y, 0, x, mdzeta, mdpsi, ruler_c=rr)
        else:
            title1 = r'Correlation $\phi(\Delta\zeta,\Delta\psi)$, %s, %s' % (
                self.theta, self.timestr)
            xlabel = r'$\Delta\psi(mpsi)$'
            tau, vdz, vdp = tools.correlation(Z, 0, y, 0, x, mdzeta, mdpsi)
            X = Xpsi
        mtau = tau.max(axis=0)
        index = np.where(mtau <= 1.0/np.e)[0]
        if index.size > 0:
            # line intersection
            i, j = index[0] - 1,  index[0]
            Lpsi, y = tools.intersection_4points(
                Xpsi[i], mtau[i], Xpsi[j], mtau[j],
                Xpsi[i], 1.0/np.e, Xpsi[j], 1.0/np.e)
            if use_ra:
                L, y = tools.intersection_4points(
                    X[i], mtau[i], X[j], mtau[j],
                    X[i], 1.0/np.e, X[j], 1.0/np.e)
            else:
                L = Lpsi
        else:
            L, Lpsi = X[-1], Xpsi[-1]  # over mdpsi
            dlog.parm("Increase mdpsi to find correlation length!")
        if use_ra:
            title2 = r'$\phi$ $C(\Delta r)$, $C_r(\Delta r=%.6f)=1/e$' % L
            dlog.parm("Find correlation length: L=%.6f, Lpsi=%.3f" % (L, Lpsi))
        else:
            title2 = r'$\phi$ $C(\Delta\psi)$, $C(\Delta\psi=%.3f)=1/e$' % Lpsi
            dlog.parm("Find correlation length: Lpsi=%.3f" % Lpsi)
        mtauz, Lz, title3 = self._find_correLz(tau, Y)
        return dict(X=X, Y=Y, tau=tau, mtau=mtau, L=L, Lpsi=Lpsi,
                    xlabel=xlabel, title1=title1, title2=title2,
                    xname=r'r' if use_ra else r'\psi',
                    Lr=L, mtauz=mtauz, Lz=Lz, title3=title3), acckwargs

    @staticmethod
    def _find_correLz(tau, Y):
        mtau = tau.max(axis=1)
        index = np.where(mtau <= 1.0/np.e)[0]
        if index.size > 0:
            # line intersection
            i, j = index[0] - 1,  index[0]
            Lz, y = tools.intersection_4points(
                Y[i], mtau[i], Y[j], mtau[j],
                Y[i], 1.0/np.e, Y[j], 1.0/np.e)
        else:
            Lz = Y[-1]  # over mdzeta
            dlog.parm("Increase mdzeta to find correlation length!")
        title3 = r'$\phi$ $C(\Delta\zeta)$, $C(\Delta\zeta=%.3f)=1/e$' % Lz
        dlog.parm("Find correlation length: Lzeta=%.3f" % Lz)
        return mtau, Lz, title3

    def _post_dig(self, results):
        r = results
        ax1_calc = dict(
            X=r['X'], Y=r['Y'], Z=r['tau'], clabel_levels=[1/np.e],
            title=r['title1'], xlabel=r['xlabel'], ylabel=r'$\Delta\zeta$')
        ax2_calc = dict(
            LINE=[
                (r['X'], r['mtau'], r'$C_r(\Delta %s)$' % r['xname']),
                ([r['X'][0], r['X'][-1]], [1/np.e, 1/np.e], '1/e'),
            ],
            title=r['title2'],
            xlabel=r['xlabel'],
            xlim=[r['X'][0], r['X'][-1]],
            ylim=[0 if r['mtau'].min() > 0 else r['mtau'].min(), 1],
        )
        if 'mtauz' in results and 'Lz' in results:
            mtauz, Lz, title3 = r['mtauz'], r['Lz'], r['title3']
        else:
            # maybe old results, without Lz
            mtauz, Lz, title3 = self._find_correLz(r['tau'], r['Y'])
        ax3_calc = dict(
            LINE=[
                (r['Y'], mtauz, r'$C_r(\Delta\zeta)$'),
                ([r['Y'][0], r['Y'][-1]], [1/np.e, 1/np.e], '1/e'),
            ],
            title=title3,
            xlabel=r'$\Delta\zeta$',
            xlim=[r['Y'][0], r['Y'][-1]],
            ylim=[0 if mtauz.min() > 0 else mtauz.min(), 1],
        )
        return dict(zip_results=[
            ('tmpl_contourf', 211, ax1_calc),
            ('tmpl_line', 223, ax2_calc),
            ('tmpl_line', 224, ax3_calc),
        ])


class SnapPhiSpectrumDigger(BreakDigDoc, SnapPhiZetaPsiDigger,
                            SnapshotFieldSpectrumDigger):
    '''field phi toroidal or r spectra.'''
    __slots__ = []
    nitems = '+'
    itemspattern = ['^(?P<section>snap\d{5})/phi_zeta_psi_(?P<j>\d+)',
                    '^(?P<section>snap\d{5})/j_list',
                    '^(?P<s>snap\d{5})/mtoroidal',
                    '^(?P<s>snap\d{5})/mzeach',
                    '^(?P<s>snap\d{5})/mpsi\+1']
    post_template = ('tmpl_z111p', 'tmpl_line')

    def _set_fignum(self, numseed=None):
        super(SnapPhiSpectrumDigger, self)._set_fignum(numseed=numseed)
        self._fignum = 'phi_%03d_spectrum' % round(self._part*360)
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *nmode*, *rmode*: int
            set toroidal or radial range
        *smooth*: bool, default False
            smooth spectrum results or not
        *norm*: bool, default False
            normalize spectrum results or not
        '''
        data, _, mtor, mzeach, mpsi1 = self.pckloader.get_many(*self.srckeys)
        mtgrid = mtor*mzeach  # toroidal grids
        if data.shape != (mtgrid, mpsi1):
            dlog.error("Invalid phi data shape!")
            return {}, {}
        acckwargs = self._set_params(
            kwargs, mtgrid, mpsi1,
            mkey='nmode', pkey='rmode', mtext='Toroidal', ptext='radial')
        nmode, rmode = acckwargs['nmode'], acckwargs['rmode']
        X1, X2 = np.arange(1, nmode + 1), np.arange(1, rmode + 1)
        smooth, norm = acckwargs['smooth'], acckwargs['norm']
        Y1, Y2, idx1, idx2 = self._get_spectrum(
            nmode, rmode, data, mtgrid, mpsi1, smooth, norm)
        n, rp = X1[idx1], X2[idx2]
        return dict(
            nX=X1, toroidal_spectrum=Y1, nmode=nmode, n=n,
            rX=X2, radial_spectrum=Y2, rmode=rmode, rp=rp,
            title=r'$\phi$(%s), %s' % (self.theta, self.timestr),
        ), acckwargs

    def _post_dig(self, results):
        r = results
        max_p = 1.05 * r['toroidal_spectrum'].max()
        ax1_calc = dict(LINE=[
            (r['nX'], r['toroidal_spectrum']),
            ([r['n'], r['n']], [0, max_p], r'$n_{pmax}=%d$' % r['n'])],
            xlabel='n', ylabel='toroidal spectrum',
            xlim=[0, r['nmode']])
        max_p = 1.05 * r['radial_spectrum'].max()
        ax2_calc = dict(LINE=[
            (r['rX'], r['radial_spectrum']),
            ([r['rp'], r['rp']], [0, max_p], r'$rp_{pmax}=%d$' % r['rp'])],
            xlabel='r(psi)', ylabel='radial spectrum',
            xlim=[1, r['rmode']])
        return dict(zip_results=[
            ('tmpl_line', 211, ax1_calc),
            ('tmpl_line', 212, ax2_calc),
        ], suptitle=r'%s, n=%d, rp=%d' % (r['title'], r['n'], r['rp']))


class SnapPhiTimeSpectrumDigger(SnapPhiSpectrumDigger):
    '''field phi toroidal or r spectra as time varied.'''
    __slots__ = ['msnap']
    nitems = '+'
    itemspattern = ['^(?P<section>snap)\d{5}/phi_zeta_psi_(?P<j>\d+)',
                    '^(?P<section>snap)\d{5}/j_list',
                    '^(?P<s>snap)\d{5}/mtoroidal',
                    '^(?P<s>snap)\d{5}/mzeach',
                    '^(?P<s>snap)\d{5}/mpsi\+1']

    def _set_fignum(self, numseed=None):
        assert len(self.srckeys) % len(self.itemspattern) == 0
        self.msnap = len(self.srckeys) // len(self.itemspattern)
        j_list = self.pckloader.get(self.srckeys[self.msnap])
        j = int(self.section[1])
        assert j in j_list
        # j_list[-1] is mtdiag
        self._part = j / j_list[-1]
        self._fignum = 'phi_%03d_spectrum' % round(self._part*360)
        self.theta = r'$\theta=%.3f=%g^\circ$' % (
            round(self._part*2*np.pi, ndigits=3), self._part*360)
        self.kwoptions = None

    def _dig(self, kwargs):
        '''*tcutoff*: [t0,t1], t0 t1 float
            t0<=time[x0:x1]<=t1
        '''
        mtor, mzeach, mpsi1 = self.pckloader.get_many(
            self.srckeys[2*self.msnap], self.srckeys[3*self.msnap],
            self.srckeys[4*self.msnap])
        mtgrid = mtor*mzeach  # toroidal grids
        acckwargs = self._set_params(
            kwargs, mtgrid, mpsi1,
            mkey='nmode', pkey='rmode', mtext='Toroidal', ptext='radial')
        nmode, rmode = acckwargs['nmode'], acckwargs['rmode']
        X1, X2 = np.arange(1, nmode + 1), np.arange(1, rmode + 1)
        # rm first item in data
        all_data = self.pckloader.get_many(*self.srckeys[1:self.msnap])
        tstep = self.pckloader.get('gtc/tstep')
        time = [self.srckeys[idx].split('/')[0] for idx in range(self.msnap)]
        time = np.around(np.array(  # rm first item in time
            [int(t.replace('snap', '')) * tstep for t in time[1:]]), 5)
        if len(time) < 2:
            dlog.error("Less than 3 phi snapshots!")
            return {}, {}
        dt = time[-1] - time[-2]
        if 'tcutoff' not in self.kwoptions:
            self.kwoptions['tcutoff'] = dict(
                widget='FloatRangeSlider',
                rangee=[time[0], time[-1], dt],
                value=[time[0], time[-1]],
                description='time cutoff:')
        acckwargs['tcutoff'] = [time[0], time[-1]]
        i0, i1 = 0, time.size
        if 'tcutoff' in kwargs:
            t0, t1 = kwargs['tcutoff']
            idx = np.where((time >= t0) & (time < t1 + dt))[0]
            if idx.size > 0:
                i0, i1 = idx[0], idx[-1]+1
                acckwargs['tcutoff'] = [time[i0], time[i1-1]]
                time = time[i0:i1]
            else:
                dlog.warning('Cannot cutoff: %s <= time <= %s!' % (t0, t1))
        YT1, YT2, nY, rpY = [], [], [], []
        dlog.info('%d snapshot phi data to do ...' % (i1 - i0))
        _idxlog = (i1 - i0) // 10
        for idx in range(i0, i1):
            if idx % _idxlog == 0 or idx == i1 - 1:
                dlog.info('Calculating [%d/%d] %s' % (
                    idx+1-i0, i1 - i0, self.srckeys[idx]))
            data = all_data[idx]
            if data.shape != (mtgrid, mpsi1):
                dlog.error("Invalid phi data shape!")
                return {}, {}
            Y1, Y2, idx1, idx2 = self._get_spectrum(
                nmode, rmode, data, mtgrid, mpsi1,
                acckwargs['smooth'], acckwargs['norm'])
            YT1.append(Y1)
            YT2.append(Y2)
            nY.append(X1[idx1])
            rpY.append(X2[idx2])
        YT1, YT2 = np.array(YT1).T, np.array(YT2).T
        nY, rpY = np.array(nY), np.array(rpY)
        return dict(
            nX=X1, nY=nY, toroidal_spectrum=YT1, nmode=nmode,
            rX=X2, rpY=rpY, radial_spectrum=YT2, rmode=rmode,
            time=time, title=r'$\phi$(%s)' % self.theta,
        ), acckwargs

    def _post_dig(self, results):
        r = results
        ax1_calc = dict(X=r['time'], Y=r['nX'], Z=r['toroidal_spectrum'],
                        xlabel=r'time($R_0/c_s$)', ylabel='n',
                        title=r'toroidal spectrum of %s' % r'$\phi$',
                        xlim=[r['time'][0], r['time'][-1]])
        ax2_calc = dict(X=r['time'], Y=r['rX'], Z=r['radial_spectrum'],
                        xlabel=r'time($R_0/c_s$)', ylabel='r(psi)',
                        title=r'radial spectrum of %s' % r'$\phi$',
                        xlim=[r['time'][0], r['time'][-1]])
        return dict(zip_results=[
            ('tmpl_contourf', 211, ax1_calc),
            ('tmpl_line', 211, dict(LINE=[(r['time'], r['nY'], 'max n')])),
            ('tmpl_contourf', 212, ax2_calc),
            ('tmpl_line', 212, dict(LINE=[(r['time'], r['rpY'], 'max rp')])),
        ], suptitle=r['title'])


class SnapPhiFieldnDigger(SnapshotFieldmDigger):
    '''profile of field_n'''
    __slots__ = ['_part']
    nitems = '+'
    itemspattern = ['^(?P<section>snap\d{5})/phi_zeta_psi_(?P<j>\d+)',
                    '^(?P<section>snap\d{5})/j_list',
                    '^(?P<s>snap\d{5})/mpsi\+1']
    commonpattern = ['gtc/tstep', 'gtc/arr2', 'gtc/a_minor']
    post_template = 'tmpl_line'

    def _set_fignum(self, numseed=None):
        j_list = self.pckloader.get(self.srckeys[1])
        j = int(self.section[1])
        assert j in j_list
        # j_list[-1] is mtdiag
        self._part = j / j_list[-1]
        self._fignum = 'phi_%03d_fieldn' % round(self._part*360)
        self.kwoptions = None

    def _dig(self, kwargs):
        timestr = _snap_get_timestr(self.group, self.pckloader)
        theta = r'$\theta=%.2f=%g^\circ$' % (
            round(self._part*2*np.pi, ndigits=2), self._part*360)
        data, j_list, mpsi1, dt, arr2, a = self.pckloader.get_many(
            *self.srckeys, *self.common)
        Lz, Lr = data.shape
        if Lr != mpsi1:
            dlog.error("Invalid phi(zeta,psi) shape!")
            return {}, {}
        rr = arr2[:, 1] / a
        fieldn = []
        for ipsi in range(1, mpsi1 - 1):
            y = data[:, ipsi]
            dy_ft = np.fft.fft(y)*Lz / 8  # why *Lz / 8
            fieldn.append(abs(dy_ft[:Lz//2]))
        fieldn = np.array(fieldn).T
        zlist, acckwargs, rr_s, Y_s, dr, dr_fwhm, envY, envXp, envYp, envXmax, envYmax = \
            self._remove_add_some_lines(fieldn, rr, kwargs)
        return dict(
            rr=rr, fieldn=fieldn, zlist=zlist,
            rr_s=rr_s, Y_s=Y_s, dr=dr, dr_fwhm=dr_fwhm,
            envY=envY, envXp=envXp, envYp=envYp,
            envXmax=envXmax, envYmax=envYmax,
            title=r'$\left|\phi_n(r)\right|$, %s, %s' % (theta, timestr)
        ), acckwargs

    def _post_dig(self, results):
        r = results
        if r['zlist'] == 'all':
            mz, _ = r['fieldn'].shape
            zlist = range(mz)
        else:
            zlist = r['zlist']
        LINE = [(r['rr'], r['fieldn'][z, :]) for z in zlist]
        if r['dr'] != 'n':
            LINE.append(
                (r['rr_s'], r['Y_s'], r'$\delta r/a(gap,fwhm)=%.6f,%.6f$'
                 % (r['dr'], r['dr_fwhm'])))
        if type(r['envY']) is np.ndarray and type(r['envYp']) is np.ndarray:
            LINE.append((r['rr'], r['envY'],
                         'envelope, $r/a(max)=%.6f$' % r['envXmax']))
            dx = r['envXp'][-1] - r['envXp'][0]
            halfY = r['envYmax'] / np.e
            flatYp = np.linspace(halfY, halfY, len(r['envXp']))
            LINE.append((r['envXp'], flatYp, r'$\Delta r/a(1/e) = %.6f$' % dx))
        r0, r1 = np.round(r['rr'][[0, -1]], decimals=2)
        return dict(LINE=LINE, title=r['title'],
                    xlabel=r'$r/a$', xlim=[r0, r1])
