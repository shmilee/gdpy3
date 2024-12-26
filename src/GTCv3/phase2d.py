#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2024 shmilee

'''
Source fortran code:

shmilee.F90, subroutine phase2d_diagnosis
```
    write(cdum,'(i5.5,".out")') (mstepall+istep)
    cdum='phase2d'//trim(cdum)
    open(iophase2d, file=cdum, status='replace')
    ! parameters: # of species and grids
    write(iophase2d,'(8i4)') nspecies, nhybrid, p2d_nfield, xgrid, ygrid, p2d_niflux, coordx, coordy
    ! diag info: number of particles near each iflux
    write(iophase2d,'(3i12)') pcount, mptmp
    write(iophase2d,'(*(i5))') p2d_ifluxes ! for p2d_niflux
     write(iophase2d,'(*(i5))') delta_fluxes
    write(iophase2d,'(*(i3))') p2d_fields ! for p2d_nfield
    ! for xymax_inv(3) of coordx, coordy
    write(iophase2d,'(f6.3,3e16.8)') xmax, xmax_inv, ymax, ymax_inv
    write(iophase2d,'(e16.8)') p2d_pdf ! data
    ! shape: p2d_pdf(p2d_nfield, xgrid, ygrid, p2d_niflux, nspecies)
```
'''

import numpy as np
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog
from .snapshot import _snap_get_time

