# -*- coding: utf-8 -*-

# Copyright (c) 2020-2021 shmilee

'''
GTC Processor Version 4 and its cores.

Notes
-----
GTC .out files should be named as:
gtc.out, data1d.out, equilibrium.out, history.out, meshgrid.out,
snap("%07d" % istep).out, trackp_dir/TRACKP.("%05d" % pe), etc.
so they can be auto-detected.
'''

from . import gtc
from ..GTCv3 import (
    data1d,
    equilibrium,
    history,
    meshgrid,
    simugrid,
    snapshot,
    trackparticle,
)
from ..processors.processor import plog

__all__ = ['Base_GTCv4']
_load_modules = (
    gtc,
    data1d,
    equilibrium,
    history,
    meshgrid,
    simugrid,
    snapshot,
    trackparticle,
)


class Base_GTCv4(object):
    __slots__ = []
    ConverterCores = [getattr(m, c)
                      for m in _load_modules for c in m._all_Converters]
    DiggerCores = [getattr(m, d)
                   for m in _load_modules for d in m._all_Diggers]
    saltname = 'gtc.out'
    convert_array_bitsize = 32
    dig_acceptable_time = 10

    @property
    def _rawsummary(self):
        return "GTC '.out' files in %s '%s'" % (
            self.rawloader.loader_type, self.rawloader.path)

    def _check_pckloader_backward_version(self, pckloader):
        if 'version' in pckloader:
            if pckloader.get('version') in [
                    '110922', 'GTCV110922',
                    'GTCV3.14-22']:
                plog.info("Use an old version '%s' pckloader %s."
                          % (pckloader.get('version'), pckloader.path))
                return True
        if 'processor' in pckloader:
            if pckloader.get('processor') in ['GTCv3']:
                plog.info("Use backward version '%s' pckloader %s."
                          % (pckloader.get('processor'), pckloader.path))
                return True
        return False
