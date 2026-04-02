# -*- coding: utf-8 -*-

# Copyright (c) 2026 shmilee

'''
Source fortran code:

* magn_mpi.F90, subroutine fieldtrace_RKG_MS
```
  write(traceunit, '(2I7, 1p,6G17.5)') ik, j, xp, yp, zp, rp, bval, cci
```
'''

import numpy as np
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog

_all_Converters = ['TraceConverter']
_all_Diggers = ['TraceDigger']
__all__ = _all_Converters + _all_Diggers


class TraceConverter(Converter):
    '''
    Trace points
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = [r'^(?P<section>trace)_surf(?P<surf>\d+)\.out$',
                    r'.*/(?P<section>trace)_surf(?P<surf>\d+)\.out$']
    _datakeys = (r'surf-%d', )

    @property
    def group(self):
        return self.section[0]

    def _convert(self):
        '''Read 'trace_surf%d.out'.'''
        surf = self.section[1]
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()
        outdata = np.array([[float(n) for n in l.split()] for l in outdata])
        phirz_etc = outdata[:, 1:]  # phip, rp, zp, bval, cci
        sd = {f'surf-{surf}': phirz_etc.T}
        clog.debug("Filling datakey: %s ..." % sd.keys())
        return sd


class TraceDigger(Digger):
    '''plot trace points'''
    __slots__ = []
    nitems = '+'
    itemspattern = [r'^(?P<section>trace)/surf-(?P<idx>\d+)$']
    commonpattern = []
    post_template = 'tmpl_line' # scatter

    def _set_fignum(self, numseed=None):
        self._fignum = 'surf-%s' % self.section[1]
        self.kwoptions = None

    def _dig(self, kwargs):
        acckwargs = {}
        self.kwoptions = {}
        rpzp, = self.pckloader.get_many(*self.srckeys, *self.extrakeys)
        return dict(rp=rpzp[1], zp=rpzp[2]), acckwargs

    def _post_dig(self, results):
        r = results
        return dict(LINE=[(r['rp'], r['zp'])], title=self.fignum,
                    xlabel=r'$R(m)$', ylabel=r'$Z(m)$', aspect=0.7)
