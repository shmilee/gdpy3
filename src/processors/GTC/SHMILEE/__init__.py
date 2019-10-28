# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

'''
User SHMILEE's Processors and Cores.

1. GTC Residual Zonal Flow Processor V110922.
   GTC .out files should be named as: gtc.out, data1d.out, history.out,
   so they can be auto-detected.

2. GTC phi(zeta,psi) Processor V3.
   GTC .out files should be named as:
   phi_dir/phi_zeta_psi_snap("%05d" % istep)_tor("%04d" % myrank_toroidal).out,
   others like GTC Processor V110922,
   so they can be auto-detected.
'''

from .. import (
    gtc,
    data1d,
    equilibrium,
    history,
    meshgrid,
    snapshot,
    trackparticle,
    GTCProcessorV110922,
)

from . import rzf, snapphizeta

__all__ = ['GTCSHMILEERZF110922', 'GTCSHMILEEPHIZETAV3']


class GTCSHMILEERZF110922(GTCProcessorV110922):
    __slots__ = []
    DigCores = [
        rzf.RZFGtcDigCoreV110922,
        data1d.Data1dDigCoreV110922,
        history.HistoryDigCoreV110922,
    ]
    LayCores = [
        rzf.RZFData1dLayCoreV110922,
        history.HistoryLayCoreV110922,
    ]
    pckversion = 'GTCSHMILEERZF110922'


class GTCSHMILEEPHIZETAV3(GTCProcessorV110922):
    __slots__ = []
    DigCores = [
        gtc.GtcDigCoreV110922,
        data1d.Data1dDigCoreV110922,
        equilibrium.EquilibriumDigCoreV110922,
        history.HistoryDigCoreV110922,
        meshgrid.MeshgridDigCoreV110922,
        snapshot.SnapshotDigCoreV110922,
        snapphizeta.SnapPhiZetaPsiDigCoreV3,
        trackparticle.TrackParticleDigCoreV110922,
    ]
    LayCores = [
        data1d.Data1dLayCoreV110922,
        equilibrium.EquilibriumLayCoreV110922,
        history.HistoryLayCoreV110922,
        snapshot.SnapshotLayCoreV110922,
        snapphizeta.SnapPhiZetaPsiLayCoreV3,
        trackparticle.TrackParticleLayCoreV110922,
    ]
    pckversion = 'GTCV3.14-22'
