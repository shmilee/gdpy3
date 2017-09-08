# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

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

import os
import numpy
from .block import Block, log

__all__ = ['MeshgridBlockV110922']


class MeshgridBlockV110922(Block):
    '''
    Meshgrid data

    1) psimesh, sprpsi, qmesh, kapatmti, kapatmte, kapatmni, kapatmne
       Shape of the array data is (mpsi+1,).

    Attributes
    ----------
    file: str
        File path of GTC ``meshgrid.out`` to convert
    group: str of data group
    datakeys: tuple
        data keys of physical quantities in ``meshgrid.out``
    data: dict of converted data
    '''
    __slots__ = []
    _Datakeys = (
        'psimesh', 'sprpsi', 'qmesh',
        'kapatmti', 'kapatmte', 'kapatmni', 'kapatmne')

    def convert(self, mpsi=None):
        '''Read meshgrid.out

        convert the .out data to self.data as a dict,
        save list in data dict as numpy.array.
        '''
        with open(self.file, 'r') as f:
            log.ddebug("Read file '%s'." % self.file)
            outdata = f.readlines()

        sd = self.data
        if mpsi == len(outdata) / 7:
            shape = (7, mpsi)
        else:
            # guess the shape
            shape = (7, len(outdata) // 7)
            outdata = outdata[:len(outdata) // 7 * 7]

        log.debug("Filling datakeys: %s ..." % str(self.datakeys[:]))
        outdata = numpy.array([float(n.strip()) for n in outdata])
        outdata = outdata.reshape(shape, order='F')
        for i, key in enumerate(self.datakeys):
            sd.update({key: outdata[i]})
