# -*- coding: utf-8 -*-

# Copyright (c) 2023 shmilee

'''
Source fortran code:

v3.21-120-g789e716e
-------------------
shmilee.F90, subroutine snap_loop_fluxdata_psi
    write(iofluxdata,101)mpsi-1,nfield,mtoroidal
    do i=1,mpsi-1
        write(iofluxdata,101)mtgrid
        allocate(eachflux(mtgrid),allflux(mtgrid,mtoroidal))
        write(iofluxdata,102)allflux
'''

import numpy as np

from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog
from .snapshot import (SnapshotFieldFluxDigger,
                       SnapshotFieldFluxTileDigger,
                       SnapshotFieldFluxCorrLenDigger)

from .gtc import Ndigits_tstep
from .. import tools

_all_Converters = ['SnapFluxDataConverter']
_all_Diggers = ['SnapFluxDataDigger', 'SnapFluxDataTileDigger',
                'SnapFluxDataCorrLenDigger']
__all__ = _all_Converters + _all_Diggers


class SnapFluxDataConverter(Converter):
    '''
    Snapshot fieldflux(theta, zeta) Data: phi, apara etc.

    Shape of data is (mtheta(ipsi), mtoroidal) for each ipsi
    '''
    __slot__ = []
    nitems = '?'
    itemspattern = ['^(?P<section>snap\d{5,7})_fluxdata\.out$',
                    '.*/(?P<section>snap\d{5,7})_fluxdata\.out$']
    _datakeys = (
        # 1. parameters
        'mpsi-1', 'nfield', 'mtoroidal',
        # 2. fluxdata allflux('mtgrid', mtoroidal), 1<=ipsi<=mspi-1
        r'mtgrid-%d', r'flux-phi-%d', r'flux-apara-%d'
    )

    @property
    def groupnote(self):
        return '%s-fluxdata' % self._group

    def _convert(self):
        '''Read 'snap%05d-fluxdata.out' % istep.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        # 1. parameters
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:3]))
        for i, key in enumerate(self._datakeys[:3]):
            sd.update({key: int(outdata[i].strip())})
        # 2. mtgrid, allflux
        idx0 = 3
        for ipsi in range(1, sd['mpsi-1']+1):
            mtgrid = int(outdata[idx0].strip())
            idx0 = idx0 + 1
            key = r'mtgrid-%d' % ipsi
            clog.debug("Filling datakeys: %s=%d ..." % (key, mtgrid))
            sd[key] = mtgrid
            size = mtgrid * sd['mtoroidal'] * sd['nfield']
            shape = (mtgrid, sd['mtoroidal'], sd['nfield'])
            idx1 = idx0 + size
            tmpdata = np.array([float(n.strip()) for n in outdata[idx0:idx1]])
            allflux = tmpdata.reshape(shape, order='F')
            key = r'fluxdata-phi-%d' % ipsi
            clog.debug("Filling datakeys: %s ..." % key)
            sd[key] = allflux[:, :, 0]
            if sd['nfield'] == 2:
                key = r'fluxdata-apara-%d' % ipsi
                clog.debug("Filling datakeys: %s ..." % key)
                sd[key] = allflux[:, :, 1]
            idx0 = idx1
        _ = sd.pop('nfield')
        - = sd.pop('mtoroidal')
        return sd


class SnapFluxDataDigger(SnapshotFieldFluxDigger):
    '''phi, a_para on every flux surface.'''
    __slots__ = []
    itemspattern = ['^(?P<section>snap\d{5,7})'
                    + '/fluxdata-(?P<field>(?:phi|apara))-(?P<ipsi>\d+)']
    _field_theta_start0 = False

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_flux_%03d' % (self.section[1], self.ipsi)


class SnapFluxDataTileDigger(SnapFluxDataDigger, SnapshotFieldFluxTileDigger):
    '''Tiled phi, a_para on every flux surface.'''
    __slots__ = []
    commonpattern = ['gtc/tstep', 'gtc/arr2']

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_flux_%03d_tiled' % (self.section[1], self.ipsi)
        self.kwoptions = None

    def _get_q_psi(self):
        '''Return q at ipsi.'''
        return self.pckloader.get('gtc/arr2')[self.ipsi-1, 2]


class SnapFluxDataCorrLenDigger(SnapFluxDataTileDigger, SnapshotFieldFluxCorrLenDigger):
    '''Get phi correlation(d_zeta, d_theta) from tiled flux surface.'''
    __slot__ = []

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_flux_%03d_corrlen' % (self.section[1], self.ipsi)
        self.kwoptions = None
