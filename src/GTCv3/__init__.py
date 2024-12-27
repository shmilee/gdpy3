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

import numpy as np
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
    theta1d,
    zetapsi3d,
    flux3d,
    phase2d,
    snapevphase,
    snapphi,
)
from ..processors.processor import plog
from ..loaders.base import log as llog

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
    theta1d,
    zetapsi3d,
    flux3d,
    phase2d,
    snapevphase,
    snapphi,
)


def _get_sprgpsi(loader):
    sprgpsi = loader.get('simugrid/sprgpsi', None)
    if sprgpsi is None:
        arr2 = loader.get('gtc/arr2', None)
        if arr2 is not None:
            rg0 = loader['gtc/rg0']*loader['gtc/a_minor']
            rg1 = loader['gtc/rg1']*loader['gtc/a_minor']
            rgpsi = arr2[:, 1]  # set 1 to mpsi-1
            # insert 0 and mpsi
            sprgpsi = np.insert(rgpsi, 0, rg0)
            sprgpsi = np.append(sprgpsi, rg1)
            assert sprgpsi.size == loader['gtc/mpsi']+1
    if sprgpsi is None:
        raise ValueError("Cann't get virtual key: gtc/sprgpsi!  rg!rg!")
    else:
        return sprgpsi


def _get_sprpsi(loader):
    sprpsi = loader.get('meshgrid/sprpsi', None)
    if sprpsi is None:
        sprpsi = loader.get('simugrid/sprpsi', None)
    if sprpsi is None:
        # TODO use equilibrium/1d-data[23] interpolation?
        # then rgpsi
        if loader['gtc/iload'] > 1:  # non-uniform marker
            llog.warning("When iload>1 using sprgpsi as sprpsi is incorrect!")
        sprpsi = _get_sprgpsi(loader)
    if sprpsi is None:
        raise ValueError("Cann't get virtual key: gtc/sprpsi!  r!r!")
    else:
        return sprpsi


def _get_qmesh(loader):
    qmesh = loader.get('meshgrid/qmesh', None)
    if qmesh is None:
        qmesh = loader.get('simugrid/qmesh', None)
    if qmesh is None:
        arr2 = loader.get('gtc/arr2', None)
        if arr2 is not None:
            qpsi = arr2[:, 2]  # set 1 to mpsi-1
            # guess & insert 0 and mpsi; TODO equilibrium/1d-data[19]?
            q0 = 2.0*qpsi[0] - qpsi[1]
            q1 = 2.0*qpsi[-1] - qpsi[-2]
            qmesh = np.insert(qpsi, 0, q0)
            qmesh = np.append(qmesh, q1)
            assert qmesh.size == loader['gtc/mpsi']+1
    if qmesh is None:
        raise ValueError("Cann't get virtual key: gtc/qmesh!")
    else:
        return qmesh


_pckloader_virtual_data = {
    'gtc/sprgpsi': _get_sprgpsi,
    'gtc/sprpsi': _get_sprpsi,
    'gtc/qmesh': _get_qmesh,
}


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

    @property
    def _default_exclude_raw_dirs(self):
        return ['restart_dir1', 'restart_dir2']

    @property
    def _default_pckloader_virtual_data(self):
        return _pckloader_virtual_data
