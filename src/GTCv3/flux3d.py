# -*- coding: utf-8 -*-

# Copyright (c) 2023 shmilee

'''
Source fortran code:

v3.26-41-g23d5f35a
-------------------
shmilee.F90, shmilee_flux3d_diag, subroutine flux3d_loop
    write(ioflux3d,101) flux3d_iflux-diflux, flux3d_iflux+diflux, &
        & digrid, mtoroidal, flux3d_nfield, flux3d_fields
    do i=flux3d_iflux-diflux, flux3d_iflux+diflux
        write(ioflux3d,101) mtheta(i)
    enddo
    write(ioflux3d,102) flux3d

shmilee.F90, shmilee_flux3d_diag, subroutine flux3d_once
    write(ioflux3d,101) flux3d_iflux-diflux, flux3d_iflux+diflux, digrid, mtoroidal
    do i=flux3d_iflux-diflux,flux3d_iflux+diflux
        write(ioflux3d,101) mtheta(i)
    enddo
    write(ioflux3d,102) coord3d
'''

import re
import numpy as np

from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog
from .snapshot import (SnapshotFieldFluxDigger,
                       SnapshotFieldFluxTileDigger,
                       SnapshotFieldFluxCorrLenDigger)

from .gtc import Ndigits_tstep
from .. import tools

_all_Converters = ['Flux3DConverter', 'Flux3DCoordConverter']
_all_Diggers = ['Flux3DDigger', 'Flux3DTileDigger',
                'Flux3DCorrLenDigger', 'Flux3DCoordDigger']
__all__ = _all_Converters + _all_Diggers


class Flux3DConverter(Converter):
    '''
    field flux3d(theta, zeta, psi)
    Data: 1 phi, 2 a_para, 3 fluidne, 4 densityi, 5 temperi,
          6 densitye, 7 tempere, 8 densityf, 9 temperf etc.

    Shape of data is (mtheta(ipsi), mtoroidal) for each ipsi
    '''
    __slot__ = []
    nitems = '?'
    itemspattern = ['^phi_dir/(?P<section>flux3d\d{5,7})\.out$',
                    '.*/phi_dir/(?P<section>flux3d\d{5,7})\.out$']
    _datakeys = (
        # 1. parameters
        'iflux0', 'iflux1', 'digrid', 'mtoroidal', 'nfield',
        r'mtgrid+1-%d',  # ipsi
        # 2. flux3d(digrid, mtoroidal, flux3d_nfield)
        #    allflux(mtgrid+1, mtoroidal), iflux0<=ipsi<=iflux1
        'phi', 'apara', 'fluidne',  # -%d % ipsi
        'densityi', 'temperi', 'densitye', 'tempere', 'densityf', 'temperf'
    )

    def _convert(self):
        '''Read 'phi_dir/flux3d%05d.out' % istep.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        # 1. parameters
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:5]))
        for i, key in enumerate(self._datakeys[:5]):
            sd.update({key: int(outdata[i].strip())})
        # 2. mtgrid, allflux
        idx0 = 5
        flux3d_fields = [int(v.strip()) for v in outdata[idx0:idx0+9]]
        fields_name = []
        for nf, enable in enumerate(flux3d_fields, 1):
            if enable > 0:
                fields_name.append(self._datakeys[5+nf])  # nf=1 -> phi
        assert len(fields_name) == sd['nfield']
        idx0 = idx0 + 9
        mtgrid_dict = {
            ipsi: int(outdata[idx0+i].strip())
            for i, ipsi in enumerate(range(sd['iflux0'], sd['iflux1']+1))}
        idx0 = idx0 + len(mtgrid_dict)
        tmpdata = np.array([float(n.strip()) for n in outdata[idx0:]])
        shape = (sd['digrid'], sd['mtoroidal'], sd['nfield'])
        size = sd['digrid'] * sd['mtoroidal'] * sd['nfield']
        assert len(tmpdata) == size
        tmpdata = tmpdata.reshape(shape, order='F')
        # split fluxes
        igrid1 = 0
        for ipsi in range(sd['iflux0'], sd['iflux1']+1):
            mtgrid1 = mtgrid_dict[ipsi] + 1
            key = r'mtgrid+1-%d' % ipsi
            clog.debug("Filling datakeys: %s=%d ..." % (key, mtgrid1))
            sd[key] = mtgrid1
            igrid0 = igrid1
            igrid1 = igrid0 + mtgrid1  # slice grids of ipsi
            # print(igrid0, igrid1)
            for nf in range(sd['nfield']):
                key = r'%s-%d' % (fields_name[nf], ipsi)
                clog.debug("Filling datakeys: %s ..." % key)
                sd[key] = tmpdata[igrid0:igrid1, :, nf]
        # _ = sd.pop('mtoroidal')
        return sd


class Flux3DCoordConverter(Converter):
    '''
    cartesian coordinates X(theta, zeta, psi), Y, Z for field flux3d
    Shape of data is (mtheta(ipsi), mtoroidal) for each ipsi
    '''
    __slot__ = []
    nitems = '?'
    itemspattern = ['^phi_dir/(?P<section>flux3dcoord)\.out$',
                    '.*/phi_dir/(?P<section>flux3dcoord)\.out$']
    _datakeys = (
        # 1. parameters
        'iflux0', 'iflux1', 'digrid', 'mtoroidal', r'mtgrid+1-%d',  # ipsi
        # 2. allcoord(mtgrid+1, mtoroidal), iflux0<=ipsi<=iflux1
        'X', 'Y', 'Z',  # -%d % ipsi
    )

    def _convert(self):
        '''Read 'phi_dir/flux3dcoord.out' % istep.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        # 1. parameters
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:4]))
        for i, key in enumerate(self._datakeys[:4]):
            sd.update({key: int(outdata[i].strip())})
        mtgrid_dict = {
            ipsi: int(outdata[4+i].strip())
            for i, ipsi in enumerate(range(sd['iflux0'], sd['iflux1']+1))}
        idx0 = 4 + len(mtgrid_dict)
        # 2. X Y Z-ipsi
        tmpdata = np.array([float(n.strip()) for n in outdata[idx0:]])
        shape = (sd['digrid'], sd['mtoroidal'], 3)
        size = sd['digrid'] * sd['mtoroidal'] * 3
        assert len(tmpdata) == size
        tmpdata = tmpdata.reshape(shape, order='F')
        igrid1 = 0
        for ipsi in range(sd['iflux0'], sd['iflux1']+1):
            mtgrid1 = mtgrid_dict[ipsi] + 1
            key = r'mtgrid+1-%d' % ipsi
            clog.debug("Filling datakeys: %s=%d ..." % (key, mtgrid1))
            sd[key] = mtgrid1
            igrid0 = igrid1
            igrid1 = igrid0 + mtgrid1
            for x in range(3):
                key = r'%s-%d' % (self._datakeys[5+x], ipsi)
                clog.debug("Filling datakeys: %s ..." % key)
                sd[key] = tmpdata[igrid0:igrid1, :, x]
        return sd


