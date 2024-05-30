# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
Source fortran code:

shmilee.F90, subroutine snap_loop_evphase_space
    ! parameters: # of species and grids
    write(iophase,101)nspecies,nhybrid,negrid,nvgrid
    write(iophase,102)ainside,aoutside,emax,plstart,plstop
    ! data
    write(iophase,102)evphase
  ! evphase(negrid,nvgrid,6,nspecies)
  ! negrid: energy grid,
  ! nvgrid: pitch angle or lambda grid,
  ! 6: fullf, delf, weight^2 in pitch(1-3) and lambda(4-6)
  ! nspecies: 1=ion, 2=electron, 2or3=EP

'''

import numpy as np
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog
from .snapshot import _snap_get_timestr

_all_Converters = ['SnapEVphaseConverter']
_all_Diggers = ['SnapEVphaseDigger']
__all__ = _all_Converters + _all_Diggers


class SnapEVphaseConverter(Converter):
    '''
    Snapshot evphase Data

    1) ion, electron, EP profiles in (E,pitch) or (E,lambda) phase space.
       Profile 3d array is evphase[E, pitch or lambda, 6].
       6 profiles order:
       fullf, delf, weight^2 in [E,pitch] (1-3)
       and [E,lambda] (4-6)
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = [r'^(?P<section>snap\d{5,7})_evphase\.out$',
                    r'.*/(?P<section>snap\d{5,7})_evphase\.out$']
    _datakeys = (
        # 1. parameters
        'nspecies', 'nhybrid', 'ev-negrid', 'nvgrid',
        'ev-ainside', 'ev-aoutside', 'ev-emax', 'ev-plstart', 'ev-plstop',
        # 2. evphase(negrid,nvgrid,6,nspecies)
        'evphase-ion', 'evphase-electron', 'evphase-fastion'
    )

    def _convert(self):
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        # 1. parameters
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:4]))
        for i, key in enumerate(self._datakeys[:4]):
            sd.update({key: int(outdata[i].strip())})
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[4:9]))
        for i, key in enumerate(self._datakeys[4:9]):
            sd.update({key: float(outdata[i+4].strip())})
        # 2. data
        shape = (sd['ev-negrid'], sd['nvgrid'], 6, sd['nspecies'])
        outdata = np.array([float(n.strip()) for n in outdata[9:]])
        outdata = outdata.reshape(shape, order='F')
        clog.debug("Filling datakey: %s ..." % 'ion-evphase')
        sd['evphase-ion'] = outdata[:, :, :, 0]
        if sd['nhybrid'] > 0:
            clog.debug("Filling datakey: %s ..." % 'electron-evphase')
            sd['evphase-electron'] = outdata[:, :, :, 1]
        if sd['nspecies'] == 2 and sd['nhybrid'] == 0:
            clog.debug("Filling datakey: %s ..." % 'fastion-evphase')
            sd['evphase-fastion'] = outdata[:, :, :, 1]
        if sd['nspecies'] == 3:
            clog.debug("Filling datakey: %s ..." % 'fastion-evphase')
            sd['evphase-fastion'] = outdata[:, :, :, 2]
        for k in ['nspecies', 'nhybrid', 'nvgrid']:
            _ = sd.pop(k)
        return sd


