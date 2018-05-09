# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
GTC Processor V110922 and its cores.
'''

from . import (
    gtc,
    data1d,
    equilibrium,
    history,
    meshgrid,
    snapshot,
    trackparticle,
    contrib_data1drzf,
)
from ..processor import Processor


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
        contrib_data1drzf.Data1dRZFDigCoreV110922,
    ]
    LayCores = [
        data1d.Data1dLayCoreV110922,
        equilibrium.EquilibriumLayCoreV110922,
        history.HistoryLayCoreV110922,
        snapshot.SnapshotLayCoreV110922,
        trackparticle.TrackParticleLayCoreV110922,
        contrib_data1drzf.Data1dRZFLayCoreV110922,
    ]
