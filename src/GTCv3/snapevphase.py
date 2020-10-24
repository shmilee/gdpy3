# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
Source fortran code:

snapshot.F90::
    ! parameters: # of species and grids
    write(iophase,101)nspecies,nhybrid,negrid,nvgrid
    write(iophase,102)ainside,aoutside,emax,plstart,plstop
    ! data
    write(iophase,102)evphase
  ! evphase(negrid,nvgrid,10,nspecies)
  ! negrid: energy grid,
  ! nvgrid: pitch angle or lambda grid,
  ! 10: fullf, delf, delf^2, weight^2, particle number in pitch(1-5) and lambda(6-10)
  ! nspecies: 1=ion, 2=electron, 2or3=EP

'''

import numpy as np
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog

_all_Converters = ['SnapEVphaseConverter']
_all_Diggers = ['SnapEVphaseDigger']
__all__ = _all_Converters + _all_Diggers


class SnapEVphaseConverter(Converter):
    '''
    Snapshot evphase Data

    1) ion, electron, EP profiles in (E,pitch) or (E,lambda) phase space.
       Profile 3d array is evphase[E, pitch or lambda, 10].
       10 profiles order:
       fullf, delf, delf^2, weight^2, particle number in [E,pitch] (1-5)
       and [E,lambda] (6-10)
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = ['^snap(?P<section>evphase\d{5,7})\.out$',
                    '.*/snap(?P<section>evphase\d{5,7})\.out$']
    _datakeys = (
        # 1. parameters
        'nspecies', 'nhybrid', 'negrid', 'nvgrid',
        'ainside', 'aoutside', 'emax', 'plstart', 'plstop',
        # 2. evphase(negrid,nvgrid,10,nspecies)
        'ion-evphase', 'electron-evphase', 'fastion-evphase'
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
        shape = (sd['negrid'], sd['nvgrid'], 10, sd['nspecies'])
        outdata = np.array([float(n.strip()) for n in outdata[9:]])
        outdata = outdata.reshape(shape, order='F')
        clog.debug("Filling datakey: %s ..." % 'ion-evphase')
        sd['ion-evphase'] = outdata[:, :, :, 0]
        if sd['nhybrid'] > 0:
            clog.debug("Filling datakey: %s ..." % 'electron-evphase')
            sd['electron-evphase'] = outdata[:, :, :, 1]
        if sd['nspecies'] == 2 and sd['nhybrid'] == 0:
            clog.debug("Filling datakey: %s ..." % 'fastion-evphase')
            sd['fastion-evphase'] = outdata[:, :, :, 1]
        if sd['nspecies'] == 3:
            clog.debug("Filling datakey: %s ..." % 'fastion-evphase')
            sd['fastion-evphase'] = outdata[:, :, :, 2]

        return sd


def _snap_get_timestr(snapgroup, pckloader):
    istep = int(snapgroup.replace('evphase', ''))
    tstep = pckloader.get('gtc/tstep')
    return r'istep=%d, time=%s$R_0/c_s$' % (istep, istep * tstep)


class SnapEVphaseDigger(Digger):
    '''ion, electron, fastion profiles in (E, pitch angle or lambda) space.'''
    __slots__ = ['_numseed']
    nitems = '+'
    itemspattern = [r'^(?P<section>evphase\d{5,7})'
                    + '/(?P<particle>(?:ion|electron|fastion))-evphase$',
                    r'^(?P<s>evphase\d{5,7})/negrid$',
                    r'^(?P<s>evphase\d{5,7})/nvgrid$',
                    r'^(?P<s>evphase\d{5,7})/emax$',
                    r'^(?P<s>evphase\d{5,7})/plstart$',
                    r'^(?P<s>evphase\d{5,7})/plstop$']
    _misc = {
        'fullf': dict(index=0, tex='full f'),
        'delf': dict(index=1, tex=r'$\delta f$'),
        'delf2': dict(index=2, tex=r'$\delta f^2$'),
        'weight2': dict(index=3, tex=r'$weight^2$'),
        'number': dict(index=4, tex='particle number N'),
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
        '''
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
                    description='mean delf^2 w^2:'))
        useX = kwargs.get('useX', 'pitch')
        mean = kwargs.get('mean', 'on')
        acckwargs = {'useX': useX, 'mean': mean}
        timestr = _snap_get_timestr(self.group, self.pckloader)
        data, negrid, nvgrid, emax, plstart, plstop = \
            self.pckloader.get_many(*self.srckeys)
        assert data.shape == (negrid, nvgrid, 10)
        Y = np.linspace(0.0, emax, negrid, endpoint=False) + emax/negrid/2.0
        if useX == 'lambda':
            X = np.linspace(plstart, plstop, nvgrid, endpoint=False) \
                + (plstop-plstart)/nvgrid/2.0
            Z = data[:, :, 5+self._misc[self._numseed]['index']]
            if mean == 'off':
                Z = Z * data[:, :, 5+self._misc['number']['index']]
            xlabel = r'$\lambda=\mu B_0/E$'
            xlim = [plstart, plstop]
        else:
            X = np.linspace(-1.0, 1.0, nvgrid, endpoint=False) + 1.0/nvgrid
            Z = data[:, :, self._misc[self._numseed]['index']]
            if mean == 'off':
                Z = Z * data[:, :, self._misc['number']['index']]
            xlabel = r'$\zeta=v_{\parallel}/v$'
            xlim = [-1.0, 1.0]
        title = r'%s %s, %s' % (
            self.section[1], self._misc[self._numseed]['tex'], timestr)
        return dict(X=X, Y=Y, Z=Z, title=title, xlabel=xlabel,
                    xlim=xlim, ylim=[0.0, emax]), acckwargs

    def _post_dig(self, results):
        r = results
        return dict(X=r['X'], Y=r['Y'], Z=r['Z'], title=r['title'],
                    ylabel=r'$E/T_{e0}$', xlabel=r['xlabel'],
                    xlim=r['xlim'], ylim=r['ylim'])