_all_Converters = ['Phase2dConverter']
_all_Diggers = ['Phase2dDigger', 'Phase2dResonanceDigger']
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
        'coordx', 'coordy', 'pcount', 'mpcount', 'p2d_ifluxes', 'delta_fluxes',
        'p2d_fields', 'xmax', 'ymax', 'xmax_inv', 'ymax_inv',
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
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:8]))
        for key, val in zip(self._datakeys[:8], outdata[0].split()):
            sd.update({key: int(val.strip())})
        nfield = sd['p2d_nfield']
        niflux = sd['p2d_niflux']
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[8:10]))
        idx = 2 + niflux
        pcount = np.array([
            int(i.strip()) for l in outdata[1:idx] for i in l.split()])
        pcount = pcount.reshape((niflux+1, 3))
        sd['pcount'], sd['mpcount'] = pcount[:-1], pcount[-1]
        sd['p2d_ifluxes'] = [int(i.strip()) for i in outdata[idx].split()]
        sd['delta_fluxes'] = [int(i.strip()) for i in outdata[idx+1].split()]
        sd['p2d_fields'] = [int(i.strip()) for i in outdata[idx+2].split()]
        xmax = [float(i.strip()) for i in outdata[idx+3].split()]
        ymax = [float(i.strip()) for i in outdata[idx+4].split()]
        sd['xmax'], sd['xmax_inv'] = xmax[0], xmax[1:]
        sd['ymax'], sd['ymax_inv'] = ymax[0], ymax[1:]
        # 2. data
        idx = idx + 5
        shape = (nfield, sd['xgrid'], sd['ygrid'], niflux, sd['nspecies'])
        outdata = np.array([float(n.strip()) for n in outdata[idx:]])
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
    ] + [
        r'^(?P<section>phase2d\d{5,7})'
        + r'/(?P<particle>(?:ion|electron|fastion))-fullf'
    ] + [r'^(?P<s>phase2d\d{5,7})/%s$' % k for k in (
        'coordx', 'coordy', 'xmax', 'ymax', 'p2d_ifluxes',
        'pcount', 'mpcount')]
    commonpattern = ['gtc/tstep', 'gtc/sprpsi', 'gtc/a_minor']
    _particle_ins = {'ion': 1, 'electron': 2, 'fastion': 3}
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
        *norm*: int, default 0
            normalize Z value by fullf, <1: off.
            1: by sum(fullf). >1: by fullf per grid.
        '''
        istep, time = _snap_get_time(self.group, self.pckloader,
                                     pat=r'.*phase2d(\d{5,7}).*')
        data, fullf, coordx, coordy, xmax, ymax, p2d_ifluxes, \
            pcount, mpcount = self.pckloader.get_many(*self.srckeys)
        # assert data.shape == (xgrid, ygrid, p2d_niflux)
        xgrid, ygrid, p2d_niflux = data.shape
        if self.kwoptions is None:
            self.kwoptions = dict(
                sflux=dict(
                    widget='IntSlider',
                    rangee=(1, p2d_niflux, 1),
                    value=1,
                    description='select flux:'),
                norm=dict(
                    widget='IntSlider',
                    rangee=(0, 2, 1),
                    value=0,
                    description='norm:'))
        sflux = kwargs.get('sflux', 1)
        norm = kwargs.get('norm', 0)
        if not isinstance(sflux, int) or sflux < 1 or sflux > p2d_niflux:
            dlog.warning("Invalid selected flux index: %s! range: %d-%d"
                         % (sflux, 1, p2d_niflux))
            sflux = 1
        if not isinstance(norm, int):
            dlog.warning("Invalid norm: %s! Please set as int!" % norm)
            norm = 0
        acckwargs = {'sflux': sflux, 'norm': norm}
        ipsi = p2d_ifluxes[sflux-1]
        pidx = self._particle_ins[self.particle] - 1
        count, mcount = pcount[sflux-1][pidx], mpcount[pidx]
        perc = count/mcount*100
        dlog.info('%d/%d=%.1f%% of %ss are counted near ipsi=%d.'
                  % (count, mcount, perc, self.particle, ipsi))
        Z = data[:, :, sflux-1]
        if norm >= 1:  # normalize with fullf
            if norm == 1:
                f0 = np.sum(fullf[:, :, sflux-1])
            else:
                f0 = fullf[:, :, sflux-1]
                f0[f0 == 0] = 1.0
            if self.pdf == 'deltaf2':
                Z = Z/f0/f0
            else:
                Z = Z/f0
        # coordx -> row -> contourY; coordy -> col -> contourX;
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
        results = dict(X=X, Y=Y, Z=Z, title=title,
                       xlabel=xlabel, ylabel=ylabel,
                       time=time, ra=ra, coordx=coordx, coordy=coordy)
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


class Phase2dResonanceDigger(Phase2dDigger):
    '''ion, electron, fastion resonance lines in phase 2D space.'''
    __slots__ = []
    post_template = ('tmpl_z111p', 'tmpl_contourf', 'tmpl_line')

    def _set_fignum(self, numseed=None):
        self._fignum = '%s_rl_%s' % (self.section[1], self.section[2])
        self.particle = self.section[1]
        self.pdf = self.section[2]
        self.kwoptions = None

    def _dig(self, kwargs):
        '''*resfun*: string name or callable function, default 'circle'
            resonance function in phase 2D space.
            preset-functions:
            1) 'circle', Z=X^2+Y^2
            2) 'ITGomega', Z=omega/omega_d=(vperp^2/4 + vpara^2/2)/vth^2
        *reslevels*: list of float, default [1.0, 2.0]
            resonance lines in 2D space
        '''
        results, acckwargs = super(Phase2dResonanceDigger, self)._dig(kwargs)
        X, Y, Z = results['X'], results['Y'], results['Z']
        X, Y = np.meshgrid(X, Y)
        coordx, coordy = results['coordx'], results['coordy']
        # coordx -> row -> contourY; coordy -> col -> contourX;
        # 1. add contour lines and labels
        resfun = kwargs.get('resfun', 'circle')
        if resfun not in ('circle', 'ITGomega') and not callable(resfun):
            dlog.warning('Invalid resonance function: %r!' % resfun)
            resfun = 'circle'
        if resfun == 'circle':
            resZ = X**2 + Y**2
        elif resfun == 'ITGomega':
            if coordx == 1 and coordy == 2:
                resZ = X**2/4 + Y**2/2
            elif coordx == 2 and coordy == 1:
                resZ = X**2/2 + Y**2/4
            else:
                dlog.warning('Invalid coordx,y for resonance function: %s!'
                             % resfun)
                resfun, resZ = 'circle', (X**2 + Y**2)
        elif callable(resfun):
            try:
                resZ = resfun(X, Y)
            except Exception:
                dlog.warning("Cannot call resonance function!", exc_info=1)
                resfun, resZ = 'circle', (X**2 + Y**2)
            else:
                resfun = '%s.%s' % (resfun.__module__, resfun.__name__)
        else:
            resfun, resZ = 'circle', (X**2 + Y**2)
        reslevels = kwargs.get('reslevels', [1.0, 2.0])
        acckwargs.update(resfun=resfun, reslevels=reslevels)
        if 'resfun' not in self.kwoptions:
            self.kwoptions.update(
                resfun=dict(
                    widget='Dropdown',
                    options=['circle', 'ITGomega'],
                    value='circle',
                    description='resonance function:'),
                reslevels=dict(
                    widget='FloatRangeSlider',
                    rangee=(-10.0, 10.0, 0.5),
                    value=[1.0, 2.0],
                    description='resonance levels:'))
        results = results.copy()
        results.update(resfun=resfun, reslevels=reslevels, resZ=resZ)
        # 2. resZ to LineX axis
        N = sum(Z.shape)
        LineX = np.linspace(resZ.min(), resZ.max(), N)
        LineY = np.zeros(N)
        ix, iy = resZ.shape
        for i in range(ix):
            for j in range(iy):
                idx = np.nanargmin(np.abs(LineX-resZ[i, j]))
                LineY[idx] += Z[i, j]
        idx = np.where(abs(LineY) > abs(LineY).max()*1e-4)[0]
        if idx.size > 0 and idx[-1] != N-1:  # cutoff
            LineX, LineY = LineX[:idx[-1]], LineY[:idx[-1]]
        results.update(LineX=LineX, LineY=LineY)
        return results, acckwargs

    def _post_dig(self, results):
        r = results
        ax1 = {k: v for k, v in r.items() if k in [
               'X', 'Y', 'Z', 'title', 'xlabel', 'ylabel', 'aspect']}
        ax1.update(clabel_Z=r['resZ'], clabel_levels=r['reslevels'])
        return dict(zip_results=[
            ('tmpl_contourf', 121, ax1),
            ('tmpl_line', 122, dict(
                LINE=[(r['LineX'], r['LineY'])],
                aspect=None,
            )),
        ])
