# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Source fortran code:

v110922
-------

diagnosis.F90, subroutine diagnosis:37-50
    !!diagnosis xy
    if(mype==1)then
    open(341,file='meshgrid.out',status='replace')
      do i=0,mpsi
        write(341,*)psimesh(i)
        write(341,*)sprpsi(psimesh(i))
        write(341,*)qmesh(i)
        write(341,*)kapatmti(i)
        write(341,*)kapatmte(i)
        write(341,*)kapatmni(i)
        write(341,*)kapatmne(i)
      enddo
    close(341)
    endif

'''

import numpy
from ..basecore import BaseCore, log

__all__ = ['MeshgridCoreV110922']


class MeshgridCoreV110922(BaseCore):
    '''
    Meshgrid data

    1) psimesh, sprpsi, qmesh, kapatmti, kapatmte, kapatmni, kapatmne
       Shape of the array data is (mpsi+1,).
    '''
    __slots__ = []
    instructions = ['dig']
    filepatterns = ['^(?P<group>meshgrid)\.out$',
                    '.*/(?P<group>meshgrid)\.out$']
    grouppattern = '^meshgrid$'
    _datakeys = (
        'psimesh', 'sprpsi', 'qmesh',
        'kapatmti', 'kapatmte', 'kapatmni', 'kapatmne')

    def _dig(self):
        '''Read 'meshgrid.out'.'''
        with self.rawloader.get(self.file) as f:
            log.ddebug("Read file '%s'." % self.file)
            outdata = f.readlines()

        sd = {}
        shape = (7, len(outdata) // 7)
        outdata = outdata[:len(outdata) // 7 * 7]
        if len(outdata) % 7 != 0:
            log.warn("Missing some raw data in '%s'! Guess the shape '%s'."
                     % (self.file, shape))

        log.debug("Filling datakeys: %s ..." % str(self._datakeys[:]))
        outdata = numpy.array([float(n.strip()) for n in outdata])
        outdata = outdata.reshape(shape, order='F')
        for i, key in enumerate(self._datakeys):
            sd.update({key: outdata[i]})

        return sd
