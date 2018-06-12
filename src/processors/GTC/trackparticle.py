# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Source fortran code:

v110922
-------

tracking.F90, subroutine write_tracked_particles:270:278-289
     write(cdum,'("trackp_dir/TRACKP.",i5.5)')mype
     ......
     write(57,*)istep
     write(57,*)ntrackp(1:nspecies)
    ! if(mype==0)write(*,*)'write istep and ntrackp'
    ! if(mype==0)write(*,*)istep
     do j=1,ntrackp(1)
        write(57,*)ptrackedi(1:nparam,j)
     enddo
     if(nhybrid>0)then
        do j=1,ntrackp(2)
           write(57,*)ptrackede(1:nparam,j)
        enddo
     endif

'''

import types
import numpy as np
from ..core import DigCore, LayCore, FigInfo, log

__all__ = ['TrackParticleDigCoreV110922', 'TrackParticleLayCoreV110922']


class TrackParticleDigCoreV110922(DigCore):
    '''
    Tracking Particle Data

    1) ion, electron
       Shape of the array data is (mstep/ndiag,7).
       7 quantities of particle:
       istep, X, Z, zeta, rho_para, weight, sqrt(mu).
    '''
    __slots__ = []
    nitems = '+'
    itemspattern = ['^(?P<section>trackp)_dir/TRACKP\.\d{5}$',
                    '.*/(?P<section>trackp)_dir/TRACKP\.\d{5}$']
    default_section = 'trackp'
    _datakeys = ('get by function :meth:`_convert`',)

    def _convert(self):
        '''Read 'trackp_dir/TRACKP.%05d' % mype.'''
        ion = {}
        electron = {}
        fastion = {}
        Particles = [ion, electron, fastion]
        keyprefix = ['ion', 'electron', 'fastion']
        for f in self.files:
            with self.rawloader.get(f) as fid:
                log.debug("Read file '%s'." % f)
                istep = fid.readline()
                while istep:
                    nums = [int(n) for n in fid.readline().split()]
                    for p, n in enumerate(nums):
                        particle = Particles[p]
                        for i in range(n):
                            line = (istep + fid.readline() +
                                    fid.readline()).split()
                            key = keyprefix[p]
                            for k in line[:-3:-1]:
                                key += '-' + str(int(float(k)))
                            line = [int(line[0])] + [float(l)
                                                     for l in line[1:-2]]
                            if key in particle:
                                particle[key].append(line)
                            else:
                                particle[key] = [line]
                    istep = fid.readline()
        sd = {}
        for particle in Particles:
            for key in particle.keys():
                particle[key].sort()
                particle[key] = np.array(particle[key])
            if particle.keys():
                log.debug("Filling datakeys: %s ..." %
                          str(tuple(particle.keys())))
                sd.update(particle)
        return sd


class OrbitFigInfo(FigInfo):
    '''Figures for particle 2d or 3d orbit.'''
    __slots__ = ['dimension', 'species', 'pckloader']
    figurenums = ['orbit_%s_%s' % (dim, spec)
                  for spec in ['ion', 'electron']  # , 'fastion']
                  for dim in ['2d', '3d']]
    numpattern = r'^orbit_%s_%s$' % (r'(?P<dim>(?:2d|3d))',
                                     r'(?P<spec>(?:ion|electron|fastion))')

    def __init__(self, fignum, scope, groups):
        groupdict = self._pre_check_get(fignum, 'dim', 'spec')
        self.dimension = groupdict['dim']
        self.species = groupdict['spec']
        super(OrbitFigInfo, self).__init__(
            fignum, scope, groups, [], ['gtc/r0'], 0)

    def get_data(self, pckloader):
        '''Save pckloader for :meth:`calculate`, then super().get_data.'''
        self.pckloader = pckloader
        return super(OrbitFigInfo, self).get_data(pckloader)

    sortfuns = {
        'increase': lambda n: int(n.split('-')[1] * 10 + n.split('-')[2]),
        'in-': lambda n: int(n.split('-')[1] * 10 + n.split('-')[2]),
        'decrease': lambda n: - int(n.split('-')[1] * 10 + n.split('-')[2]),
        'de-': lambda n: - int(n.split('-')[1] * 10 + n.split('-')[2]),
        'random': lambda n: np.random.random(),
    }

    def calculate(self, data, **kwargs):
        '''
        kwargs
        ------
        particle 2d, 3d orbit kwargs:
            *skey*: key function for `sorted`,
                or str 'increase', 'in-', 'decrease', 'de-', 'random',
                default 'increase'.
            *index_start*: int
                select sorted particles in pckloader, default 0
                index = range(index_start, index_start + 9)
            *cal_dr*: bool
                calculate delta R of trapped ions in 2d orbit, default False.
        '''
        r0 = data['gtc/r0']
        trackp = 'trackp/%s-' % self.species
        particles = self.pckloader.find(trackp)
        total = len(particles)
        log.parm("Total number of tracked %s particles: %d."
                 % (self.species, total))
        self.layout['skey'] = dict(
            widget='Dropdown',
            options=['increase', 'decrease', 'random'],
            value='increase',
            description='sort particles:')
        self.layout['index_start'] = dict(
            widget='IntSlider',
            rangee=(0, total - 1, 1),
            value=0,
            description='particles index start:')
        if self.dimension == '2d' and self.species == 'ion':
            self.layout['cal_dr'] = dict(
                widget='Checkbox',
                value=False,
                description='show $\Delta R$ of trapped ion')
        # sorted key function
        skey = kwargs['skey'] if 'skey' in kwargs else 'increase'
        if isinstance(skey, types.FunctionType):
            particles = sorted(particles, key=skey)
        else:
            if skey not in self.sortfuns:
                log.warning("Invalid `sorted` key for tracked particles.")
                skey = 'increase'
            particles = sorted(particles, key=self.sortfuns[skey])
        # index of sorted particles
        index_start = kwargs.get('index_start', None)
        if not(isinstance(index_start, int) and 0 <= index_start < total):
            index_start = 0
        cal_dr = bool(kwargs.get('cal_dr', False))
        ax_cal = {}
        for n, idx in enumerate(range(index_start, index_start + 9)):
            number = int("33%s" % str(n + 1))
            log.debug("calculating Axes %d ..." % number)
            if idx + 1 > total:
                log.error("Failed to calculate Axes %d ..." % number)
                continue
            try:
                pdata = self.pckloader[particles[idx]]
                pname = particles[idx].replace(trackp, '')
                title = '(%d) %s' % (idx, pname)
                R = pdata[:, 1] * r0
                Z = pdata[:, 2] * r0
                if self.dimension == '2d':
                    rlim = 1.1 * max(abs(np.max(R) - r0), np.max(Z),
                                     abs(r0 - np.min(R)), abs(np.min(Z)))
                    layoutkw = dict(xlim=[r0 - rlim, r0 + rlim],
                                    ylim=[-rlim, rlim],
                                    title=title)
                    data = [[1, 'plot', (R, Z), dict()],
                            [2, 'set_aspect', ('equal',), dict()]]
                    if cal_dr and self.species == 'ion':
                        data = self.__trapped_ion_dr(
                            R, Z, r0, pname, rlim) or data
                    ax_cal[number] = dict(layoutkw=layoutkw, data=data)
                else:
                    zeta = pdata[:, 3]
                    X = R * np.cos(zeta)
                    Y = R * np.sin(zeta)
                    Rlim = 1.05 * np.max(R)
                    scale = [-Rlim, Rlim]
                    lay = dict(title=title, projection='3d')
                    data = [
                        [1, 'plot', (X, Y, Z), dict(linewidth=1)],
                        [2, 'set_aspect', ('equal',), dict()],
                        [3, 'auto_scale_xyz', (scale, scale, scale), dict()],
                    ]
                    ax_cal[number] = dict(layoutkw=lay, data=data)
            except Exception:
                log.error("Failed to get data of '%s' from %s!"
                          % (self.species + ':' + pname, self.pckloader.path),
                          exc_info=1)
        self.calculation['axes_results'] = ax_cal
        # suptitle
        self.calculation['suptitle'] = "%s orbits of %s (9/%d)" % (
            self.dimension.upper(), self.species, total)

    def __trapped_ion_dr(self, R, Z, r0, pname, rlim):
        # find dr = |R1-R2| while z=0
        # TODO, check trapped
        fR = []
        for t in range(0, len(R) - 1):
            if Z[t] * Z[t + 1] < 0:
                fR.append((R[t] + R[t + 1]) / 2)
        R1 = sum(fR[::2]) / len(fR[::2])
        R2 = sum(fR[1::2]) / len(fR[1::2])
        dr = abs(R1 - R2)
        # theta M
        mpoints = np.array(sorted(zip(R, Z), key=lambda p: p[0])[:4])
        minR = np.average(mpoints[:, 0])
        minZ = np.average(np.abs(mpoints[:, 1]))
        minvec = [minR - r0, minZ]
        costhetaM = np.inner([r0, 0], minvec) / r0 / \
            np.sqrt(np.inner(minvec, minvec))
        thetaM = np.arccos(costhetaM) * 180 / np.pi
        self.calculation.update(
            {'%s-dr' % pname: dr, '%s-theta' % pname: thetaM})
        data = [[1, 'plot', (R, Z),
                 dict(label='$\Delta R$ = %.3f' % dr)],
                [2, 'plot', ([R1, R1], [-0.6 * rlim, 0.6 * rlim]),
                 dict(label='R=%.3f' % R1)],
                [3, 'plot', ([R2, R2], [-0.6 * rlim, 0.6 * rlim]),
                 dict(label='R=%.3f' % R2)],
                [4, 'plot', ([r0, r0 + rlim], [0, 0], 'k'), {}],
                [5, 'plot', ([r0, minR], [0, minZ]), {}],
                [6, 'text', (r0 + 1, 0 + 1,
                             r'$\theta$ = %.2f' % thetaM), {}],
                [7, 'legend', (), dict()],
                [8, 'set_aspect', ('equal',), dict()]]
        return data

    def serve(self, plotter):
        if not plotter.name.startswith('mpl::'):
            log.error("Need 'mpl::' plotter, not %s!" % plotter.name)
            raise ValueError("Plotter %s not supported!" % plotter.name)
        AxStrus = []
        for number in range(331, 340):
            if number not in self.calculation['axes_results']:
                AxStrus.append({'data': [], 'layout': [number, {}]})
                continue
            res = self.calculation['axes_results'][number]
            layoutkw, data = res['layoutkw'], res['data']
            if number in (337, 338, 339):
                if self.dimension == '2d':
                    layoutkw.update(xlabel='R(cm)')
                else:
                    layoutkw.update(xlabel='X(cm)', ylabel='Y(cm)')
            if number in (331, 334, 337) and self.dimension == '2d':
                layoutkw.update(ylabel='Z(cm)')
            if number in (333, 336, 339) and self.dimension == '3d':
                layoutkw.update(zlabel='Z(cm)')
            AxStrus.append({'data': data, 'layout': [number, layoutkw]})
        # suptitle
        data = AxStrus[0]['data']
        order = len(data) + 1

        def addsuptitle(fig, ax, art):
            return fig.suptitle(self.calculation['suptitle'])
        data.append([order, 'revise', addsuptitle, dict()])
        return AxStrus, []


class TrackParticleLayCoreV110922(LayCore):
    '''
    Tracking Particle Figures
    '''
    __slots__ = []
    itemspattern = ['^(?P<section>trackp)$']
    default_section = 'trackp'
    figinfoclasses = [OrbitFigInfo]
