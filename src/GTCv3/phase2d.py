#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2024 shmilee

'''
Source fortran code:

shmilee.F90, subroutine phase2d_diagnosis
    write(cdum,'(i5.5,".out")') (mstepall+istep)
    cdum='phase2d'//trim(cdum)
    ! parameters: # of species and grids
    write(iophase2d,101) nspecies, nhybrid, p2d_nfield, xgrid, ygrid, p2d_niflux
    write(iophase2d,101) p2d_fields ! for p2d_nfield
    write(iophase2d,101) coordx, coordy ! for xgrid, ygrid
    ! for xymax_inv(3) of coordx, coordy
    write(iophase2d,102) xmax, ymax, xmax_inv, ymax_inv
    write(iophase2d,101) p2d_ifluxes ! for p2d_niflux
    write(iophase2d,102) p2d_pdf ! data
    ! shape: p2d_pdf(p2d_nfield, xgrid, ygrid, p2d_niflux, nspecies)

'''

import numpy as np
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog
from .snapshot import _snap_get_time

_all_Converters = ['Phase2dConverter']
_all_Diggers = ['Phase2dDigger']
__all__ = _all_Converters + _all_Diggers


class Phase2dConverter(Converter):
    '''
    Phase 2D Data

    1) ion, electron, EP profiles in pdf(coordx,coordy) phase space.
       coordx,y can be: 1, vpara; 2, vperp; 3, energy; 4, lambda; 5, mu 
    2) pdf can be: 1, fullf; 2, deltaf; 3, deltaf^2; 4, angular momentum;
                   5, energy; 6, heat; 7, ExB drift; 8, particle flux;
                   9, momentum flux; 10, energy flux; 11, heat flux;
                   12, radial drift; 13, diffusion, and 14 energy loss
    3) data 5d array is pdf2d(p2d_nfield, xgrid, ygrid, p2d_niflux, nspecies)
       pdf2d(1, ...) is always for fullf.
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = [r'^(?P<section>phase2d\d{5,7})\.out$',
                    r'.*/(?P<section>phase2d\d{5,7})\.out$']
    _datakeys = (
        # 1. parameters
        'nspecies', 'nhybrid', 'p2d_nfield', 'xgrid', 'ygrid', 'p2d_niflux',
        'p2d_fields', 'coordx', 'coordy',
        'xmax', 'ymax', 'xmax_inv', 'ymax_inv', 'p2d_ifluxes',
        # 2. Data pdf2d(p2d_nfield, xgrid, ygrid, p2d_niflux, nspecies)
        #    split to pdf(xgrid, ygrid, p2d_niflux)
        r'(?:ion|electron|fastion)-(?:fullf|deltaf|deltaf2|momentum)',
        r'(?:ion|electron|fastion)-(?:energy|heat|vdr)',
        r'(?:ion|electron|fastion)-(?:particle|momentum|energy|heat)-flux',
        r'(?:ion|electron|fastion)-(?:r-drift|diffusion|Eloss)',
    )
    _pdf_index = {1: 'fullf', 2: 'deltaf', 3: 'deltaf2', 4: 'momentum',
                  5: 'energy', 6: 'heat', 7: 'vdr', 8: 'particle-flux',
                  9: 'momentum-flux', 10: 'energy-flux', 11: 'heat-flux',
                  12: 'r-drift', 13: 'diffusion', 14: 'Eloss'}

    def _convert(self):
        '''Read 'phase2d%05d.out' % istep.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        # 1. parameters
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:6]))
        for i, key in enumerate(self._datakeys[:6]):
            sd.update({key: int(outdata[i].strip())})
        nfield = sd['p2d_nfield']
        niflux = sd['p2d_niflux']
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[6:14]))
        sd['p2d_fields'] = [int(l.strip()) for l in outdata[6:6+nfield]]
        idx0 = 6 + nfield
        sd['coordx'] = int(outdata[idx0].strip())
        sd['coordy'] = int(outdata[idx0+1].strip())
        sd['xmax'] = float(outdata[idx0+2].strip())
        sd['ymax'] = float(outdata[idx0+3].strip())
        sd['xmax_inv'] = [float(l.strip()) for l in outdata[idx0+4:idx0+7]]
        sd['ymax_inv'] = [float(l.strip()) for l in outdata[idx0+7:idx0+10]]
        idx1 = idx0 + 10
        idx2 = idx1 + niflux
        sd['p2d_ifluxes'] = [int(l.strip()) for l in outdata[idx1:idx2]]
        # 2. data
        shape = (nfield, sd['xgrid'], sd['ygrid'], niflux, sd['nspecies'])
        outdata = np.array([float(n.strip()) for n in outdata[idx2:]])
        outdata = outdata.reshape(shape, order='F')
        particles = [('ion', 0)]
        if sd['nspecies'] == 2:
            if sd['nhybrid'] > 0:
                particles.append(('electron', 1))
            else:
                particles.append(('fastion', 1))
        elif sd['nspecies'] == 3:
            particles.append(('electron', 1))
            particles.append(('fastion', 2))
        for part, idx in particles:
            for jdx, ifield in enumerate(sd['p2d_fields']):
                key = '%s-%s' % (part, self._pdf_index[ifield])
                clog.debug("Filling datakey: %s ..." % key)
                sd[key] = outdata[jdx, :, :, :, idx]
        for k in ['nspecies', 'nhybrid']:
            _ = sd.pop(k)
        return sd


