# -*- coding: utf-8 -*-

# Copyright (c) 2026 shmilee

'''
MAGN Processor Version 1 and its cores for my MAGN.

Notes
-----
MAGN .out files should be named as:
magn.out, axis.out, surf_profile.out,
trace_surf("%d" % index).out, poincare_rnk("%d" % myrank).out, etc.
so they can be auto-detected.
'''

import numpy as np
from . import (
    magn,
    axis,
    poincare,
#    profile,
    trace,
)
from ..processors.processor import plog
from ..loaders.base import log as llog

__all__ = ['Base_MAGNv1']
_load_modules = (
    magn,
    axis,
    poincare,
#    profile,
    trace,
)


class Base_MAGNv1(object):
    __slots__ = []
    ConverterCores = [getattr(m, c)
                      for m in _load_modules for c in m._all_Converters]
    DiggerCores = [getattr(m, d)
                   for m in _load_modules for d in m._all_Diggers]
    saltname = 'magn.out'
    convert_array_bitsize = 32
    dig_acceptable_time = 10

    @property
    def _rawsummary(self):
        return "MAGN '.out' files in %s '%s'" % (
            self.rawloader.loader_type, self.rawloader.path)
