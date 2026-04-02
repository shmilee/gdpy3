# -*- coding: utf-8 -*-

# Copyright (c) 2026 shmilee

'''
Source fortran code:

* magn_mpi.F90, subroutine fieldtrace_RKG_MS
```
  write(poincareunit, '(2I7, 1p,2G17.8, G15.6)') ik, j, &
    & rp, zp, phi / (2.0 * 3.14159265358979d0 / real(nfp))
```
'''

import numpy as np
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog

_all_Converters = ['PoincareConverter']
_all_Diggers = ['PoincareDigger']
__all__ = _all_Converters + _all_Diggers


class PoincareConverter(Converter):
    '''
    Poincare points
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = [r'^(?P<section>poincare)_rnk(?P<rank>\d+)\.out$',
                    r'.*/(?P<section>poincare)_rnk(?P<rank>\d+)\.out$']
    _datakeys = (r'surf-%d', )

    @property
    def group(self):
        return self.section[0]

    def _convert(self):
        '''Read 'poincare_rnk%d.out'.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()
        outdata = np.array([[float(n) for n in l.split()] for l in outdata])
        col1 = outdata[:, 0]
        unique_idxs = np.unique(col1)
        pp = {}
        for idx in unique_idxs:
            mask = col1 == idx  # select rows
            rp_zp = outdata[mask, 2:4]  # rp,zp
            pp[f'surf-{int(idx)}'] = rp_zp.T
        clog.debug("Filling datakeys: %s ..." % pp.keys())
        return pp


class PoincareDigger(Digger):
    '''scatter Poincare points'''
    __slots__ = []
    nitems = '+'
    itemspattern = [r'^(?P<section>poincare)/surf-(?P<idx>\d+)$']
    commonpattern = []
    post_template = 'tmpl_line' # scatter

    def _set_fignum(self, numseed=None):
        self._fignum = 'surf-%s' % self.section[1]
        self.kwoptions = None

    def _dig(self, kwargs):
        acckwargs = {}
        self.kwoptions = {}
        rpzp, = self.pckloader.get_many(*self.srckeys, *self.extrakeys)
        return dict(rp=rpzp[0], zp=rpzp[1]), acckwargs

    def _post_dig(self, results):
        r = results
        return dict(LINE=[(r['rp'], r['zp'])], title=self.fignum,
                    xlabel=r'$R(m)$', ylabel=r'$Z(m)$', aspect=0.7)
