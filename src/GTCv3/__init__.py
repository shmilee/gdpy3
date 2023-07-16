# -*- coding: utf-8 -*-

# Copyright (c) 2019-2021 shmilee

'''
GTC Processor Version 3 and its cores for GTC v3.x and v4.x.

Notes
-----
GTC .out files should be named as:
gtc.out, data1d.out, equilibrium.out, history.out, meshgrid.out,
snap("%05d" % istep).out or snap("%07d" % istep).out,
trackp_dir/TRACKP.("%05d" % pe), etc.
so they can be auto-detected.
'''

from . import (
    gtc,
    data1d,
    equilibrium,
    history,
    meshgrid,
    simugrid,
    snapshot,
    trackparticle,
    rzf,
    zetapsi3d,
    flux3d,
    snapevphase,
    snapphi,
)
from ..processors.processor import plog

__all__ = ['Base_GTCv3']
_load_modules = (
    gtc,
    data1d,
    equilibrium,
    history,
    meshgrid,
    simugrid,
    snapshot,
    trackparticle,
    rzf,
    zetapsi3d,
    flux3d,
    snapevphase,
    snapphi,
)


class Base_GTCv3(object):
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
        return False

    def _check_pckloader_forward_version(self, pckloader):
        if 'processor' in pckloader:
            if pckloader.get('processor') in ['GTCv4']:
                plog.info("Use a new version '%s' pckloader %s."
                          % (pckloader.get('processor'), pckloader.path))
                return True
        return False
