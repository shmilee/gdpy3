# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
Source fortran code:

skip
'''

import numpy
from ..GTCv3 import gtc as gtcv3

_all_Converters = gtcv3._all_Converters
_all_Diggers = gtcv3._all_Diggers
__all__ = _all_Converters + _all_Diggers


class GtcConverter(gtcv3.GtcConverter):
    __slots__ = []

    @property
    def twoDarraypats(self):
        # search two dimensional array parameters
        # parent_pats = super(GtcConverter, self).twoDarraypats
        return [
            r'meshte\s+?meshti\s+?meshne\s+?meshni\s*?$'
            + r'(?P<arr1>.*)$'
            + r'\s*?eq_flux at i=\s*?' + self.numpat + r'$',
            r'rg_sp/rg - 1,\s+?dtorpsi/q\s*?$'
            + r'(?P<arr2>.*)?$'
            + r'\s*?\*+?$'
            + r'\s*?=+?$'
            + r'\s*?No Radial Boundary Decay',
            (r'poisson solver=(\s*?' + self.numpat + r'){4}\s*$'
             + r'(?P<arr3>.*)$'
             + r'\s+routine\s+count\s+rank0.*$', 'float_2d_arr3'),
        ]

    def _convert(self):
        '''Read 'gtc.out' parameters.'''
        sd = super(GtcConverter, self)._convert()
        # arr2: rg/a -> rg, GTCv3 compatibility
        if 'arr2' in sd and 'a_minor' in sd:
            val = sd['arr2']
            val = numpy.insert(val, 1, values=val[:, 1]*sd['a_minor'], axis=1)
            sd['arr2'] = val
        return sd
