# -*- coding: utf-8 -*-

# Copyright (c) 2019-2020 shmilee

'''
Source fortran code:

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
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog

_all_Converters = ['MeshgridConverter']
_all_Diggers = []
__all__ = _all_Converters + _all_Diggers


class MeshgridConverter(Converter):
    '''
    Meshgrid data

    1) psimesh, sprpsi, qmesh, kapatmti, kapatmte, kapatmni, kapatmne
       Shape of the array data is (mpsi+1,).
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = [r'^(?P<section>meshgrid)\.out$',
                    r'.*/(?P<section>meshgrid)\.out$']
    _datakeys = (
        'psimesh', 'sprpsi', 'qmesh',
        'kapatmti', 'kapatmte', 'kapatmni', 'kapatmne')

    def _convert(self):
        '''Read 'meshgrid.out'.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        shape = (7, len(outdata) // 7)
        outdata = outdata[:len(outdata) // 7 * 7]
        if len(outdata) % 7 != 0:
            clog.warning("Missing some raw data in '%s'! Guess the shape '%s'."
                         % (self.files, shape))

        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:]))
        outdata = numpy.array([float(n.strip()) for n in outdata])
        outdata = outdata.reshape(shape, order='F')
        for i, key in enumerate(self._datakeys):
            sd.update({key: outdata[i]})

        return sd
