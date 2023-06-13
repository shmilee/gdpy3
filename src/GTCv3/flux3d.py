# -*- coding: utf-8 -*-

# Copyright (c) 2023 shmilee

'''
Source fortran code:

v3.26-49-g400f979b
-------------------
shmilee.F90, shmilee_flux3da_diag, subroutine flux3da_diagnosis
    write(ioflux3d,101) flux3d_iflux-diflux, flux3d_iflux+diflux, &
        & digrid, mtoroidal, flux3d_nfield, flux3d_fields
    do i=flux3d_iflux-diflux,flux3d_iflux+diflux
        write(ioflux3d,101) mtheta(i)
    enddo
    write(ioflux3d,102) flux3d

shmilee.F90, shmilee_flux3dt_diag, subroutine flux3dt_diagnosis
    if(myrank_toroidal==0)then
        ! parameters: shape of data; selected psi; and field info
        write(ioflux3d,101)mzeach,iflux0,iflux1,flux3d_mthetamax, flux3d_nfield, flux3d_fields
    endif
    write(ioflux3d,102)flux3d !(mzeach,iflux0:iflux1,flux3d_mthetamax,flux3d_nfield)
'''

import re
import numpy as np

from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog
from .snapshot import (SnapshotFieldFluxDigger,
                       SnapshotFieldFluxTileDigger,
                       SnapshotFieldFluxCorrLenDigger)
from .zetapsi3d import field_tex_str
from .gtc import Ndigits_tstep
from .. import tools

_all_Converters = ['Flux3DaConverter', 'Flux3DtConverter']
_all_Diggers = ['Flux3DaDigger', 'Flux3DaTileDigger', 'Flux3DaCorrLenDigger',
                'Flux3DtDigger', 'Flux3DtTileDigger']  # , 'Flux3DtCorrLenDigger']
__all__ = _all_Converters + _all_Diggers


class Flux3DaConverter(Converter):
    '''
    field flux3da(alpha, zeta, psi)
    Data: 1 phi, 2 a_para, 3 fluidne, 4 densityi, 5 temperi,
          6 densitye, 7 tempere, 8 densityf, 9 temperf etc.

    Shape of data is (mtheta(ipsi), mtoroidal) for each ipsi
    '''
    __slot__ = []
    nitems = '?'
    itemspattern = ['^phi_dir/(?P<section>flux3da\d{5})\.out$',
                    '.*/phi_dir/(?P<section>flux3da\d{5})\.out$']
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
        '''Read 'phi_dir/flux3da%05d.out' % istep.'''
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
        flux3d_fields = [int(v.strip())
                         for v in outdata[idx0:idx0+sd['nfield']]]
        fields_name = []
        for nf in flux3d_fields:
            fields_name.append(self._datakeys[5+nf])  # nf=1 -> phi
        assert len(fields_name) == sd['nfield']
        idx0 = idx0 + sd['nfield']
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


class Flux3DtConverter(Converter):
    '''
    field flux3dt(theta, zeta, psi)
    Data: 1 phi, 2 a_para, 3 fluidne, 4 densityi, 5 temperi,
          6 densitye, 7 tempere, 8 densityf, 9 temperf etc.

    Shape of data is (mthetamax, mtoroidal*mzeach) for each ipsi
    '''
    __slot__ = []
    nitems = '+'
    itemspattern = ['^phi_dir/(?P<section>flux3dt\d{5})_tor\d{4}\.out$',
                    '.*/phi_dir/(?P<section>flux3dt\d{5})_tor\d{4}\.out$']
    _datakeys = (
        # 1. parameters
        'mzeach', 'iflux0', 'iflux1', 'mthetamax', 'nfield',
        # 2. flux3d(mzeach,iflux0:iflux1,flux3d_mthetamax,flux3d_nfield)
        'phi', 'apara', 'fluidne',  # -%d % ipsi
        'densityi', 'temperi', 'densitye', 'tempere', 'densityf', 'temperf'
    )

    def _convert(self):
        '''Read 'phi_dir/flux3da%05d.out' % istep.'''
        fdata = []
        # tor0000.out
        f = self.files[0]
        with self.rawloader.get(f) as fid:
            clog.debug("Read file '%s'." % f)
            # parameters
            mzeach, iflux0, iflux1, mthetamax, nfield = \
                (int(fid.readline()) for j in range(5))
            nflux = iflux1 - iflux0 + 1
            ft3d_fields = [int(fid.readline().strip()) for v in range(nfield)]
            fields_name = []
            for nf in ft3d_fields:
                fields_name.append(self._datakeys[4+nf])  # nf=1 -> phi
            assert len(fields_name) == nfield
            # data
            shape = (mzeach, nflux, mthetamax, nfield)
            outdata = np.array([float(n.strip()) for n in fid.readlines()])
            fdata.extend(outdata.reshape(shape, order='F'))
        # tor0001.out ...
        for f in self.files[1:]:
            with self.rawloader.get(f) as fid:
                outdata = np.array([float(n.strip()) for n in fid.readlines()])
                fdata.extend(outdata.reshape(shape, order='F'))
        fdata = np.array(fdata)
        mtoroidal = len(self.files)
        assert fdata.shape == (mzeach*mtoroidal, nflux, mthetamax, nfield)
        # 1. parameters
        clog.debug("Filling datakeys: %s ..."
                   % 'mzeach, iflux0, iflux1, mthetamax')
        sd = dict(mzeach=mzeach, iflux0=iflux0,
                  iflux1=iflux1, mthetamax=mthetamax)
        # 2. data
        for nf in range(nfield):
            for idx, i in enumerate(range(iflux0, iflux1+1)):
                key = r'%s-%d' % (fields_name[nf], i)
                clog.debug("Filling datakeys: %s ..." % key)
                sd[key] = fdata[:, idx, :, nf].T  # -> (mtheta, mzeta)
        return sd


