# -*- coding: utf-8 -*-

# Copyright (c) 2023 shmilee

'''
Source fortran code:

v3.26-49-g400f979b
-------------------
shmilee.F90, shmilee_flux3d_diag, subroutine flux3d_diagnosis
    write(ioflux3d,101) flux3d_iflux-diflux, flux3d_iflux+diflux, &
        & digrid, mtoroidal, flux3d_nfield, flux3d_fields
    do i=flux3d_iflux-diflux,flux3d_iflux+diflux
        write(ioflux3d,101) mtheta(i)
    enddo
    write(ioflux3d,102) flux3d
'''

import re
import numpy as np

from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog
from .snapshot import (SnapshotFieldFluxAlphaDigger,
                       SnapshotFieldFluxThetaDigger,
                       SnapshotFieldFluxAlphaTileDigger,
                       SnapshotFieldFluxThetaTileDigger,
                       SnapshotFieldFluxAlphaTileFFTDigger,
                       SnapshotFieldFluxAlphaCorrLenDigger,
                       SnapshotFieldFluxTimeDigger,
                       SnapshotFieldFluxTimeFFTDigger,
                       _snap_get_timestr,
                       _fluxdata_theta_interpolation)
from .zetapsi3d import field_tex_str
from .gtc import Ndigits_tstep
from .. import tools

_all_Converters = ['Flux3DConverter']
_all_Diggers = ['Flux3DAlphaDigger', 'Flux3DThetaDigger',
                'Flux3DAlphaTileDigger', 'Flux3DThetaTileDigger',
                'Flux3DAlphaTileFFTDigger',
                'Flux3DAlphaCorrLenDigger',
                'Flux3DAlphaTimeDigger', 'Flux3DAlphaTimeFFTDigger']
__all__ = _all_Converters + _all_Diggers


class Flux3DConverter(Converter):
    '''
    field flux3d(alpha, zeta, psi)
    Data: 1 phi, 2 a_para, 3 fluidne, 4 densityi, 5 temperi,
          6 densitye, 7 tempere, 8 densityf, 9 temperf etc.

    Shape of data is (mtheta(ipsi), mtoroidal) for each ipsi
    '''
    __slot__ = []
    nitems = '?'
    itemspattern = [r'^phi_dir/(?P<section>flux3da*\d{5})\.out$',
                    r'.*/phi_dir/(?P<section>flux3da*\d{5})\.out$']
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
        r'''Read 'phi_dir/flux3da*\d{5}.out'. '''
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


class Flux3DAlphaDigger(SnapshotFieldFluxAlphaDigger):
    '''phi(alpha,zeta), a_para etc. on every flux surface.'''
    __slots__ = []
    itemspattern = [
        r'^(?P<section>flux3da*\d{5,7})/(?P<field>(?:phi|apara|fluidne|densityi'
        + r'|temperi|densitye|tempere|densityf|temperf))-(?P<ipsi>\d+)']

    def _set_group(self):
        r'''Set :attr:`group`, 'flux3da(\d{5,7})' -> 'flux3d(\d{5,7})' .'''
        if 'flux3da' in self.section[0]:
            self._group = self.section[0].replace('flux3da', 'flux3d')
        else:
            self._group = self.section[0]

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_%03da' % (self.section[1], self.ipsi)

    def _get_timestr(self):
        return _snap_get_timestr(self.group, self.pckloader,
                                 pat=r'.*flux3da*(\d{5,7}).*')

    def _get_fieldstr(self):
        return field_tex_str[self.section[1]]


class Flux3DThetaDigger(Flux3DAlphaDigger, SnapshotFieldFluxThetaDigger):
    '''phi(theta,zeta), a_para etc. on every flux surface.'''
    __slots__ = []
    commonpattern = ['gtc/tstep', 'gtc/qmesh']

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_%03dt' % (self.section[1], self.ipsi)
        self.kwoptions = None

    def _get_q_psi(self):
        '''Return q at ipsi.'''
        return self.pckloader['gtc/qmesh'][self.ipsi]


def _flux3d_interpolate_worker(i, total, data, q, iM, iN, fielddir):
    '''
    Interpolate flux(alpha,zeta) -> flux(theta,zeta). Return flux(theta,zeta)
    '''
    logstep = max(1, round(total/10))
    res = _fluxdata_theta_interpolation(data, q, iM, iN, fielddir)[2]
    if (i+1) % logstep == 0 or i == 0 or i+1 == total:
        dlog.info("Interpolation %d/%d, done." % (i+1, total))
    return res


