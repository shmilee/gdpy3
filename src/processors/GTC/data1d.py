# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Source fortran code:

v110922
-------

1. diagnosis.F90:opendiag():739, ::
    write(iodata1d,101)ndstep,mpsi+1,nspecies,nhybrid,mpdata1d,nfield,mfdata1d

2. diagnosis.F90:opendiag():790, ::
    ndata=(mpsi+1)*(nspecies*mpdata1d+nfield*mfdata1d)

diagnosis.F90:194-203, ::
    write(iodata1d,102)data1di
    if(nspecies>1)then
       if(nhybrid>0)write(iodata1d,102)data1de
       if(fload>0)write(iodata1d,102)data1df
    endif
    write(iodata1d,102)field00
    write(iodata1d,102)fieldrms

3. data1di(0:mpsi,mpdata1d), pushi.F90:461-472, ::
    ! radial profile of particle and energy flux
        dden(ii-1)=dden(ii-1)+fullf*dp1
        dden(ii)  =dden(ii)+  fullf*(1.0-dp1)
        data1di(ii-1,1)=data1di(ii-1,1)+vdr*deltaf*dp1
        data1di(ii,  1)=data1di(ii,  1)+vdr*deltaf*(1.0-dp1)
        data1di(ii-1,2)=data1di(ii-1,2)+vdr*deltaf*energy*dp1
        data1di(ii,  2)=data1di(ii,  2)+vdr*deltaf*energy*(1.0-dp1)
    ! radial profiles of momentum flux
        data1di(ii-1,3)=data1di(ii-1,3)+vdr*deltaf*angmom*dp1
        data1di(ii,  3)=data1di(ii,  3)+vdr*deltaf*angmom*(1.0-dp1)

4. data1de(0:mpsi,mpdata1d), pushe.F90:623-634

5. data1df(0:mpsi,mpdata1d), pushf.F90:459-470

6. field00(0:mpsi,nfield), diagnosis.F90:83-136, ::
    !!! field diagnosis: phi, a_para, fluid_ne, ...
    ...
    do i=0,mpsi
       field00(i,nf)=phip00(i)/rho0
       fieldrms(i,nf)=sum(phi(0,igrid(i):igrid(i)+mtheta(i)-1)**2)/(rho0**4)
    enddo
    ...
    do i=0,mpsi
       field00(i,nf)=apara00(i)/(rho0*sqrt(betae*aion))
       fieldrms(i,nf)=sum(sapara(0,igrid(i):igrid(i)+mtheta(i)-1)**2)/(rho0*rho0*betae*aion)
    enddo
    ...
    do i=0,mpsi
        field00(i,nf)=fluidne00(i)
        fieldrms(i,nf)=sum(sfluidne(0,igrid(i):igrid(i)+mtheta(i)-1)**2)
    enddo