class SnapEVphaseDigger(Digger):
    '''ion, electron, fastion profiles in (E, pitch angle or lambda) space.'''
    __slots__ = ['_numseed']
    nitems = '+'
    itemspattern = [r'^(?P<section>snap\d{5,7})'
                    + '/evphase-(?P<particle>(?:ion|electron|fastion))$',
                    r'^(?P<s>snap\d{5,7})/ev-negrid$',
                    r'^(?P<s>snap\d{5,7})/nvgrid$',
                    r'^(?P<s>snap\d{5,7})/ev-emax$',
                    r'^(?P<s>snap\d{5,7})/ev-plstart$',
                    r'^(?P<s>snap\d{5,7})/ev-plstop$']
    _misc = {
        'fullf': dict(index=0, tex='full f'),
        'delf': dict(index=1, tex=r'$\delta f$'),
        'weight2': dict(index=2, tex=r'$weight^2$'),
    }
    numseeds = list(_misc.keys())
    post_template = 'tmpl_contourf'

    def _set_fignum(self, numseed=None):
        self._fignum = '%s_%s' % (self.section[1], numseed)
        self._numseed = numseed
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *useX*: str 'pitch' or 'lambda', default 'pitch'
        *mean*: str 'on'/'off', default 'on'
            mean delf^2 weight^2 by particle number
        *merge_xgrid*: int, default 1
        *merge_ygrid*: int, default 1
        *least_N*: int, default 0
            at least N particles in one merged cell
        '''
        timestr = _snap_get_timestr(self.group, self.pckloader)
        data, negrid, nvgrid, emax, plstart, plstop = \
            self.pckloader.get_many(*self.srckeys)
        try:
            assert data.shape == (negrid, nvgrid, 6)
        except Exception:
            nvgrid = data.shape[1]
        Y = np.linspace(0.0, emax, negrid, endpoint=False) + emax/negrid/2.0
        if self.kwoptions is None:
            self.kwoptions = dict(
                useX=dict(
                    widget='Dropdown',
                    options=['pitch', 'lambda'],
                    value='pitch',
                    description='X in:'),
                mean=dict(
                    widget='Dropdown',
                    options=['on', 'off'],
                    value='on',
                    description='mean delf^2 w^2:'),
                merge_xgrid=dict(widget='IntSlider',
                                 rangee=(1, nvgrid//2, 1),
                                 value=1,
                                 description='merge xgrid:'),
                merge_ygrid=dict(widget='IntSlider',
                                 rangee=(1, negrid//2, 1),
                                 value=1,
                                 description='merge ygrid:'),
                least_N=dict(
                    widget='IntSlider',
                    rangee=(0, 1000, 100),
                    value=0,
                    description='least N:'))
        useX = kwargs.get('useX', 'pitch')
        mean = kwargs.get('mean', 'on')
        merge_xgrid = kwargs.get('merge_xgrid', 1)
        merge_ygrid = kwargs.get('merge_ygrid', 1)
        least_N = kwargs.get('least_N', 0)
        acckwargs = {'useX': useX, 'mean': mean, 'least_N': least_N,
                     'merge_xgrid': merge_xgrid, 'merge_ygrid': merge_ygrid}
        if useX == 'lambda':
            X = np.linspace(plstart, plstop, nvgrid, endpoint=False) \
                + (plstop-plstart)/nvgrid/2.0
            Z = data[:, :, 3+self._misc[self._numseed]['index']]
            N = data[:, :, 3+self._misc['fullf']['index']]
            if mean == 'off':
                Z = Z * N
            xlabel = r'$\lambda=\mu B_0/E$'
            xlim = [plstart, plstop]
        else:
            X = np.linspace(-1.0, 1.0, nvgrid, endpoint=False) + 1.0/nvgrid
            Z = data[:, :, self._misc[self._numseed]['index']]
            N = data[:, :, self._misc['fullf']['index']]
            if mean == 'off':
                Z = Z * N
            xlabel = r'$\zeta=v_{\parallel}/v$'
            xlim = [-1.0, 1.0]
        title = r'%s %s, %s' % (
            self.section[1], self._misc[self._numseed]['tex'], timestr)
        ylim = [0.0, emax]
        if merge_xgrid > 1 or merge_ygrid > 1:
            if mean == 'on':
                iZ = Z*N
            else:
                iZ = Z
            X, Y, Z = self.__merge_grids(
                X, Y, iZ, N, least_N, merge_xgrid, merge_ygrid)
            xlim = [X[0], X[-1]]
            ylim = [Y[0], Y[-1]]
        else:
            if least_N > 0:
                for i in range(Y.size):
                    for j in range(X.size):
                        if N[i, j] < least_N:
                            dlog.debug("Drop data [%d, %d]" % (i, j))
                            Z[i, j] = 0.0

        return dict(X=X, Y=Y, Z=Z, title=title, xlabel=xlabel,
                    xlim=xlim, ylim=ylim), acckwargs

    @staticmethod
    def _div_avoid_zero(a, b):
        if a == 0 or b == 0:
            return 0
        return a/b

    def __merge_grids(self, X, Y, iZ, N, least_N, dx, dy):
        newX = np.array(
            [np.sum(X[i:i+dx])/X[i:i+dx].size for i in range(0, X.size, dx)])
        newY = np.array(
            [np.sum(Y[i:i+dy])/Y[i:i+dy].size for i in range(0, Y.size, dy)])
        newZ = np.zeros((newY.size, newX.size))
        dlog.parm('Data shape is %s -> %s' % (iZ.shape, newZ.shape))
        print(newX, newY, newX.size, newY.size)
        for jj, j in enumerate(range(0, N.shape[1], dx)):
            for ii, i in enumerate(range(0, N.shape[0], dy)):
                a, b = np.sum(iZ[i:i+dy, j:j+dx]), np.sum(N[i:i+dy, j:j+dx])
                print(jj, j, ii, i, a, b, least_N)
                if least_N > 0 and b < least_N:
                    dlog.parm("Drop data [%d, %d]" % (ii, jj))
                    newZ[ii, jj] = 0.0
                else:
                    if a == 0 or b == 0:
                        newZ[ii, jj] = 0.0
                    else:
                        newZ[ii, jj] = a / b
        return newX, newY, newZ

    def _post_dig(self, results):
        r = results
        return dict(X=r['X'], Y=r['Y'], Z=r['Z'], title=r['title'],
                    ylabel=r'$E/T_{e0}$', xlabel=r['xlabel'],
                    xlim=r['xlim'], ylim=r['ylim'])