class Flux3DaDigger(SnapshotFieldFluxDigger):
    '''phi(alpha,zeta), a_para on every flux surface.'''
    __slots__ = []
    itemspattern = [
        '^(?P<section>flux3da\d{5,7})/(?P<field>(?:phi|apara|fluidne|densityi'
        + '|temperi|densitye|tempere|densityf|temperf))-(?P<ipsi>\d+)']
    _field_theta_start0 = True

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_%03d' % (self.section[1], self.ipsi)

    def _get_timestr(self):
        istep = int(re.match('.*flux3da(\d{5,7}).*', self.group).groups()[0])
        tstep = self.pckloader.get('gtc/tstep')
        time = round(istep * tstep, Ndigits_tstep)
        return r'istep=%d, time=%s$R_0/c_s$' % (istep, time)

    def _get_fieldstr(self):
        return field_tex_str[self.section[1]]


class Flux3DaTileDigger(Flux3DaDigger, SnapshotFieldFluxTileDigger):
    '''Tiled phi(alpha,zeta), a_para, etc. on every flux surface.'''
    __slots__ = []
    commonpattern = ['gtc/tstep', 'gtc/arr2']

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_%03d_tiled' % (self.section[1], self.ipsi)
        self.kwoptions = None

    def _get_q_psi(self):
        '''Return q at ipsi.'''
        return self.pckloader.get('gtc/arr2')[self.ipsi-1, 2]


class Flux3DaCorrLenDigger(Flux3DaTileDigger, SnapshotFieldFluxCorrLenDigger):
    '''Get phi correlation(d_zeta, d_theta) from tiled flux surface.'''
    __slot__ = []

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_%03d_corrlen' % (self.section[1], self.ipsi)
        self.kwoptions = None


class Flux3DtDigger(SnapshotFieldFluxDigger):
    '''phi(theta,zeta), a_para on every flux surface.'''
    __slots__ = []
    itemspattern = [
        '^(?P<section>flux3dt\d{5,7})/(?P<field>(?:phi|apara|fluidne|densityi'
        + '|temperi|densitye|tempere|densityf|temperf))-(?P<ipsi>\d+)']
    _field_theta_start0 = False

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_%03d' % (self.section[1], self.ipsi)

    def _get_timestr(self):
        istep = int(re.match('.*flux3dt(\d{5,7}).*', self.group).groups()[0])
        tstep = self.pckloader.get('gtc/tstep')
        time = round(istep * tstep, Ndigits_tstep)
        return r'istep=%d, time=%s$R_0/c_s$' % (istep, time)

    def _get_fieldstr(self):
        return field_tex_str[self.section[1]]


class Flux3DtTileDigger(Flux3DtDigger):
    '''Tiled phi(theta,zeta), a_para, etc. on every flux surface.'''
    __slots__ = []
    commonpattern = ['gtc/tstep']

    def _set_fignum(self, numseed=None):
        super(Flux3DtTileDigger, self)._set_fignum(numseed=numseed)
        self._fignum = '%s_tiled' % self._fignum
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *N*: int, >=2, default 2
            how many zeta(2pi) will be tiled
        *M*: int, >=2, default 2
            how many theta(2pi) will be tiled
        '''
        res, _ = super(Flux3DtTileDigger, self)._dig(kwargs)
        title, zeta = res['title'], res['zeta']
        field, theta = res['field'], res['theta']  # (0, 2pi]
        N, M = kwargs.get('N', 2), kwargs.get('M', 2)
        if not (isinstance(N, int) and N >= 2):
            N = 2
        if not (isinstance(M, int) and M >= 2):
            M = 2
        if self.kwoptions is None:
            self.kwoptions = dict(
                N=dict(widget='IntSlider',
                       rangee=(2, 5, 1),
                       value=2,
                       description='zeta N_2pi:'),
                M=dict(widget='IntSlider',
                       rangee=(2, 5, 1),
                       value=2,
                       description='theta N_2pi:'))
        acckwargs = dict(N=N, m=M)
        for i in range(1, N):
            field = np.column_stack((field, res['field']))
            zeta = np.append(zeta, res['zeta']+2*np.pi*i)
        fieldM = field
        for j in range(1, M):
            fieldM = np.row_stack((fieldM, field))
            theta = np.append(theta, res['theta']+2*np.pi*j)
        # print(fieldM.shape, zeta.shape, theta.shape)
        return dict(title=title, field=fieldM,
                    zeta=zeta, theta=theta), acckwargs
