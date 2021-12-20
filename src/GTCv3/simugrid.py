# -*- coding: utf-8 -*-

# Copyright (c) 2019-2021 shmilee

'''
Source fortran code:

setup.F90, subroutine fieldinitial
  i=17
  write(911,*)i
  write(911,*)mpsi+1
  do i=0,mpsi
     write(911,*)psimesh(i)
     write(911,*)qmesh(i)
     write(911,*)tormesh(i)
     write(911,*)sprpsi(psimesh(i))
     write(911,*)sprgpsi(psimesh(i))
     write(911,*)meshti(i)
     write(911,*)kapati(i)
     write(911,*)meshni(i)
     write(911,*)kapani(i)
     write(911,*)meshte(i)
     write(911,*)kapate(i)
     write(911,*)meshne(i)
     write(911,*)kapane(i)
     write(911,*)meshtf(i)
     write(911,*)kapatf(i)
     write(911,*)meshnf(i)
     write(911,*)kapanf(i)
     !!! write(911,*)dtndpsi(i)
  enddo
'''

import numpy as np
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog
from .equilibrium import _1d_data_misc

_all_Converters = ['SimugridConverter']
_all_Diggers = ['SimugridQshearDigger', 'SimugridParticleDigger']
__all__ = _all_Converters + _all_Diggers


class SimugridConverter(Converter):
    '''
    Simulation meshgrid data

    psimesh, qmesh, ......, meshti, ......, meshnf, etc.
    Shape of the array data is (mpsi+1,).
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = ['^(?P<section>simugrid)\.out$',
                    '.*/(?P<section>simugrid)\.out$']
    _datakeys = ('psimesh', 'qmesh', 'tormesh', 'sprpsi', 'sprgpsi',
                 'meshti', 'kapati', 'meshni', 'kapani',
                 'meshte', 'kapate', 'meshne', 'kapane',
                 'meshtf', 'kapatf', 'meshnf', 'kapanf')

    def _convert(self):
        '''Read 'simugrid.out'.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()
        sd = {}
        N, mpsi1 = int(outdata[0]), int(outdata[1])
        assert N == 17
        outdata = outdata[2:]
        shape = (N, len(outdata) // N)
        if len(outdata) % N != 0:
            clog.warning("Missing some raw data in '%s'! Guess the shape '%s'."
                         % (self.files, shape))
            outdata = outdata[:shape[0]*shape[1]]
        else:
            assert shape == (N, mpsi1)
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:]))
        outdata = np.array([float(n.strip()) for n in outdata])
        outdata = outdata.reshape(shape, order='F')
        for i, key in enumerate(self._datakeys):
            sd.update({key: outdata[i]})
        return sd


class SimugridQshearDigger(Digger):
    '''psi(r), rg(r), q(r) and shear(r)'''
    __slots__ = []
    nitems = '+'
    itemspattern = [r'^(?P<section>simugrid)/psimesh',
                    r'^(?P<section>simugrid)/qmesh',
                    r'^(?P<section>simugrid)/sprpsi',
                    r'^(?P<section>simugrid)/sprgpsi']
    commonpattern = ['equilibrium/1d-data']
    post_template = ('tmpl_z111p', 'tmpl_line')

    def _set_fignum(self, numseed=None):
        self._fignum = 'q_shear(r)'
        self.kwoptions = None

    def _check_use_ra(self, kwargs, r, er):
        '''
        kwargs
        ------
        *use_ra*: bool
            use psi or r/a, default False
        '''
        if self.kwoptions is None:
            self.kwoptions = dict(
                use_ra=dict(widget='Checkbox',
                            value=False,
                            description='X: r/a'))
        acckwargs = {'use_ra': False}
        if kwargs.get('use_ra', False):
            r = r / er[-1]
            er = er / er[-1]
            acckwargs['use_ra'] = True
            xlabel = r'$r/a$'
        else:
            xlabel = r'$r/R$'
        return r, er, acckwargs, xlabel

    def _dig(self, kwargs):
        psi, q, r, rg, e1d = self.pckloader.get_many(
            *self.srckeys, *self.extrakeys)
        shear = np.gradient(np.log(q))/np.gradient(np.log(r))
        epsi, eq, er, erg = e1d[0], e1d[19], e1d[23], e1d[25]
        eshear = np.gradient(np.log(eq[1:]))/np.gradient(np.log(er[1:]))
        r, er, acckwargs, xlabel = self._check_use_ra(kwargs, r, er)
        return dict(psi=psi, q=q, r=r, rg=rg, shear=shear,
                    epsi=epsi, eq=eq, er=er, erg=erg, eshear=eshear,
                    xlabel=xlabel), acckwargs

    _dig.__doc__ = _check_use_ra.__doc__

    def _post_dig(self, results):
        r = results
        ax_calc = {}
        for pv in ['psi', 'rg', 'q', 'shear']:
            er = r['er'][1:] if pv == 'shear' else r['er']
            title = r'$\%s(r)$' if pv == 'psi' else r'%s(r)'
            ax_calc[pv] = dict(
                LINE=[(er, r['e%s' % pv], 'equilibrium'),
                      (r['r'], r[pv], 'simulated'), ],
                title=title % pv, xlim=[0, r['er'][-1]],
            )
            if pv in ['q', 'shear']:
                ax_calc[pv]['xlabel'] = r['xlabel']
        return dict(zip_results=[
            ('tmpl_line', 221, ax_calc['psi']),
            ('tmpl_line', 222, ax_calc['rg']),
            ('tmpl_line', 223, ax_calc['q']),
            ('tmpl_line', 224, ax_calc['shear']),
        ])


