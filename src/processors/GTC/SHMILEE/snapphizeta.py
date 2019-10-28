#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

'''
Source fortran code:

v3.14-22-g5a68f08d
------------------

snapshot.F90, subroutine snapshot
    ! nj=4
    do j=1,4
        snap_j_list(j)=j*mtdiag/4
    enddo

snapshot.F90, subroutine snap_phi_zeta_psi(j_list)
  write(fdum,'("phi_dir/phi_zeta_psi_snap",i5.5,"_tor",i4.4,".out")')nsnap,myrank_toroidal
  open(iopotential,file=trim(fdum),status='replace')
  if(myrank_toroidal==0)then
    ! parameters: shape of data, all selected j
    write(iopotential,101)mzeach,mpsi+1, nj, j_list(:nj)
  endif
  write(iopotential,102)phiflux
'''

import numpy as np
from ...core import DigCore, LayCore, FigInfo, PcolorFigInfo, log

__all__ = ['SnapPhiZetaPsiDigCoreV3', 'SnapPhiZetaPsiLayCoreV3']


class SnapPhiZetaPsiDigCoreV3(DigCore):
    '''
    Snapshot phi(zeta,psi) Data

    Shape os array data is (mtdiag,mpsi+1)
    '''
    __slot__ = []
    nitems = '+'
    itemspattern = ['^phi_dir/phi_zeta_psi_(?P<section>snap\d{5})_tor\d{4}\.out$',
                    '.*/phi_dir/phi_zeta_psi_(?P<section>snap\d{5})_tor\d{4}\.out$']
    default_section = 'snap99999'
    _datakeys = (
        # 1. parameters
        'mzeach', 'nj', 'j_list',
        'mpsi+1', 'mtgrid+1', 'mtoroidal',  # by SnapshotDigCore
        # 2. phi(zeta,psi,nj), # theta; j
        'phi_zeta_psi_090',  # pi/2;  mtgrid/4
        'phi_zeta_psi_180',  # pi  ;  2mtgrid/4
        'phi_zeta_psi_270',  # 3pi/2; 3mtgrid/4
        'phi_zeta_psi_360',  # 0,2pi; mtgrid
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
        mtdiag = mzeach*mtoroidal
        assert phi.shape == (mtdiag, mpsi1, nj)
        # 1. parameters
        log.debug("Filling datakeys: %s ..." % str(self._datakeys[:3]))
        sd = dict(mzeach=mzeach, nj=nj, j_list=j_list)
        # 2. data
        log.debug("Filling datakeys: %s ..." % str(self._datakeys[-4:]))
        for j in range(nj):
            sd['phi_zeta_psi_%03d' % (90*j+90)] = phi[:, :, j]
        return sd


class PhiZetaPsiFigInfo(PcolorFigInfo):
    '''Figures of phi(zeta,psi). nj=4'''
    __slots__ = ['theta']
    figurenums = ['phi-zeta_psi_%03d' % (90*j+90) for j in range(4)]
    numpattern = '^phi-zeta_psi_(?P<theta>\d{3})$'
    default_plot_method = 'contourf'

    def _get_srckey_extrakey(self, fignum):
        groupdict = self._pre_check_get(fignum, 'theta')
        self.theta = int(groupdict['theta'])
        return ['nj', 'j_list', 'phi_zeta_psi_%03d' % self.theta], ['gtc/tstep']

    def _get_data_X_Y_Z_title_etc(self, data):
        Z = data['phi_zeta_psi_%03d' % self.theta]
        y, x = Z.shape if Z.size > 0 else (0, 0)
        X = np.arange(0, x)
        Y = np.arange(0, y) / y * 2 * np.pi
        xlabel, ylabel = r'$\psi$(mpsi)', r'$\zeta$'
        istep = int(self.groups.replace('snap', ''))
        title = (r'$\phi(\zeta,\psi), \theta=%d^\circ$, istep=%d, time=%s$R_0/c_s$'
                 % (self.theta, istep, istep * data['gtc/tstep']))
        return dict(X=X, Y=Y, Z=Z, title=title, xlabel=xlabel, ylabel=ylabel)


class SnapPhiZetaPsiLayCoreV3(LayCore):
    '''
    Snapshot phi(zeta,psi) Figures
    '''
    __slot__ = []
    itemspattern = ['^(?P<section>snap\d{5})$']
    default_section = 'snap99999'
    figinfoclasses = [PhiZetaPsiFigInfo]
