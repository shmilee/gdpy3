# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

'''
Source fortran code:

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
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog

__all__ = ['TrackParticleConverter', 'TrackParticleOrbitDigger']


class TrackParticleConverter(Converter):
    '''
    Tracking Particle Data

    1) ion, electron. key example: 'ion-31-2'
       Shape of the array data is (mstep/ndiag,7).
       7 quantities of particle:
       istep, X, Z, zeta, rho_para, weight, sqrt(mu).
    '''
    __slots__ = []
    nitems = '+'
    itemspattern = ['^(?P<section>trackp)_dir/TRACKP\.\d{5}$',
                    '.*/(?P<section>trackp)_dir/TRACKP\.\d{5}$']

    def _convert(self):
        '''Read 'trackp_dir/TRACKP.%05d' % mype.'''
        ion = {}
        electron = {}
        fastion = {}
        Particles = [ion, electron, fastion]
        keyprefix = ['ion', 'electron', 'fastion']
        for f in self.files:
            with self.rawloader.get(f) as fid:
                clog.debug("Read file '%s'." % f)
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
                clog.debug("Filling datakeys: %s ..." %
                           str(tuple(particle.keys())))
                sd.update(particle)
        return sd


class TrackParticleOrbitDigger(Digger):
    '''particle 2d or 3d orbit.'''
    __slots__ = ['dimension']
    nitems = '?'
    itemspattern = [r'^(?P<s>trackp)/(?P<particle>(?:ion|electron|fastion))'
                    + r'-(?P<tag>\d+-\d+)$']
    commonpattern = ['gtc/r0']
    numseeds = ['2d', '3d']

    def _set_fignum(self, numseed=None):
        self._fignum = 'orbit_%s_%s_%s' % (
            numseed, self.section[1], self.section[2])
        self.dimension = numseed

    def _dig(self, **kwargs):
        '''
        kwargs
        ------
        *cal_dr*: bool
            calculate delta R of trapped ions in 2d orbit, default False.
        '''
        acckwargs = {}
        pdata, r0 = self.pckloader.get_many(self.srckeys[0], 'gtc/r0')
        title = 'orbit of %s %s' % self.section[1:]
        results = dict(r0=r0, title='%s %s' % (self.dimension.upper(), title))
        R = pdata[:, 1] * r0
        Z = pdata[:, 2] * r0
        if self.dimension == '2d':
            rlim = 1.1 * max(abs(np.max(R) - r0), np.max(Z),
                             abs(r0 - np.min(R)), abs(np.min(Z)))
            results.update(dict(R=R, Z=Z, rlim=rlim))
            if bool(kwargs.get('cal_dr', False)) and self.section[1] == 'ion':
                acckwargs['cal_dr'] = True
                results.update(self.__trapped_ion_dr(R, Z, r0))
        else:
            zeta = pdata[:, 3]
            X = R * np.cos(zeta)
            Y = R * np.sin(zeta)
            rlim = 1.05 * np.max(R)
            results.update(dict(X=X, Y=Y, Z=Z, rlim=rlim))
        return results, acckwargs

    def __trapped_ion_dr(self, R, Z, r0):
        '''find dr = |R1-R2| while z=0'''
        try:
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
            return dict(dr=dr, R1=R1, R2=R2,
                        minR=minR, minZ=minZ, thetaM=thetaM)
        except Exception:
            dlog.warning('Cannot calculate dr of trapped ions!', exc_info=1)
            return {}