def flux3d_interpolate_stack(loader, iM, iN, field, fielddir=0,
                             float64=False, savepath=None, dry=False):
    '''
    Interpolate of flux(alpha,zeta) -> flux(theta,zeta), then stack 2-D array
    into a 4-D array flux(time,psi,theta,zeta).
    Save time, ipsi, theta, zeta, flux 4-D array in *savepath*.

    Parameters
    ----------
    loader: pckloader instance
    iM: int, interpolation grid points in theta
    iN: int, interpolation grid points in zeta
    field: str, phi|apara|fluidne|densityi|temperi|densitye etc.
    fielddir: int, 0, 1, 2 or 3, magnetic field & current direction
    float64: bool, default False
        array dtype is float64 or float32, default float32
    savepath: str, pcksaver path
        default 'gtcv3-XXXXXX.flux4d-%s-iM%d-iN%d.npz' % (field, iM, iN)
    dry: bool, dry run, show array info then return
    '''
    import os
    import time as mod_time
    import multiprocessing
    from ..savers import get_pcksaver
    from .. import __gversion__

    _pat = re.compile(r'^flux3da*\d{5,7}/%s-(?P<ipsi>\d+)' % field)
    keys = loader.refind(_pat)
    if not keys:
        dlog.error('Flux3d of %s: Not Found! Try phi, densityi etc.' % field)
        return
    _pat = re.compile(r'^%s/%s-(?P<ipsi>\d+)' % (keys[0].split('/')[0], field))
    psis = [k.split('-')[1] for k in loader.refind(_pat)]
    _pat = re.compile(r'^flux3da*\d{5,7}/%s-%s' % (field, psis[0]))
    steps = [re.match(r'^flux3da*(\d{5,7})/.*', k).groups()[0]
             for k in loader.refind(_pat)]
    if len(steps)*len(psis) - len(keys) != 0:
        dlog.error('Wrong keys len(steps)*len(psis)=%d*%d=%d != len(keys)=%d',
                   (len(steps), len(psis), len(steps)*len(psis), len(keys)))
        return
    keys = np.array(keys).reshape((len(steps), len(psis)))
    qs = [loader['gtc/qmesh'][int(ipsi)] for ipsi in psis]
    tstep = loader.get('gtc/tstep')
    time = np.array([round(int(i) * tstep, Ndigits_tstep) for i in steps])
    ipsi = np.array([int(i) for i in psis])
    theta = np.arange(0, iM) / (iM-1) * 2*np.pi
    zeta = np.arange(0, iN) / (iN-1) * 2*np.pi
    shape = (len(steps), len(psis), iM, iN)
    size = len(steps)*len(psis)*iM*iN*(8 if float64 else 4)/1024/1024  # MB
    dlog.info('%s 4-D array shape: %s, size=%.1fMB' % (field, shape, size))
    dlog.info('steps found(%d): %s ... ... %s'
              % (len(steps), steps[:5], steps[-5:]))
    dlog.info('psis found(%d): %s ... ... %s' %
              (len(psis), psis[:5], psis[-5:]))
    if dry:
        return
    if savepath is None:
        idx = loader.path.rfind('.converted.')
        if idx < 0:
            dlog.error('Cannot set default savepath by loader.path!')
            return
        name = 'flux4d-%s-iM%d-iN%d' % (field, iM, iN)
        savepath = '.'.join([loader.path[:idx], name, loader.path[idx+11:]])
        dlog.info('Default flux4d data path is %s.' % savepath)
    if os.path.exists(savepath):
        dlog.warning("Path '%s' exists!" % savepath)

    if float64:
        f4d_arr = np.zeros(shape, dtype=np.float64)
    else:
        f4d_arr = np.zeros(shape, dtype=np.float32)
    for i in range(len(psis)):
        dlog.info("Getting raw-data of %s(ipsi=%s), q=%f" %
                  (field, psis[i], qs[i]))
        rawdata = loader.get_many(*keys[:, i])
        total = len(rawdata)
        nproc = min(multiprocessing.cpu_count(), total)
        with multiprocessing.Pool(processes=nproc) as pool:
            results = [
                pool.apply_async(
                    _flux3d_interpolate_worker,
                    (idx, total, rawdata[idx], qs[i], iM, iN, fielddir)
                ) for idx in range(total)
            ]
            pool.close()
            pool.join()
        dlog.info("Set interpolate-data of ipsi=%s, q=%f" % (psis[i], qs[i]))
        # tmp(time, psi=i, theta, zeta)
        tmp = [res.get() for res in results]
        f4d_arr[:, i, :, :] = tmp
        loader.clear_cache()
    desc = "Flux4D array: %s(time, psi, theta, zeta)." % field
    desc = ("%s\nCreated by gdpy3 v%s.\nCreated on %s."
            % (desc, __gversion__, mod_time.asctime()))
    with get_pcksaver(savepath) as saver:
        dlog.info("Writing interpolate-data(size=%.1fMB) of %s ..." %
                  (size, field))
        saver.write('/', {
            field: f4d_arr,
            'time': time,
            'ipsi': ipsi,
            'theta': theta,
            'zeta': zeta,
            'description': desc,
            'version': 1,
        })
    dlog.info('Done.')


