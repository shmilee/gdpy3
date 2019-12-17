# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

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
from .snapshot import _snap_get_timestr, SnapshotFieldmDigger
from .. import tools

__all__ = ['SnapPhiZetaPsiConverter',
           'SnapPhiZetaPsiDigger', 'SnapPhiCorrLenDigger',
           'SnapPhiFieldnDigger']


class SnapPhiZetaPsiConverter(Converter):
    '''
    Snapshot phi(zeta,psi) Data

    Shape os array data is (mzeach*mtoroidal,mpsi+1)
    '''
    __slot__ = []
    nitems = '+'
    itemspattern = ['^phi_dir/phi_zeta_psi_(?P<section>snap\d{5})_tor\d{4}\.out$',
                    '.*/phi_dir/phi_zeta_psi_(?P<section>snap\d{5})_tor\d{4}\.out$']
    _datakeys = (
        # 1. parameters
        'mzeach', 'msnap_nj', 'j_list',
        'mpsi+1',
        # 2. phi(zeta,psi,msnap_nj), nj<=36
        r'phi_zeta_psi_%d'
    )

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
        self.theta = r'$\theta=%.2f=%d^\circ$' % (
            round(self._part*2*np.pi, ndigits=2), round(self._part*360))
        self.timestr = _snap_get_timestr(self.group, self.pckloader)
        self.kwoptions = None

    def _dig(self, **kwargs):
        '''
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


class SnapPhiCorrLenDigger(SnapPhiZetaPsiDigger):
    '''phi(zeta,psi) correlation (d_zeta, d_psi) at at theta=j/mtdiag*2pi'''
    __slots__ = []
    post_template = 'tmpl_z111p'

    def _set_fignum(self, numseed=None):
        super(SnapPhiCorrLenDigger, self)._set_fignum(numseed=numseed)
        self._fignum = 'phi_%03d_corrlen' % round(self._part*360)
        self.kwoptions = None

    def _dig(self, **kwargs):
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
            mdzeta = y // 24
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
        return dict(X=X, Y=Y, tau=tau, mtau=mtau, L=L, Lpsi=Lpsi,
                    xlabel=xlabel, title1=title1, title2=title2,
                    xname=r'r' if use_ra else r'\psi'), acckwargs

    def _post_dig(self, results):
        r = results
        ax1_calc = dict(X=r['X'], Y=r['Y'], Z=r['tau'], title=r['title1'],
                        xlabel=r['xlabel'], ylabel=r'$\Delta\zeta$')
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
        return dict(zip_results=[
            ('tmpl_contourf', 211, ax1_calc),
            ('tmpl_line', 212, ax2_calc),
        ])


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

    def _dig(self, **kwargs):
        timestr = _snap_get_timestr(self.group, self.pckloader)
        theta = r'$\theta=%.2f=%d^\circ$' % (
            round(self._part*2*np.pi, ndigits=2), round(self._part*360))
        data, j_list, mpsi1, dt, arr2, a = self.pckloader.get_many(
            *self.srckeys, *self.common)
        Lz, Lr = data.shape
        if Lr != mpsi1:
            log.error("Invalid phi(zeta,psi) shape!")
            return
        rr = arr2[:, 1] / a
        fieldn = []
        for ipsi in range(1, mpsi1 - 1):
            y = data[:, ipsi]
            dy_ft = np.fft.fft(y)*Lz / 8  # why *Lz / 8
            fieldn.append(abs(dy_ft[:Lz//2]))
        fieldn = np.array(fieldn).T
        zlist, acckwargs, envY, envXp, envYp, envXmax, envYmax = \
            self._remove_add_some_lines(fieldn, rr, kwargs)
        return dict(
            rr=rr, fieldn=fieldn, zlist=zlist,
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
