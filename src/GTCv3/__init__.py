# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

'''
GTC Processor Version 3 (V110922) and its cores.

Notes
-----
GTC .out files should be named as:
gtc.out, data1d.out, equilibrium.out, history.out, meshgrid.out,
snap("%05d" % istep).out, trackp_dir/TRACKP.("%05d" % pe), etc.
so they can be auto-detected.
'''

from . import (
    gtc,
    data1d,
    equilibrium,
    history,
    meshgrid,
    snapshot,
    snapphi,
    trackparticle,
)
from ..processors.processor import Processor, plog

__all__ = ['GTCv3']


class GTCv3(Processor):
    __slots__ = []
    ConverterCores = [
        getattr(m, c)
        for m in [
            gtc,
            data1d,
            equilibrium,
            history,
            meshgrid,
            snapshot,
            snapphi,
            trackparticle,
        ] for c in m._all_Converters]
    DiggerCores = [
        getattr(m, d)
        for m in [
            gtc,
            data1d,
            equilibrium,
            history,
            meshgrid,
            snapshot,
            snapphi,
            trackparticle,
        ] for d in m._all_Diggers]
    saltname = 'gtc.out'
    dig_acceptable_time = 20

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
