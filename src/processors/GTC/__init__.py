# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
GTC Processor V110922 and its cores.

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
    trackparticle,
)
from ..processor import Processor

__all__ = ['GTCProcessorV110922']


class GTCProcessorV110922(Processor):
    __slots__ = []
    DigCores = [
        gtc.GtcDigCoreV110922,
        data1d.Data1dDigCoreV110922,
        equilibrium.EquilibriumDigCoreV110922,
        history.HistoryDigCoreV110922,
        meshgrid.MeshgridDigCoreV110922,
        snapshot.SnapshotDigCoreV110922,
        trackparticle.TrackParticleDigCoreV110922,
    ]
    LayCores = [
        data1d.Data1dLayCoreV110922,
        equilibrium.EquilibriumLayCoreV110922,
        history.HistoryLayCoreV110922,
        snapshot.SnapshotLayCoreV110922,
        trackparticle.TrackParticleLayCoreV110922,
    ]
    pckversion = 'GTCV110922'
    pcksaltname = 'gtc.out'

    @property
    def _rawdata_summary(self):
        return "GTC '.out' files in %s '%s'" % (
            self.rawloader.loader_type, self.rawloader.path)