class Flux3DAlphaTileDigger(Flux3DAlphaDigger,
                            SnapshotFieldFluxAlphaTileDigger):
    '''Tiled phi(alpha,zeta), a_para, etc. on every flux surface.'''
    __slots__ = []
    commonpattern = ['gtc/tstep', 'gtc/qmesh']

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_%03da_tile' % (self.section[1], self.ipsi)
        self.kwoptions = None

    def _get_q_psi(self):
        '''Return q at ipsi.'''
        return self.pckloader['gtc/qmesh'][self.ipsi]


class Flux3DThetaTileDigger(Flux3DThetaDigger,
                            SnapshotFieldFluxThetaTileDigger):
    '''Tiled phi(theta,zeta), a_para, etc. on every flux surface.'''
    __slots__ = []

    def _set_fignum(self, numseed=None):
        super(Flux3DThetaTileDigger, self)._set_fignum(numseed=numseed)
        self._fignum = '%s_tile' % self._fignum
        self.kwoptions = None


class Flux3DAlphaTileFFTDigger(Flux3DAlphaTileDigger,
                               SnapshotFieldFluxAlphaTileFFTDigger):
    '''Get phi (kalpha,k//) from tiled flux surface.'''
    __slot__ = []

    def _set_fignum(self, numseed=None):
        super()._set_fignum(numseed=numseed)
        self._fignum = '%s_fft' % self._fignum


class Flux3DAlphaCorrLenDigger(Flux3DAlphaTileDigger,
                               SnapshotFieldFluxAlphaCorrLenDigger):
    '''Get phi correlation(d_zeta, d_alpha) from tiled flux surface.'''
    __slot__ = []

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_%03da_corrlen' % (self.section[1], self.ipsi)
        self.kwoptions = None


class Flux3DAlphaTimeDigger(SnapshotFieldFluxTimeDigger):
    '''phi(alpha, time), a_para etc. on every flux surface at izeta=i.'''
    __slots__ = []
    nitems = '+'
    itemspattern = [
        r'^(?P<section>flux3da*)\d{5,7}/(?P<field>(?:phi|apara|fluidne|densityi'
        + r'|temperi|densitye|tempere|densityf|temperf))-(?P<ipsi>\d+)']
    _snap_time_pat = r'.*flux3da*(\d{5,7}).*'

    def _set_group(self):
        r'''Set :attr:`group`, 'flux3da(\d{5,7})' -> 'flux3d(\d{5,7})' .'''
        if 'flux3da' in self.section[0]:
            self._group = self.section[0].replace('flux3da', 'flux3d')
        else:
            self._group = self.section[0]

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_%03da_time' % (self.section[1], self.ipsi)
        self.kwoptions = None

    def _get_fieldstr(self):
        return field_tex_str[self.section[1]]


class Flux3DAlphaTimeFFTDigger(Flux3DAlphaTimeDigger,
                               SnapshotFieldFluxTimeFFTDigger):
    '''phi(ktheta,omega), a_para etc. on every flux surface.'''
    __slots__ = []

    def _set_fignum(self, numseed=None):
        super()._set_fignum(numseed=numseed)
        self._fignum = '%s_fft' % self._fignum