7. fieldrms(0:mpsi,nfield), diagnosis.F90:83-136
'''

import numpy
from ..core import DigCore, LayCore, PcolorFigInfo, log

__all__ = ['Data1dDigCoreV110922', 'Data1dLayCoreV110922']


class Data1dDigCoreV110922(DigCore):
    '''
    Radial Time Data

    1) Radial profile of particle, energy and momentum flux.
       Source: data1di, data1de, data1df.
       The flux 2d array is flux[r,time].
    2) Field diagnosis: phi, a_para, fluid_ne.
       Source: field00, fieldrms.
       The field 2d array is field[r,time].
    '''
    __slots__ = []
    itemspattern = ['^(?P<section>data1d)\.out$',
                    '.*/(?P<section>data1d)\.out$']
    default_section = 'data1d'
    _datakeys = (
        # 1. diagnosis.F90:opendiag():739
        'ndstep', 'mpsi+1', 'nspecies', 'nhybrid',
        'mpdata1d', 'nfield', 'mfdata1d',
        # 3. data1di(0:mpsi,mpdata1d)
        'i-particle-flux', 'i-energy-flux', 'i-momentum-flux',
        # 4. data1de(0:mpsi,mpdata1d)
        'e-particle-flux', 'e-energy-flux', 'e-momentum-flux',
        # 5. data1df(0:mpsi,mpdata1d)
        'f-particle-flux', 'f-energy-flux', 'f-momentum-flux',
        # 6. field00(0:mpsi,nfield)
        'field00-phi', 'field00-apara', 'field00-fluidne',
        # 7. fieldrms(0:mpsi,nfield)
        'fieldrms-phi', 'fieldrms-apara', 'fieldrms-fluidne')

    def _convert(self):
        '''Read 'data1d.out'.'''
        with self.rawloader.get(self.files) as f:
            log.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        # 1. diagnosis.F90:opendiag():739
        log.debug("Filling datakeys: %s ..." % str(self._datakeys[:7]))
        for i, key in enumerate(self._datakeys[:7]):
            sd.update({key: int(outdata[i].strip())})

        # 2. diagnosis.F90:opendiag():790
        outdata = numpy.array([float(n.strip()) for n in outdata[7:]])
        ndata = sd['mpsi+1'] * (sd['nspecies'] * sd['mpdata1d'] +
                                sd['nfield'] * sd['mfdata1d'])
        if len(outdata) // ndata != sd['ndstep']:
            log.debug("Filling datakeys: %s ..." % 'ndstep')
            sd.update({'ndstep': len(outdata) // ndata})
            outdata = outdata[:sd['ndstep'] * ndata]

        # reshape outdata
        outdata = outdata.reshape((ndata, sd['ndstep']), order='F')

        # 3. data1di(0:mpsi,mpdata1d), mpdata1d=3
        log.debug("Filling datakeys: %s ..." % str(self._datakeys[7:10]))
        sd.update({'i-particle-flux': outdata[:sd['mpsi+1'], :]})
        index0, index1 = sd['mpsi+1'], 2 * sd['mpsi+1']
        sd.update({'i-energy-flux':  outdata[index0:index1, :]})
        index0, index1 = 2 * sd['mpsi+1'], 3 * sd['mpsi+1']
        sd.update({'i-momentum-flux':  outdata[index0:index1, :]})

        # 4. data1de(0:mpsi,mpdata1d)
        if sd['nspecies'] > 1 and sd['nhybrid'] > 0:
            log.debug("Filling datakeys: %s ..." % str(self._datakeys[10:13]))
            index0, index1 = index1, index1 + sd['mpsi+1']
            sd.update({'e-particle-flux': outdata[index0:index1, :]})
            index0, index1 = index1, index1 + sd['mpsi+1']
            sd.update({'e-energy-flux': outdata[index0:index1, :]})
            index0, index1 = index1, index1 + sd['mpsi+1']
            sd.update({'e-momentum-flux': outdata[index0:index1, :]})
        else:
            sd.update({'e-particle-flux': [],
                       'e-energy-flux': [], 'e-momentum-flux': []})

        # 5. data1df(0:mpsi,mpdata1d)
        if ((sd['nspecies'] == 2 and sd['nhybrid'] == 0) or
                (sd['nspecies'] == 3 and sd['nhybrid'] > 0)):
            log.debug("Filling datakeys: %s ..." % str(self._datakeys[13:16]))
            index0, index1 = index1, index1 + sd['mpsi+1']
            sd.update({'f-particle-flux': outdata[index0:index1, :]})
            index0, index1 = index1, index1 + sd['mpsi+1']
            sd.update({'f-energy-flux': outdata[index0:index1, :]})
            index0, index1 = index1, index1 + sd['mpsi+1']
            sd.update({'f-momentum-flux': outdata[index0:index1, :]})
        else:
            sd.update({'f-particle-flux': [],
                       'f-energy-flux': [], 'f-momentum-flux': []})

        # 6. field00(0:mpsi,nfield), nfield=3
        log.debug("Filling datakeys: %s ..." % str(self._datakeys[16:19]))
        index0 = sd['mpsi+1'] * sd['nspecies'] * sd['mpdata1d']
        index1 = index0 + sd['mpsi+1']
        sd.update({'field00-phi': outdata[index0:index1, :]})
        index0, index1 = index1, index1 + sd['mpsi+1']
        sd.update({'field00-apara': outdata[index0:index1, :]})
        index0, index1 = index1, index1 + sd['mpsi+1']
        sd.update({'field00-fluidne': outdata[index0:index1, :]})

        # 7. fieldrms(0:mpsi,nfield)
        log.debug("Filling datakeys: %s ..." % str(self._datakeys[19:22]))
        index0, index1 = index1, index1 + sd['mpsi+1']
        sd.update({'fieldrms-phi': outdata[index0:index1, :]})
        index0, index1 = index1, index1 + sd['mpsi+1']
        sd.update({'fieldrms-apara': outdata[index0:index1, :]})
        index0, index1 = index1, index1 + sd['mpsi+1']
        sd.update({'fieldrms-fluidne': outdata[index0:index1, :]})

        return sd


class FluxFigInfo(PcolorFigInfo):
    '''Figures of particle, energy and momentum flux of ion, electron, EP.'''
    __slots__ = ['particle', 'flux']
    figurenums = ['%s_%s_flux' % (p, f)
                  for p in ['ion', 'electron', 'fastion']
                  for f in ['particle', 'energy', 'momentum']]
    numpattern = r'^%s_%s_flux$' % (
        r'(?P<particle>(?:ion|electron|fastion))',
        r'(?P<flux>(?:particle|energy|momentum))')

    def _get_srckey_extrakey(self, fignum):
        groupdict = self._pre_check_get(fignum, 'particle', 'flux')
        self.particle = groupdict['particle']
        self.flux = groupdict['flux']
        Zkey = '%s-%s-flux' % (self.particle[0], self.flux)
        return [Zkey], ['gtc/tstep', 'gtc/ndiag']

    def _get_data_X_Y_Z_title_etc(self, data):
        tunit = data['gtc/tstep'] * data['gtc/ndiag']
        Z = data['%s-%s-flux' % (self.particle[0], self.flux)]
        y, x = Z.shape if Z.size > 0 else (0, 0)
        X, Y = numpy.arange(1, x + 1) * tunit, numpy.arange(0, y)
        title = '%s %s flux' % (self.particle, self.flux)
        if self.particle == 'ion':
            title = 'thermal %s' % title
        elif self.particle == 'fastion':
            title = title.replace('fastion', 'fast ion')
        return dict(X=X, Y=Y, Z=Z, title=title,
                    xlabel=r'time($R_0/c_s$)', ylabel=r'$r$(mpsi)')


class Field00FigInfo(PcolorFigInfo):
    '''Figures of phi, a_para, fluid_ne of field00'''
    __slots__ = ['flow']
    figurenums = ['zonal_%s' % f for f in ['flow', 'current', 'fluidne']]
    numpattern = r'^zonal_(?P<flow>(?:flow|current|fluidne))$'
    __keystrdict = {'flow': 'phi', 'current': 'apara', 'fluidne': 'fluidne'}

    def _get_srckey_extrakey(self, fignum):
        groupdict = self._pre_check_get(fignum, 'flow')
        self.flow = groupdict['flow']
        Zkey = 'field00-%s' % self.__keystrdict[self.flow]
        return [Zkey], ['gtc/tstep', 'gtc/ndiag']

    def _get_data_X_Y_Z_title_etc(self, data):
        tunit = data['gtc/tstep'] * data['gtc/ndiag']
        Z = data['field00-%s' % self.__keystrdict[self.flow]]
        y, x = Z.shape if Z.size > 0 else (0, 0)
        X, Y = numpy.arange(1, x + 1) * tunit, numpy.arange(0, y)
        return dict(X=X, Y=Y, Z=Z, title=self.fignum.replace('_', ' '),
                    xlabel=r'time($R_0/c_s$)', ylabel=r'$r$(mpsi)')


class FieldRMSFigInfo(PcolorFigInfo):
    '''Figures of phi, a_para, fluid_ne of fieldrms'''
    __slots__ = ['field']
    figurenums = ['%s_rms' % f for f in ['phi', 'apara', 'fluidne']]
    numpattern = r'^(?P<field>(?:phi|apara|fluidne))_rms$'

    def _get_srckey_extrakey(self, fignum):
        groupdict = self._pre_check_get(fignum, 'field')
        self.field = groupdict['field']
        return ['fieldrms-%s' % self.field], ['gtc/tstep', 'gtc/ndiag']

    def _get_data_X_Y_Z_title_etc(self, data):
        tunit = data['gtc/tstep'] * data['gtc/ndiag']
        Z = data['fieldrms-%s' % self.field]
        y, x = Z.shape if Z.size > 0 else (0, 0)
        X, Y = numpy.arange(1, x + 1) * tunit, numpy.arange(0, y)
        title = r'$%s rms$' % self.field
        title = title.replace('phi', '\phi').replace('apara', 'A_{\parallel}')
        return dict(X=X, Y=Y, Z=Z, title=title,
                    xlabel=r'time($R_0/c_s$)', ylabel=r'$r$(mpsi)')


class Data1dLayCoreV110922(LayCore):
    '''
    Radial Time Figures
    '''
    __slots__ = []
    itemspattern = ['^(?P<section>data1d)$']
    default_section = 'data1d'
    figinfoclasses = [FluxFigInfo, Field00FigInfo, FieldRMSFigInfo]