class Phase2dDigger(Digger):
    '''ion, electron, fastion profiles in phase 2D space.'''
    __slots__ = ['particle', 'pdf']
    nitems = '+'
    itemspattern = [
        r'^(?P<section>phase2d\d{5,7})'
        + r'/(?P<particle>(?:ion|electron|fastion))-'
        + r'(?P<pdf>(?:fullf|deltaf|deltaf2|momentum|energy|heat|vdr'
        + r'|particle-flux|momentum-flux|energy-flux|heat-flux'
        + r'|r-drift|diffusion|Eloss))$'
    ] + [r'^(?P<s>phase2d\d{5,7})/%s$' % k for k in (
        'coordx', 'coordy', 'xmax', 'ymax', 'p2d_ifluxes')]
    commonpattern = ['gtc/tstep', 'gtc/sprpsi', 'gtc/a_minor']
    _pdf_tex = {
        'fullf': 'full f', 'deltaf': r'$\delta f$',
        'deltaf2': r'$\delta f^2$', 'momentum': 'angular momentum',
        'energy': 'E', 'heat': 'heat', 'vdr': 'ExB drift',
        'particle-flux': 'particle flux', 'momentum-flux': 'momentum flux',
        'energy-flux': 'energy flux', 'heat-flux': 'heat flux',
        'r-drift': r'$\langle \Delta r \rangle$',
        'diffusion': r'$\langle \Delta r^2 \rangle$',
        'Eloss': r'$-\mathrm{d}E/\mathrm{d}t$',
    }
    post_template = 'tmpl_contourf'

    def _set_fignum(self, numseed=None):
        self._fignum = '%s_%s' % (self.section[1], self.section[2])
        self.particle = self.section[1]
        self.pdf = self.section[2]
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *sflux*: int, default 1
            select one flux from range(1, p2d_niflux+1)
        '''
        istep, time = _snap_get_time(self.group, self.pckloader,
                                     pat=r'.*phase2d(\d{5,7}).*')
        data, coordx, coordy, xmax, ymax, p2d_ifluxes = \
            self.pckloader.get_many(*self.srckeys)
        # assert data.shape == (xgrid, ygrid, p2d_niflux)
        xgrid, ygrid, p2d_niflux = data.shape
        if self.kwoptions is None:
            self.kwoptions = dict(
                sflux=dict(
                    widget='IntSlider',
                    rangee=(1, p2d_niflux, 1),
                    value=1,
                    description='select flux:'))
        sflux = kwargs.get('sflux', 1)
        if sflux < 1 or sflux > p2d_niflux:
            dlog.warning("Invalid selected flux index: %d! range: %d-%d"
                         % (sflux, 1, p2d_niflux))
            sflux = 1
        acckwargs = {'sflux': sflux}
        ipsi = p2d_ifluxes[sflux-1]
        Z = data[:, :, sflux-1]
        # xgrid -> row -> contourY; ygrid -> col -> contourX;
        X, xlabel = self._get_X_xlabel(coordy, ygrid, ymax)
        Y, ylabel = self._get_X_xlabel(coordx, xgrid, xmax)
        sec = self.section
        title = r'%s %s, t=%g$R_0/c_s$, ipsi=%d' % (
                sec[1], self._pdf_tex[sec[2]], time, ipsi)
        try:
            # rpsi [0, mpsi]
            rpsi, a = self.pckloader.get_many(*self.common[-2:])
            ra = np.round(rpsi[ipsi]/a, decimals=3)
            title += ', r=%ga' % ra
        except Exception:
            pass
        results = dict(X=X, Y=Y, Z=Z, title=title, time=time, ra=ra,
                       xlabel=xlabel, ylabel=ylabel,)
        if coordx in (1, 2) and coordy in (1, 2):
            results['aspect'] = 'equal'
        return results, acckwargs

    def _get_X_xlabel(self, coordx, xgrid, xmax):
        if coordx == 1:
            X = np.linspace(-xmax, xmax, xgrid)
            xlabel = r'$v_{\parallel}(v_{th})$'
        elif coordx == 2:
            X = np.linspace(0, xmax, xgrid)
            xlabel = r'$v_{\perp}(v_{th})$'
        elif coordx == 3 or coordx == 4:
            X = np.linspace(0, xmax, xgrid)
            xlabel = r'$E(T_{e0})$' if coordx == 3 else r'$\lambda$'
        elif coordx == 5:
            X = np.linspace(0, xmax, xgrid)
            xlabel = r'$\mu$'
        return X, xlabel

    def _post_dig(self, results):
        d = {k: v for k, v in results.items() if k in [
            'X', 'Y', 'Z', 'title', 'xlabel', 'ylabel', 'aspect']}
        return d
