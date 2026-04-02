# -*- coding: utf-8 -*-

# Copyright (c) 2026 shmilee

'''
Source fortran code:

* axis.F90, subroutine axisshoot
```
  do i=1, axis_ntotalt
      write(axisunit, '(I4,1p,3G18.8)') i, phi0(i), rax0(i), zax0(i)
  enddo
```
'''

import numpy as np
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog

_all_Converters = ['AxisConverter']
_all_Diggers = ['AxisDigger']
__all__ = _all_Converters + _all_Diggers


class AxisConverter(Converter):
    '''
    Axis Data
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = [r'^(?P<section>axis)\.out$', r'.*/(?P<section>axis)\.out$']
    _datakeys = ('axis', 'axis_ntotalt')

    def _convert(self):
        '''Read 'axis.out'.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()
        outdata = np.array([[float(n) for n in l.split()] for l in outdata])
        phirz = outdata[:, 1:]  # phip, rp, zp
        N = outdata[-1, 0]
        sd = {'axis': phirz.T, 'axis_ntotalt': N}
        clog.debug("Filling datakeys: %s ..." % sd.keys())
        return sd


class AxisDigger(Digger):
    '''plot Axis points'''
    __slots__ = []
    nitems = '+'
    itemspattern = [r'^(?P<section>axis)/axis$']
    commonpattern = []
    post_template = 'tmpl_line' # scatter

    def _set_fignum(self, numseed=None):
        self._fignum = 'axis'
        self.kwoptions = None

    def _dig(self, kwargs):
        acckwargs = {}
        self.kwoptions = {}
        axis, = self.pckloader.get_many(*self.srckeys, *self.extrakeys)
        phip, rp, zp = axis[0], axis[1], axis[2]
        rlim = 1.05 * np.max(rp)
        return dict(xp=rp*np.cos(phip), yp=rp*np.sin(phip), zp=zp,
                    rlim=rlim), acckwargs

    def _post_dig(self, results):
        r = results
        sc = [-r['rlim'], r['rlim']]
        return dict(LINE=[(r['xp'], r['yp'], r['zp'])], title=self.fignum,
                    xlabel=r'X(m)', ylabel=r'Y(m)', aspect='equal',
                    lin3d=True, zlabel='Z(m)', scale_xyz=(sc, sc, sc))