class SimugridParticleDigger(SimugridQshearDigger):
    '''n, T, L_n, L_T of particle ion, electron, fastion'''
    __slots__ = []
    nitems = '+'
    itemspattern = [r'^(?P<section>simugrid)/mesht(?P<particle>(?:i|e|f))',
                    r'^(?P<section>simugrid)/kapat(?P<particle>(?:i|e|f))',
                    r'^(?P<section>simugrid)/meshn(?P<particle>(?:i|e|f))',
                    r'^(?P<section>simugrid)/kapan(?P<particle>(?:i|e|f))']
    commonpattern = ['simugrid/psimesh', 'simugrid/sprpsi',
                     'equilibrium/1d-data', 'gtc/rho0']
    __particles = dict(i='ion', e='electron', f='fastion')
    post_template = ('tmpl_z111p', 'tmpl_line')

    def _set_fignum(self, numseed=None):
        self._fignum = self.__particles[self.section[1]]
        self.kwoptions = None

    def _dig(self, kwargs):
        p = self.section[1]
        T, kapaT, n, kapan, psi, r, e1d, rho0 = self.pckloader.get_many(
            *self.srckeys, *self.extrakeys)
        drdp = np.gradient(r)/np.gradient(psi)
        LT_1 = kapaT/drdp
        Ln_1 = kapan/drdp
        eT = e1d[_1d_data_misc['T%s' % p]['index']]
        en = e1d[_1d_data_misc['n%s' % p]['index']]
        er = e1d[23]
        eLT_1 = - np.gradient(np.log(eT))/np.gradient(er)
        eLn_1 = - np.gradient(np.log(en))/np.gradient(er)
        r, er, acckwargs, xlabel = self._check_use_ra(kwargs, r, er)
        return dict(T=T/rho0**2, LT_1=LT_1, n=n, Ln_1=Ln_1, r=r,
                    eT=eT, eLT_1=eLT_1, en=en, eLn_1=eLn_1, er=er,
                    xlabel=xlabel), acckwargs

    _dig.__doc__ = SimugridQshearDigger._check_use_ra.__doc__

    def _post_dig(self, results):
        r = results
        p = self.section[1]
        ax_calc = {}
        for pv, tv in [('T', r'T_%s'), ('LT_1', r'R/L_{T%s}'),
                       ('n', 'n_%s'), ('Ln_1', r'R/L_{n%s}')]:
            ax_calc[pv] = dict(
                LINE=[(r['er'], r['e%s' % pv], 'equilibrium'),
                      (r['r'], r[pv], 'simulated'), ],
                title=(r'$%s(r)$' % tv) % p, xlim=[0, r['er'][-1]],
            )
            if pv in ['n', 'Ln_1']:
                ax_calc[pv]['xlabel'] = r['xlabel']
        return dict(zip_results=[
            ('tmpl_line', 221, ax_calc['T']),
            ('tmpl_line', 222, ax_calc['LT_1']),
            ('tmpl_line', 223, ax_calc['n']),
            ('tmpl_line', 224, ax_calc['Ln_1']),
        ])
