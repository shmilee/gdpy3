#!/usr/bin/env python
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
from .snapshot import _snap_get_timestr
from .. import tools

__all__ = ['SnapPhiZetaPsiConverter',
           'SnapPhiZetaPsiDigger', 'SnapPhiCorrLenDigger']


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
    commonpattern = ['gtc/tstep']
    post_template = 'tmpl_contourf'

    def _set_fignum(self, numseed=None):
        j_list = self.pckloader.get(self.srckeys[1])
        j = int(self.section[1])
        assert j in j_list
        # j_list[-1] is mtdiag
        self._part = j / j_list[-1]
        self._fignum = 'phi_zeta_psi_%03d' % round(self._part*360)
        self.theta = r'$\theta=%.2f=%d^\circ$' % (
            round(self._part*2*np.pi, ndigits=2), round(self._part*360))
        self.timestr = _snap_get_timestr(self.group, self.pckloader)

    def _dig(self, **kwargs):
        title = r'$\phi(\zeta,\psi)$, %s, %s' % (self.theta, self.timestr)
        Z = self.pckloader.get(self.srckeys[0])
        y, x = Z.shape
        return dict(X=np.arange(0, x), Y=np.arange(0, y) / y * 2 * np.pi,
                    Z=Z, title=title), {}

    def _post_dig(self, results):
        results.update(xlabel=r'$\psi$(mpsi)', ylabel=r'$\zeta$')
        return results


class SnapPhiCorrLenDigger(SnapPhiZetaPsiDigger):
    '''phi(zeta,psi) correlation (d_zeta, d_psi) at at theta=j/mtdiag*2pi'''
    __slots__ = []
    post_template = 'tmpl_z111p'

    def _set_fignum(self, numseed=None):
        super(SnapPhiCorrLenDigger, self)._set_fignum(numseed=numseed)
        self._fignum = 'phi_correlation_%03d' % round(self._part*360)
        self.kwoptions = None

    def _dig(self, **kwargs):
        '''
        kwargs
        ------
        *mdpsi*, *mdzeta*: int
            set dpsi dzeta range, max mpsi//2, mzeta//2
        '''
        acckwargs = {}
        title = r'Correlation $\phi(d\zeta,d\psi)$, %s, %s' % (
                self.theta, self.timestr)
        Z = self.pckloader.get(self.srckeys[0])
        y, x = Z.shape
        # if Z size is too large, cal corr will be very slow
        max_x, max_y = 400, 1536
        step_x = round(x/max_x) if x > max_x else 1
        step_y = round(y/max_y) if y > max_y else 1
        if step_x != 1 or step_y != 1:
            Z = Z[::step_y, ::step_x]
            dlog.parm('Too large data of phi(zeta,psi), slice it: %s -> %s'
                      % ((y, x), Z.shape))
            y, x = Z.shape
        else:
            dlog.parm('Data shape of phi(zeta,psi) is %s.' % ((y, x),))
        maxmdpsi, maxmdzeta = int(x/2+1), int(y/2+1)
        mdpsi, mdzeta = kwargs.get('mdpsi', None), kwargs.get('mdzeta', None)
        if isinstance(mdpsi, int) and mdpsi <= maxmdpsi:
            acckwargs['mdpsi'] = mdpsi
        else:
            mdpsi = x // 2
        if isinstance(mdzeta, int) and mdzeta <= maxmdzeta:
            acckwargs['mdzeta'] = mdzeta
        else:
            mdzeta = y // 24
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
                    description='mdzeta:'))
        tau = tools.correlation(Z, 0, y, 0, x, mdzeta, mdpsi)
        X = np.arange(0, mdpsi) * step_x
        Y = np.arange(0, mdzeta) * step_y / y * 2 * np.pi
        mtau = tau.max(axis=0)
        index = np.where(mtau <= 1/np.e)[0]
        if index.size > 0:
            Lpsi = X[index[0]]
        else:
            Lpsi = X[-1]  # over mdpsi
            dlog.parm("Increase mdpsi to find correlation length!")
        dlog.parm("Find correlation length: Lpsi=%s" % Lpsi)
        return dict(X=X, Y=Y, tau=tau, mtau=mtau, Lpsi=Lpsi,
                    title=title), acckwargs

    def _post_dig(self, results):
        r = results
        ax1_calc = dict(X=r['X'], Y=r['Y'], Z=r['tau'], title=r['title'],
                        xlabel=r'$d\psi$(mpsi)', ylabel=r'$d\zeta$',
                        plot_method='contourf')
        ax2_calc = dict(
            LINE=[
                (r['X'], r['mtau'], r'$C_r(\Delta \psi)$'),
                ([r['X'][0], r['X'][-1]], [1/np.e, 1/np.e], '1/e'),
            ],
            title=r'$\phi$ Correlation$(d\psi)$, C(%s)=1/e' % r['Lpsi'],
            xlim=[r['X'][0], r['X'][-1]],
            ylim=[0 if r['mtau'].min() > 0 else r['mtau'].min(), 1],
        )
        return dict(zip_results=[
            ('tmpl_contourf', 211, ax1_calc),
            ('tmpl_line', 212, ax2_calc),
        ])