field_tex_str = {
    'phi': r'\phi',
    'apara': r'A_{\parallel}',
    'fluidne': r'fluid n_e',
    'densityi': r'\delta n_i',
    'densitye': r'\delta n_e',
    'densityf': r'\delta n_f',
    'temperi': r'\delta T_i',
    'tempere': r'\delta T_e',
    'temperf': r'\delta T_f',
}


class Flux3DDigger(SnapshotFieldFluxDigger):
    '''phi, a_para on every flux surface.'''
    __slots__ = []
    itemspattern = [
        '^(?P<section>flux3d\d{5,7})/(?P<field>(?:phi|apara|fluidne|densityi'
        + '|temperi|densitye|tempere|densityf|temperf))-(?P<ipsi>\d+)']
    _field_theta_start0 = True

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_%03d' % (self.section[1], self.ipsi)

    def _get_timestr(self):
        istep = int(re.match('.*flux3d(\d{5,7}).*', self.group).groups()[0])
        tstep = self.pckloader.get('gtc/tstep')
        time = round(istep * tstep, Ndigits_tstep)
        return r'istep=%d, time=%s$R_0/c_s$' % (istep, time)

    def _get_fieldstr(self):
        return field_tex_str[self.section[1]]


class Flux3DTileDigger(Flux3DDigger, SnapshotFieldFluxTileDigger):
    '''Tiled phi, a_para, etc. on every flux surface.'''
    __slots__ = []
    commonpattern = ['gtc/tstep', 'gtc/arr2']

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_%03d_tiled' % (self.section[1], self.ipsi)
        self.kwoptions = None

    def _get_q_psi(self):
        '''Return q at ipsi.'''
        return self.pckloader.get('gtc/arr2')[self.ipsi-1, 2]


class Flux3DCorrLenDigger(Flux3DTileDigger, SnapshotFieldFluxCorrLenDigger):
    '''Get phi correlation(d_zeta, d_theta) from tiled flux surface.'''
    __slot__ = []

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_%03d_corrlen' % (self.section[1], self.ipsi)
        self.kwoptions = None


class Flux3DCoordDigger(Digger):
    '''show flux surface for each psi.'''
    __slots__ = ['ipsi']
    nitems = '?'
    itemspattern = ['^(?P<section>flux3dcoord)/Z-(?P<ipsi>\d+)$']
    commonpattern = ['gtc/arr2']
    post_template = 'tmpl_contourf'

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%03d' % self.ipsi
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *addzeta0*: add zeta=0, use data from zeta=2pi, default True
        '''
        X = self.pckloader.get("%s/X-%d" % (self.group, self.ipsi))
        Y = self.pckloader.get("%s/Y-%d" % (self.group, self.ipsi))
        Z = self.pckloader.get("%s/Z-%d" % (self.group, self.ipsi))
        addzeta0 = kwargs.get('addzeta0', True)
        if self.kwoptions is None:
            self.kwoptions = dict(
                addzeta0=dict(widget='Checkbox',
                              value=bool(addzeta0),
                              description='add zeta=0:'))
        acckwargs = dict(addzeta0=bool(addzeta0))
        if addzeta0:
            q = self.pckloader.get('gtc/arr2')[self.ipsi-1, 2]
            sep = round(Z.shape[0]*(1.0-1.0/q))  # q>1
            if sep != 0:
                X0 = np.row_stack((X[sep:, -2:], X[:sep, -2:]))[:, -1]
                Y0 = np.row_stack((Y[sep:, -2:], Y[:sep, -2:]))[:, -1]
                Z0 = np.row_stack((Z[sep:, -2:], Z[:sep, -2:]))[:, -1]
                X = np.column_stack((X0, X))
                Y = np.column_stack((Y0, Y))
                Z = np.column_stack((Z0, Z))
            else:
                X = np.column_stack((X[:, -1], X))
                Y = np.column_stack((Y[:, -1], Y))
                Z = np.column_stack((Z[:, -1], Z))
        return dict(X=X, Y=Y, Z=Z,
                    title='flux surface(ipsi=%d)' % self.ipsi), acckwargs

    def _post_dig(self, results):
        r = results
        return dict(X=r['X'], Y=r['Y'], Z=r['Z'], plot_method='plot_surface',
                    title=r['title'], xlabel=r'$X$',
                    ylabel=r'$Y$', aspect='equal')
