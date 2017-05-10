# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

r''' Source fortran code:

v110922
=======

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

import os
import numpy
from .datablock import DataBlock

__all__ = ['TrackParticleBlockV110922']


class TrackParticleBlockV110922(DataBlock):
    '''Tracking Particle data

    1) ion, electron

    Attributes
    ----------
        path: str
            Path of GTC ``trackp_dir/`` to convert
        file: alias path
        group: str of data group
        datakeys: tuple
            tags of tracked particles
        data: dict of converted data
    '''
    __slots__ = ['path', 'file', 'group', 'datakeys', 'data']

    def __init__(self, path=None, group='trackp'):
        if os.path.isdir(path):
            self.path = path
        else:
            raise IOError("Can't find '%s' dir: '%s'!" % (group, path))
        self.file = path
        self.group = group
        self.datakeys = ('set by function convert',)
        self.data = dict(description='Tracking Particle data'
                         '\nShape of the array data is (mstep/ndiag,7).'
                         '\n7 quantities of particle:'
                         '\n  istep, X, Z, zeta,'
                         '\n  rho_para, weight, sqrt(mu).')

    def convert(self):
        '''Read trackp_dir/TRACKP.("%05d" % mype)

        convert the data to self.data as a dict,
        save list in data dict as numpy.array.
        '''

        ion = {}
        electron = {}
        fastion = {}
        Particles = [ion, electron, fastion]
        keyprefix = ['ion', 'electron', 'fastion']
        for f in sorted(os.listdir(self.path)):
            with open(os.path.join(self.path, f), 'r') as fid:
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

        for particle in Particles:
            for key in particle.keys():
                particle[key].sort()
                particle[key] = numpy.array(particle[key])
            self.data.update(particle)

        self.datakeys = tuple(self.data.keys())
