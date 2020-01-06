# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
GTC Processor Version 4 and its cores.

Notes
-----
GTC .out files should be named as:
gtc.out, data1d.out, equilibrium.out, history.out, meshgrid.out,
snap("%07d" % istep).out, trackp_dir/TRACKP.("%05d" % pe), etc.
so they can be auto-detected.
'''

from . import gtc, snapshot
from ..GTCv3 import (
    data1d,
    equilibrium,
    history,
    meshgrid,
    simugrid,
    # snapphi,
    trackparticle,
)
from ..processors.processor import Processor, plog

__all__ = ['GTCv4']


class GTCv4(Processor):
    __slots__ = []
    ConverterCores = [
        getattr(m, c)
        for m in [
            gtc,
            data1d,
            equilibrium,
            history,
            meshgrid,
            simugrid,
            # snapphi,
            snapshot,
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
            simugrid,
            # snapphi,
            snapshot,
            trackparticle,
        ] for d in m._all_Diggers]
    saltname = 'gtc.out'
    dig_acceptable_time = 10

    @property
    def _rawsummary(self):
        return "GTC '.out' files in %s '%s'" % (
            self.rawloader.loader_type, self.rawloader.path)
