# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
Source fortran code:

v110922
-------

1. diagnosis.F90:opendiag():734-735, ::
    write(iodiag,101)ndstep,nspecies,mpdiag,nfield,modes,mfdiag
    write(iodiag,102)tstep*ndiag

2. diagnosis.F90:opendiag():729, ::
    ndata=(nspecies*mpdiag+nfield*(2*modes+mfdiag))

diagnosis.F90:156-170, ::
    do i=1,nspecies
       do j=1,mpdiag
          write(iodiag,102)partdata(j,i)
       enddo
    enddo
    do i=1,nfield
       do j=1,mfdiag
          write(iodiag,102)fieldtime(j,i)
       enddo
    enddo
    do i=1,nfield
       do j=1,modes
          write(iodiag,102)fieldmode(1,j,i),fieldmode(2,j,i)
       enddo
    enddo

3. partdata(mpdiag,nspecies)

diagion(mpdiag), pushi.F90:474-485, ::
    !!! ion diagnosis: density,entropy,flow,energy,fluxes of particle,momentum,heat
       diagion(1)=diagion(1)+deltaf
       diagion(2)=diagion(2)+deltaf*deltaf
       diagion(3)=diagion(3)+angmom
       diagion(4)=diagion(4)+angmom*deltaf
       diagion(5)=diagion(5)+energy
       diagion(6)=diagion(6)+energy*deltaf
       diagion(7)=diagion(7)+vdr*deltaf
       diagion(8)=diagion(8)+vdr*angmom*deltaf
       diagion(9)=diagion(9)+vdr*energy*deltaf
    enddo
    diagion(10)=real(mi)

diagelectron(mpdiag), pushe.F90:636-647

diagfast(mpdiag), pushf.F90:472-483

4. fieldtime(mfdiag,nfield), diagnosis.F90:83-136

5. fieldmode(2,modes,nfield), diagnosis.F90:spectrum()
'''

import os
import numpy
from .block import Block, log

__all__ = ['HistoryBlockV110922']


class HistoryBlockV110922(Block):
    '''
    History Data

    1) density,entropy,flow,energy,fluxes of particle,momentum,heat
       Source: diagion, diagelectron, diagfast.
       The particle 2d array is particle[mpdiag,time].
    2) time history of field quantity at theta=zeta=0 & i=iflux
       Source: fieldtime, fieldmode: phi, a_para, fluid_ne
       The fieldtime 2d array is fieldtime[mfdiag,time].
       The fieldmode 2d array is fieldmode[modes,time].

    Attributes
    ----------
    file: str
        File path of GTC ``history.out`` to convert
    group: str of data group
    datakeys: tuple
        data keys of physical quantities in ``history.out``
    data: dict of converted data
    '''
    __slots__ = []
    _Datakeys = (
        # 1. diagnosis.F90:opendiag():734-735
        'ndstep', 'nspecies', 'mpdiag', 'nfield', 'modes', 'mfdiag',
        'tstep*ndiag',
        # 3. partdata(mpdiag,nspecies)
        'ion', 'electron', 'fastion',
        # 4. fieldtime(mfdiag,nfield)
        'fieldtime-phi', 'fieldtime-apara', 'fieldtime-fluidne',
        # 5. fieldmode(2,modes,nfield)
        'fieldmode-phi-real', 'fieldmode-phi-imag',
        'fieldmode-apara-real', 'fieldmode-apara-imag',
        'fieldmode-fluidne-real', 'fieldmode-fluidne-imag')

    def convert(self):
        '''Read history.out

        convert the .out data to self.data as a dict,
        save list in data dict as numpy.array.
        '''
        with open(self.file, 'r') as f:
            log.ddebug("Read file '%s'." % self.file)
            outdata = f.readlines()

        sd = self.data
        # 1. diagnosis.F90:opendiag():734-735
        log.debug("Filling datakeys: %s ..." % str(self.datakeys[:7]))
        for i, key in enumerate(self.datakeys[:6]):
            sd.update({key: int(outdata[i].strip())})
        # 1. tstep*ndiag
        sd.update({'tstep*ndiag': float(outdata[6].strip())})

        # 2. diagnosis.F90:opendiag():729::
        outdata = numpy.array([float(n.strip()) for n in outdata[7:]])
        ndata = sd['nspecies'] * sd['mpdiag'] + \
            sd['nfield'] * (2 * sd['modes'] + sd['mfdiag'])
        if len(outdata) // ndata != sd['ndstep']:
            ndstep = len(outdata) // ndata
            log.debug("Updating datakey: %s=%d ..." % ('ndstep', ndstep))
            sd.update({'ndstep': len(outdata) // ndata})
            outdata = outdata[:sd['ndstep'] * ndata]

        # reshape outdata
        outdata = outdata.reshape((ndata, sd['ndstep']), order='F')

        # 3. partdata(mpdiag,nspecies)
        log.debug("Filling datakey: %s ..." % 'ion')
        sd.update({'ion': outdata[:sd['mpdiag'], :]})
        if sd['nspecies'] > 1:
            log.debug("Filling datakey: %s ..." % 'electron')
            index0, index1 = sd['mpdiag'], 2 * sd['mpdiag']
            sd.update({'electron': outdata[index0:index1, :]})
        else:
            sd.update({'electron': []})
        if sd['nspecies'] > 2:
            log.debug("Filling datakey: %s ..." % 'fastion')
            index0, index1 = 2 * sd['mpdiag'], 3 * sd['mpdiag']
            sd.update({'fastion': outdata[index0:index1, :]})
        else:
            sd.update({'fastion': []})

        # 4. fieldtime(mfdiag,nfield)
        log.debug("Filling datakeys: %s ..." % str(self.datakeys[10:13]))
        index0 = sd['nspecies'] * sd['mpdiag']
        index1 = index0 + sd['mfdiag']
        sd.update({'fieldtime-phi': outdata[index0:index1, :]})
        index0, index1 = index1, index1 + sd['mfdiag']
        sd.update({'fieldtime-apara': outdata[index0:index1, :]})
        index0, index1 = index1, index1 + sd['mfdiag']
        sd.update({'fieldtime-fluidne': outdata[index0:index1, :]})

        # 5. fieldmode(2,modes,nfield)
        log.debug("Filling datakeys: %s ..." % str(self.datakeys[13:]))
        index0, index1 = index1, index1 + 2 * sd['modes']
        sd.update({'fieldmode-phi-real': outdata[index0:index1:2, :]})
        sd.update({'fieldmode-phi-imag': outdata[index0 + 1:index1:2, :]})
        index0, index1 = index1, index1 + 2 * sd['modes']
        sd.update({'fieldmode-apara-real': outdata[index0:index1:2, :]})
        sd.update({'fieldmode-apara-imag': outdata[index0 + 1:index1:2, :]})
        index0, index1 = index1, index1 + 2 * sd['modes']
        sd.update({'fieldmode-fluidne-real': outdata[index0:index1:2, :]})
        sd.update({'fieldmode-fluidne-imag': outdata[index0 + 1:index1:2, :]})
