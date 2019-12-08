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
from ..processors.processor import Processor

__all__ = ['GTCv3']


class GTCv3(Processor):
    __slots__ = []
    ConverterCores = [
        gtc.GtcConverter,
        data1d.Data1dConverter,
        equilibrium.EquilibriumConverter,
        history.HistoryConverter,
        meshgrid.MeshgridConverter,
        snapshot.SnapshotConverter,
        snapphi.SnapPhiZetaPsiConverter,
        trackparticle.TrackParticleConverter,
    ]
    DiggerCores = [
        data1d.Data1dFluxDigger,
        data1d.Data1dFieldDigger,
        equilibrium.EquilibriumPsi1DDigger,
        equilibrium.EquilibriumRadial1DDigger,
        equilibrium.EquilibriumErro1DDigger,
        equilibrium.EquilibriumPoloidalDigger,
        equilibrium.EquilibriumMeshDigger,
        equilibrium.EquilibriumThetaDigger,
        history.HistoryParticleDigger,
        history.HistoryFieldDigger,
        history.HistoryFieldModeDigger,
        snapshot.SnapshotProfilePdfDigger,
        snapshot.SnapshotFieldFluxPloidalDigger,
        snapshot.SnapshotFieldSpectrumDigger,
        snapshot.SnapshotFieldProfileDigger,
        snapphi.SnapPhiZetaPsiDigger,
        snapphi.SnapPhiCorrLenDigger,
        trackparticle.TrackParticleOrbitDigger,
    ]
    saltname = 'gtc.out'
    dig_acceptable_time = 20

    @property
    def _rawsummary(self):
        return "GTC '.out' files in %s '%s'" % (
            self.rawloader.loader_type, self.rawloader.path)
