#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2024 shmilee

'''
Source fortran code:

shmilee.F90, subroutine phase2d_diagnosis

* old format. No `format=`
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
    ! 5D shape: p2d_pdf(p2d_nfield, xgrid, ygrid, p2d_niflux, nspecies)
```

* second pdf(x,y) support, `format=2`
```
    write(cdum,'(i5.5,".out")') (mstepall+istep)
    cdum='phase2d'//trim(cdum)
    open(iophase2d, file=cdum, status='replace')
    write(iophase2d,*) 'format=2'
    ! parameters: # of species and grids
    write(iophase2d,'(7i5)') nspecies, nhybrid, p2d_nfield, xgrid, ygrid, p2d_ncoord, p2d_niflux
    ! diag info: number of particles near each iflux
    write(iophase2d,'(3i12)') pcount, mptmp
    write(iophase2d,'(*(i5))') p2d_fields ! for p2d_nfield
    write(iophase2d,'(4i5)') coordxy ! for coordx, coordy
    write(iophase2d,'(*(i5))') p2d_ifluxes ! for p2d_niflux
     write(iophase2d,'(*(i5))') delta_fluxes
    ! for xymax_inv(3) of coordx, coordy
    write(iophase2d,'(5f6.3)') xymax
    write(iophase2d,'(5e16.8)') xymax_inv
    write(iophase2d,'(e16.8)') p2d_pdf ! data
    ! 6D shape: p2d_pdf(p2d_nfield, xgrid, ygrid, p2d_ncoord, p2d_niflux, nspecies)
```

* xymin support, `format=3`
```
-   ! for xymax_inv(3) of coordx, coordy
-   write(iophase2d,'(5f6.3)') xymax
-   write(iophase2d,'(5e16.8)') xymax_inv
+   ! for xymax(5), xymin(5), xyrange_inv(5,3), xymin(5,3) of coordx, coordy
+   write(iophase2d,'(5f6.3)') xymax_norm, xymin_norm
+   write(iophase2d,'(5e16.8)') xyrange_inv, xymin
```
'''

import numpy as np
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog
from .snapshot import _snap_get_time

_all_Converters = ['Phase2dConverter']
_all_Diggers = ['Phase2dDigger', 'Phase2dResonanceDigger', 'Phase2dTimeDigger']
__all__ = _all_Converters + _all_Diggers


class Phase2dConverter(Converter):
    '''
    Phase 2D Data

    1) ion, electron, EP profiles in pdf(coordx,coordy) phase space.
       coordx,y can be: 1, vpara; 2, vperp; 3, energy; 4, lambda; 5, mu
    2) pdf can be: 1, fullf; 2, deltaf; 3, deltaf^2; 4, angular momentum;
                   5, energy; 6, heat; 7, ExB drift; 8, particle flux;
                   9, momentum flux; 10, energy flux; 11, heat flux;
                   12, radial drift; 13, diffusion; 14, energy loss; 15, fullf+deltaf
    3) data 6d array is pdf2d(p2d_nfield, xgrid, ygrid, p2d_ncoord, p2d_niflux, nspecies)
       pdf2d(1, ...) is always for fullf.
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = [r'^(?P<section>phase2d\d{5,7})\.out$',
                    r'.*/(?P<section>phase2d\d{5,7})\.out$']
    _datakeys = (
        # 1. parameters
        'nspecies', 'nhybrid', 'p2d_nfield',
        'xgrid', 'ygrid', 'p2d_ncoord', 'p2d_niflux',
        'pcount', 'mpcount',  # 7,8
        'p2d_fields', 'coordxy', 'p2d_ifluxes', 'delta_fluxes',
        'xymax', 'xymin',  # 13,14 for xymax_norm, xymin_norm
        # 15,16,17 for xymax_inv, xyrange_inv, xymin: useless
        'xymax_inv', 'xyrange_inv', 'xymin_org',
        # 2. Data pdf2d(p2d_nfield, xgrid, ygrid, p2d_ncoord, p2d_niflux, nspecies)
        #    split to pdf(xgrid, ygrid, p2d_ncoord, p2d_niflux)
        r'(?:ion|electron|fastion)-(?:fullf|deltaf|deltaf2|momentum)',
        r'(?:ion|electron|fastion)-(?:energy|heat|vdr)',
        r'(?:ion|electron|fastion)-(?:particle|momentum|energy|heat)-flux',
        r'(?:ion|electron|fastion)-(?:r-drift|diffusion|Eloss|full+delf)',
    )
    _pdf_index = {1: 'fullf', 2: 'deltaf', 3: 'deltaf2', 4: 'momentum',
                  5: 'energy', 6: 'heat', 7: 'vdr', 8: 'particle-flux',
                  9: 'momentum-flux', 10: 'energy-flux', 11: 'heat-flux',
                  12: 'r-drift', 13: 'diffusion', 14: 'Eloss', 15: 'full+delf'}

    def _convert(self):
        '''Read 'phase2d%05d.out' % istep.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()
        if 'format=' not in outdata[0]:
            return self._read_old_format(outdata)
        elif 'format=2' in outdata[0]:
            fmt = 2
        elif 'format=3' in outdata[0]:
            fmt = 3
        else:
            raise ValueError('Wrong phase2d format: ' + outdata[0])
        sd = {'format': fmt}
        outdata = outdata[1:]

        # 1. parameters
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:7]))
        for key, val in zip(self._datakeys[:7], outdata[0].split()):
            sd.update({key: int(val.strip())})
        nfield = sd['p2d_nfield']
        ncoord = sd['p2d_ncoord']
        niflux = sd['p2d_niflux']
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[7:9]))
        idx = 2 + niflux
        pcount = np.array([
            int(i.strip()) for l in outdata[1:idx] for i in l.split()])
        pcount = pcount.reshape((niflux+1, 3))
        sd['pcount'], sd['mpcount'] = pcount[:-1], pcount[-1]
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[9:13]))
        sd['p2d_fields'] = [int(i.strip()) for i in outdata[idx].split()]
        assert len(sd['p2d_fields']) == nfield
        sd['coordxy'] = [int(i.strip()) for i in outdata[idx+1].split()]
        assert len(sd['coordxy']) == 4
        sd['p2d_ifluxes'] = [int(i.strip()) for i in outdata[idx+2].split()]
        assert len(sd['p2d_ifluxes']) == niflux
        sd['delta_fluxes'] = [int(i.strip()) for i in outdata[idx+3].split()]
        assert len(sd['delta_fluxes']) == niflux
        idx = idx + 4
        if fmt == 2:
            clog.debug("Filling datakeys: %s ..." % 'xymax, xymax_inv')
            sd['xymax'] = [float(i.strip()) for i in outdata[idx].split()]
            assert len(sd['xymax']) == 5
            sd['xymax_inv'] = np.array([
                [float(i.strip()) for i in outdata[idx+1].split()],
                [float(i.strip()) for i in outdata[idx+2].split()],
                [float(i.strip()) for i in outdata[idx+3].split()],
            ]).T
            assert sd['xymax_inv'].shape == (5, 3)
            idx = idx + 4  # xymax ... 4 lines
        elif fmt == 3:
            clog.debug("Filling datakeys: %s ..." % 'xymax, xymin, xyrange')
            sd['xymax'] = [float(i.strip()) for i in outdata[idx].split()]
            sd['xymin'] = [float(i.strip()) for i in outdata[idx+1].split()]
            assert len(sd['xymax']) == len(sd['xymin']) == 5
            sd['xyrange_inv'] = np.array([
                [float(i.strip()) for i in outdata[idx+2].split()],
                [float(i.strip()) for i in outdata[idx+3].split()],
                [float(i.strip()) for i in outdata[idx+4].split()],
            ]).T
            sd['xymin_org'] = np.array([
                [float(i.strip()) for i in outdata[idx+5].split()],
                [float(i.strip()) for i in outdata[idx+6].split()],
                [float(i.strip()) for i in outdata[idx+7].split()],
            ]).T
            assert sd['xymin_org'].shape == (5, 3)
            idx = idx + 8  # xymax ... 8 lines

        # 2. data
        shape = (nfield, sd['xgrid'], sd['ygrid'], ncoord, niflux,
                 sd['nspecies'])
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
                sd[key] = outdata[jdx, :, :, :, :, idx]
        for k in ['nspecies', 'nhybrid']:
            _ = sd.pop(k)
        return sd

    _fmt1_keys = (
        # 1. old parameters
        'nspecies', 'nhybrid', 'p2d_nfield', 'xgrid', 'ygrid', 'p2d_niflux',
        'coordx', 'coordy', 'pcount', 'mpcount', 'p2d_ifluxes', 'delta_fluxes',
        'p2d_fields', 'xmax', 'xmax_inv', 'ymax', 'ymax_inv',
        # 2. Data pdf2d(p2d_nfield, xgrid, ygrid, p2d_niflux, nspecies)
        #    split to pdf(xgrid, ygrid, p2d_niflux)
    )

    def _read_old_format(self, outdata):
        sd = {'format': 1, 'p2d_ncoord': 1}
        # 1. parameters
        clog.debug("Filling datakeys: %s ..." % str(self._fmt1_keys[:8]))
        for key, val in zip(self._fmt1_keys[:8], outdata[0].split()):
            sd.update({key: int(val.strip())})
        nfield = sd['p2d_nfield']
        niflux = sd['p2d_niflux']
        sd['coordxy'] = [sd['coordx'], sd['coordy'], -1, -1]
        clog.debug("Filling datakeys: %s ..." % str(self._fmt1_keys[8:10]))
        idx = 2 + niflux
        pcount = np.array([
            int(i.strip()) for l in outdata[1:idx] for i in l.split()])
        pcount = pcount.reshape((niflux+1, 3))
        sd['pcount'], sd['mpcount'] = pcount[:-1], pcount[-1]
        clog.debug("Filling datakeys: %s ..." % str(self._fmt1_keys[10:]))
        sd['p2d_ifluxes'] = [int(i.strip()) for i in outdata[idx].split()]
        sd['delta_fluxes'] = [int(i.strip()) for i in outdata[idx+1].split()]
        sd['p2d_fields'] = [int(i.strip()) for i in outdata[idx+2].split()]
        xmax = [float(i.strip()) for i in outdata[idx+3].split()]
        ymax = [float(i.strip()) for i in outdata[idx+4].split()]
        assert len(xmax) == len(ymax) == 4
        sd['xymax'], sd['xymax_inv'] = [-999]*5, [[-999]*3]*5  # -999 unset
        sd['xymax'][sd['coordx']-1] = xmax[0]
        sd['xymax'][sd['coordy']-1] = ymax[0]
        sd['xymax_inv'][sd['coordx']-1] = xmax[1:]
        sd['xymax_inv'][sd['coordy']-1] = ymax[1:]
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
                tmparr = outdata[jdx, :, :, :, idx]
                shape = tmparr.shape  # (xgrid, ygrid, p2d_niflux)
                sd[key] = np.zeros((*shape[:2], 1, shape[-1]))
                sd[key][:, :, 0, :] = tmparr
        for k in ['nspecies', 'nhybrid', 'coordx', 'coordy']:
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
        + r'|r-drift|diffusion|Eloss|full\+delf))$'
    ] + [
        r'^(?P<section>phase2d\d{5,7})'
        + r'/(?P<particle>(?:ion|electron|fastion))-fullf'
    ] + [r'^(?P<s>phase2d\d{5,7})/%s$' % k for k in (
        'format', 'coordxy', 'xymax', 'p2d_ifluxes',
        'pcount', 'mpcount')]
    commonpattern = ['gtc/tstep', 'gtc/sprpsi', 'gtc/a_minor']
    _particle_ins = {'ion': 1, 'electron': 2, 'fastion': 3}
    _coord_rawtex = {
        1: r'v_{\parallel}', 2: r'v_{\perp}',
        3: r'E', 4: r'\lambda', 5: r'\mu',
    }
    _coord_label = {
        1: r'$v_{\parallel}(v_{th})$', 2: r'$v_{\perp}(v_{th})$',
        3: r'$E(T_{e0})$', 4: r'$\lambda$', 5: r'$\mu$',
    }
    _pdf_tex = {
        'fullf': r'$f_0$', 'deltaf': r'$\delta f$',
        'deltaf2': r'$\delta f^2$', 'momentum': 'angular momentum',
        'energy': 'E', 'heat': 'heat', 'vdr': 'ExB drift',
        'particle-flux': 'particle flux', 'momentum-flux': 'momentum flux',
        'energy-flux': 'energy flux', 'heat-flux': 'heat flux',
        'r-drift': r'$\langle \Delta r \rangle$',
        'diffusion': r'$\langle \Delta r^2 \rangle$',
        'Eloss': r'$\mathrm{d}E$',
        'full+delf': r'$f_0 + \delta f$',
    }
    post_template = 'tmpl_contourf'

    def _set_fignum(self, numseed=None):
        self._fignum = '%s_%s' % (self.section[1], self.section[2])
        self.particle = self.section[1]
        self.pdf = self.section[2]
        self.kwoptions = None

    def _get_selected_index(self, kwargs, key, default, vmin, vmax, desc):
        idx = kwargs.get(key, default)
        if not isinstance(idx, int) or idx < vmin or idx > vmax:
            dlog.warning("Invalid selected %s index: %s! range: %d-%d"
                         % (desc, idx, vmin, vmax))
            idx = default
        if self.kwoptions is None:
            self.kwoptions = dict()
        if key not in self.kwoptions:
            self.kwoptions[key] = dict(widget='IntSlider',
                                       rangee=(vmin, vmax, 1),
                                       value=default,
                                       description='select %s:' % desc)
        return idx

    def _get_norm(self, kwargs):
        default = 0 if self.pdf in ('r-drift', 'diffusion', 'Eloss') else 1
        norm = kwargs.get('norm', default)
        if not isinstance(norm, int):
            dlog.warning("Invalid norm: %s! Please set as int!" % norm)
            norm = default
        if 'norm' not in self.kwoptions:
            self.kwoptions['norm'] = dict(widget='IntSlider',
                                          rangee=(-2, 2, 1),
                                          value=default,
                                          description='norm:')
        return norm

    def _normalize_Z(self, Z, fullf, norm):
        if norm != 0:  # >0: normalize with fullf[:,:]; or <0: times fullf
            if abs(norm) == 1:
                f0 = np.sum(fullf)
            else:
                f0 = fullf[:, :]
                if norm > 0:
                    f0[f0 == 0] = 1.0
            if self.pdf == 'deltaf2':
                Z = Z/f0/f0 if norm > 0 else Z*f0*f0
            else:
                Z = Z/f0 if norm > 0 else Z*f0
        return Z

    def _get_X_Y_labels(self, scoord, fmt, coordxy, xymax, xygrid, kgroup):
        if scoord == 1:
            coordx, coordy = coordxy[:2]
        elif scoord == 2:
            coordx, coordy = coordxy[2:]
        else:
            raise ValueError('Invalid coordinate index!')
        if fmt == 3:
            try:
                xymin = self.pckloader['%s/xymin' % kgroup]
            except Exception:
                dlog.error('Cannot get key: phase2d/xymin!', exc_info=1)
                xymin = [-xymax[0], 0.0, 0.0, 0.0, 0.0]
        else:
            xymin = [-xymax[0], 0.0, 0.0, 0.0, 0.0]
        xgrid, ygrid = xygrid
        # coordx -> row -> contourY; coordy -> col -> contourX;
        X = np.linspace(xymin[coordy-1], xymax[coordy-1], ygrid)
        Y = np.linspace(xymin[coordx-1], xymax[coordx-1], xgrid)
        xlabel, ylabel = self._coord_label[coordy], self._coord_label[coordx]
        return coordx, coordy, X, Y, xlabel, ylabel

    def _get_title_ra(self, t, ipsi):
        sec = self.section
        title = r'%s %s, t=%g$R_0/c_s$, ipsi=%d' % (
            sec[1], self._pdf_tex[sec[2]], t, ipsi)
        try:  # rpsi [0, mpsi]
            rpsi, a = self.pckloader.get_many(*self.common[-2:])
            ra = np.round(rpsi[ipsi]/a, decimals=3)
        except Exception:
            dlog.warning("Cannot get r/a!", exc_info=1)
            ra = None
        else:
            title += ', r=%ga' % ra
        return title, ra

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *sflux*: int, default 1
            select one flux from range(1, p2d_niflux+1)
        *scoord*: int, default 1
            select the coordinates, from range(1, p2d_ncoord+1)
        *norm*: int, default 1 or 0 for r-drift, diffusion, Eloss
            normalize Z value by fullf.
            0: off; 1: by sum(fullf); >1: by fullf per grid.
            -1: times sum(fullf); <-1: times fullf per grid.
        '''
        istep, time = _snap_get_time(self.group, self.pckloader,
                                     pat=r'.*phase2d(\d{5,7}).*')
        data, fullf, fmt, coordxy, xymax, p2d_ifluxes, \
            pcount, mpcount = self.pckloader.get_many(*self.srckeys)
        # assert data.shape == (xgrid, ygrid, p2d_ncoord, p2d_niflux)
        xgrid, ygrid, p2d_ncoord, p2d_niflux = data.shape
        get_index = self._get_selected_index
        sflux = get_index(kwargs, 'sflux', 1, 1, p2d_niflux, 'flux')
        scoord = get_index(kwargs, 'scoord', 1, 1, p2d_ncoord, 'coordinate')
        norm = self._get_norm(kwargs)
        acckwargs = {'sflux': sflux, 'scoord': scoord, 'norm': norm}
        ipsi = p2d_ifluxes[sflux-1]
        pidx = self._particle_ins[self.particle] - 1
        count, mcount = pcount[sflux-1][pidx], mpcount[pidx]
        if mcount > 0:
            perc = count/mcount*100
        else:
            perc = -1
        dlog.info('%d/%d=%.1f%% of %ss are counted near ipsi=%d.'
                  % (count, mcount, perc, self.particle, ipsi))
        Z = data[:, :, scoord-1, sflux-1]
        fullf = fullf[:, :, scoord-1, sflux-1]
        Z = self._normalize_Z(Z, fullf, norm)
        # coordx -> row -> contourY; coordy -> col -> contourX;
        coordx, coordy, X, Y, xlabel, ylabel = self._get_X_Y_labels(
            scoord, fmt, coordxy, xymax, (xgrid, ygrid), self.group)
        title, ra = self._get_title_ra(time, ipsi)
        results = dict(X=X, Y=Y, Z=Z, title=title,
                       xlabel=xlabel, ylabel=ylabel,
                       time=time, ra=ra, coordx=coordx, coordy=coordy)
        if coordx in (1, 2) and coordy in (1, 2):
            results['aspect'] = 'equal'
        return results, acckwargs

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
        '''*resfun*: string name or callable function, default 'Circle'
            resonance function in phase 2D space.
            preset-functions:
            1) 'Circle', Z=X^2/2+Y^2/2
            2) 'Xline', Z=X
            3) 'Yline', Z=Y
            4) 'ITGomegad', omega ~ <omega_d> = 2*epsilon_n*omega_*i,
                Z=omega/epsilon_n/omega_*i=(vperp^2/2 + vpara^2)/vth^2
                with vth=sqrt(Ti/mi)
        *shiftvpara*: float, default 0
            add kpara-vpara effect for preset resfun 'ITGomegad'
        *reslevels*: list of float, default [1.0, 2.0]
            resonance lines in 2D space, like Z=1.0
        '''
        results, acckwargs = super(Phase2dResonanceDigger, self)._dig(kwargs)
        oX, oY, Z = results['X'], results['Y'], results['Z']
        X, Y = np.meshgrid(oX, oY)
        coordx, coordy = results['coordx'], results['coordy']
        # coordx -> row -> contourY; coordy -> col -> contourX;
        # 1. add contour lines and labels
        resfun = kwargs.get('resfun', 'Circle')
        shiftvpara = kwargs.get('shiftvpara', 0.0)
        xtex, ytex = self._coord_rawtex[coordy], self._coord_rawtex[coordx]
        if resfun == 'Circle':
            resZ = (X**2 + Y**2)/2
        elif resfun == 'Xline':
            resZ, LineXlabel = X, r'$%s$' % xtex
        elif resfun == 'Yline':
            resZ, LineXlabel = Y, r'$%s$' % ytex
        elif resfun == 'ITGomegad':
            if shiftvpara == 0:
                LineXlabel = r'$v_{\parallel}^2+v_{\perp}^2/2$'
            else:
                LineXlabel = (r'$v_{\parallel}^2+v_{\perp}^2/2'
                              + r'+%.2f v_{\parallel}$' % shiftvpara)
            if coordx == 1 and coordy == 2:  # coordy <-> X
                resZ = X**2/2 + Y**2 + shiftvpara*Y
            elif coordx == 2 and coordy == 1:
                resZ = X**2 + Y**2/2 + shiftvpara*X
            else:
                dlog.warning('Invalid coordx,y for resonance function: %s!'
                             % resfun)
                resfun, resZ = 'Circle', (X**2 + Y**2)/2
        elif callable(resfun):
            try:
                resZ = resfun(X, Y)
            except Exception:
                dlog.warning("Cannot call resonance function!", exc_info=1)
                resfun, resZ = 'Circle', (X**2 + Y**2)/2
            else:
                resfun = '%s.%s' % (resfun.__module__, resfun.__name__)
                LineXlabel = r'%s$(%s,%s)$' % (resfun, xtex, ytex)
        else:
            dlog.warning('Invalid resonance function: %r!' % resfun)
            resfun, resZ = 'Circle', (X**2 + Y**2)/2
        if resfun == 'Circle':  # fix Circle LineXlabel
            if (coordx, coordy) in [(1, 2), (2, 1)]:
                LineXlabel = r'$E=(%s^2+%s^2)/2$' % (xtex, ytex)
            else:
                LineXlabel = r'$(%s^2+%s^2)/2$' % (xtex, ytex)
        reslevels = kwargs.get('reslevels', [1.0, 2.0])
        acckwargs.update(
            resfun=resfun, shiftvpara=shiftvpara, reslevels=reslevels)
        if 'resfun' not in self.kwoptions:
            self.kwoptions.update(
                resfun=dict(
                    widget='Dropdown',
                    options=['Circle', 'Xline', 'Yline', 'ITGomegad'],
                    value='Circle',
                    description='resonance function:'),
                shiftvpara=dict(
                    widget='FloatSlider',
                    rangee=(-2.0, 2.0, 0.1),
                    value=0.0,
                    description='shift vpara:'),
                reslevels=dict(
                    widget='FloatRangeSlider',
                    rangee=(-6.0, 6.0, 0.2),
                    value=[1.0, 2.0],
                    description='resonance levels:'))
        results = results.copy()
        results.update(resfun=resfun, shiftvpara=shiftvpara,
                       reslevels=reslevels, resZ=resZ)
        # 2. resZ to LineX axis
        if resfun == 'Xline':
            LineX, LineY = oX, Z.sum(axis=0)
            xlim = None
        elif resfun == 'Yline':
            LineX, LineY = oY, Z.sum(axis=1)
            xlim = None
        else:
            N = sum(Z.shape)
            LineX = np.linspace(resZ.min(), resZ.max(), N)
            dx = (resZ.max() - resZ.min())/(N-1)
            LineY = np.zeros(N)
            ix, iy = resZ.shape
            for i in range(ix):
                for j in range(iy):
                    # idx = np.nanargmin(np.abs(LineX-resZ[i, j]))
                    # LineY[idx] += Z[i, j]
                    idx = np.where(LineX < resZ[i, j])[0]
                    if idx.size == 0:
                        LineY[0] += Z[i, j]
                    elif idx.size == N:
                        LineY[N-1] += Z[i, j]
                    else:
                        idx = idx[-1]
                        dp = (resZ[i, j] - LineX[idx])/dx
                        LineY[idx] += (1.0-dp)*Z[i, j]
                        LineY[idx+1] += dp*Z[i, j]
            idx = np.where(abs(LineY) > abs(LineY).max()*1e-4)[0]
            xlim = sorted([LineX[0], LineX[idx[-1]]])
            # if idx.size > 0 and idx[-1] != N-1:  # cutoff
            #    LineX, LineY = LineX[:idx[-1]], LineY[:idx[-1]]
        results.update(LineX=LineX, LineY=LineY,
                       LineXlabel=LineXlabel, LineXlim=xlim)
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
                xlabel=r['LineXlabel'], aspect=None,
                xlim=r['LineXlim'],
            )),
        ])


class Phase2dTimeDigger(Phase2dDigger):
    '''ion, electron, fastion history per phase 2D space grid.'''
    __slots__ = []
    nitems = '+'
    itemspattern = [
        r'^(?P<section>phase2d)\d{5,7}'
        + r'/(?P<particle>(?:ion|electron|fastion))-'
        + r'(?P<pdf>(?:fullf|deltaf|deltaf2|momentum|energy|heat|vdr'
        + r'|particle-flux|momentum-flux|energy-flux|heat-flux'
        + r'|r-drift|diffusion|Eloss|full\+delf))$'
    ] + [
        r'^(?P<section>phase2d)\d{5,7}'
        + r'/(?P<particle>(?:ion|electron|fastion))-fullf'
    ] + [r'^(?P<s>phase2d)\d{5,7}/%s$' % k for k in (
        'format', 'coordxy', 'xymax', 'p2d_ifluxes')]
    post_template = ('tmpl_z111p', 'tmpl_contourf', 'tmpl_line')

    def _set_fignum(self, numseed=None):
        self._fignum = '%s_%s' % (self.section[1], self.section[2])
        self.particle = self.section[1]
        self.pdf = self.section[2]
        self.kwoptions = None

    def _dig(self, kwargs):
        '''*sgridx1*, *sgridx2*: int, default xgrid//3, xgrid//2
            select phase2d grid x-index
        *sgridy1*, *sgridy2*: int, default ygrid//3, ygrid//2
            select phase2d grid y-index
        *stime*: int, default len(time)//2
            select a time index for phase2d contourf
        '''
        N = len(self.srckeys)
        assert N % 6 == 0
        N = N//6
        datakeys = self.srckeys[:N]
        fullfkeys = self.srckeys[N:2*N]
        time = np.array([_snap_get_time(
            k.split('/')[0], self.pckloader, pat=r'.*phase2d(\d{5,7}).*')[1]
            for k in datakeys])
        data0 = self.pckloader.get(datakeys[0])
        fmt, coordxy, xymax, p2d_ifluxes = self.pckloader.get_many(*[
            '%s/%s' % (datakeys[0].split('/')[0], k)
            for k in ('format', 'coordxy', 'xymax', 'p2d_ifluxes')])
        # assert data0.shape == (xgrid, ygrid, p2d_ncoord, p2d_niflux)
        xgrid, ygrid, p2d_ncoord, p2d_niflux = data0.shape
        get_index = self._get_selected_index
        sflux = get_index(kwargs, 'sflux', 1, 1, p2d_niflux, 'flux')
        scoord = get_index(kwargs, 'scoord', 1, 1, p2d_ncoord, 'coordinate')
        norm = self._get_norm(kwargs)
        # x,row -> contourY; y,col -> contourX;
        sgridx1 = get_index(kwargs, 'sgridx1', ygrid//3, 0, ygrid-1, 'gridX1')
        sgridx2 = get_index(kwargs, 'sgridx2', ygrid//2, 0, ygrid-1, 'gridX2')
        sgridy1 = get_index(kwargs, 'sgridy1', xgrid//3, 0, xgrid-1, 'gridY1')
        sgridy2 = get_index(kwargs, 'sgridy2', xgrid//2, 0, xgrid-1, 'gridY2')
        stime = get_index(kwargs, 'stime', N//2, 0, N-1, 'time')
        acckwargs = {'sflux': sflux, 'scoord': scoord, 'norm': norm,
                     'sgridx1': sgridx1, 'sgridx2': sgridx2,
                     'sgridy1': sgridy1, 'sgridy2': sgridy2, 'stime': stime}
        ipsi = p2d_ifluxes[sflux-1]
        pidx = self._particle_ins[self.particle] - 1
        # coordx -> row -> contourY; coordy -> col -> contourX;
        coordx, coordy, X, Y, xlabel, ylabel = self._get_X_Y_labels(
            scoord, fmt, coordxy, xymax, (xgrid, ygrid),
            datakeys[0].split('/')[0])
        title, ra = self._get_title_ra(time[stime], ipsi)
        allZ = []
        Zhis11, Zhis12, Zhis22, Zhis21, Zhisall = [], [], [], [], []
        _idxlog = max(1, N // 7)
        for idx, dkey, fkey in zip(range(1, N+1), datakeys, fullfkeys):
            if idx % _idxlog == 0 or idx == N:
                dlog.info('Collecting [%d/%d] %s' % (idx, N, dkey))
            data, fullf = self.pckloader.get_many(dkey, fkey)
            Z = data[:, :, scoord-1, sflux-1]
            fullf = fullf[:, :, scoord-1, sflux-1]
            Z = self._normalize_Z(Z, fullf, norm)
            allZ.append(Z)
            # x,row <-> sgridy;
            Zhis11.append(Z[sgridy1, sgridx1])
            Zhis12.append(Z[sgridy1, sgridx2])
            Zhis22.append(Z[sgridy2, sgridx2])
            Zhis21.append(Z[sgridy2, sgridx1])
            zall = np.sum(Z*fullf)/np.sum(fullf)
            Zhisall.append(zall)
        # selected grid points
        sX = X[[sgridx1, sgridx2, sgridx2, sgridx1]]
        sY = Y[[sgridy1, sgridy1, sgridy2, sgridy2]]
        results = dict(X=X, Y=Y, Z=allZ[stime], allZ=allZ, title=title,
                       xlabel=xlabel, ylabel=ylabel,
                       Zhis11=np.array(Zhis11), Zhis12=np.array(Zhis12),
                       Zhis22=np.array(Zhis22), Zhis21=np.array(Zhis21),
                       Zhisall=np.array(Zhisall), sX=sX, sY=sY,
                       time=time, ra=ra, coordx=coordx, coordy=coordy)
        # TODO d/dt allZ for r-drift etc. mean as vp in sat-time
        if coordx in (1, 2) and coordy in (1, 2):
            results['aspect'] = 'equal'
        return results, acckwargs

    def _post_dig(self, results):
        r = results
        ax1 = {k: v for k, v in r.items() if k in [
            'X', 'Y', 'Z', 'title', 'xlabel', 'ylabel', 'aspect']}
        return dict(zip_results=[
            ('tmpl_contourf', 121, ax1),
            ('tmpl_line', 121, dict(
                LINE=[([], [])],
                TEXT_X=r['sX'], TEXT_Y=r['sY'],
                TEXT_T=['11', '12', '22', '21'])),
            ('tmpl_line', 122, dict(
                LINE=[(r['time'], r['Zhis%s' % k], 'P-%s' % k)
                      for k in ('all', '11', '12', '22', '21')],
                xlabel=r'$R_0/c_s$', xlim=r['time'][[0, -1]],
                ylabel=self._pdf_tex[self.section[2]], aspect=None,
            )),
        ])
