# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

'''
Source fortran code:

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
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog

__all__ = ['Data1dConverter', 'Data1dFluxDigger', 'Data1dFieldDigger']


class Data1dConverter(Converter):
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
    nitems = '?'
    itemspattern = ['^(?P<section>data1d)\.out$',
                    '.*/(?P<section>data1d)\.out$']
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
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        # 1. diagnosis.F90:opendiag():739
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:7]))
        for i, key in enumerate(self._datakeys[:7]):
            sd.update({key: int(outdata[i].strip())})

        # 2. diagnosis.F90:opendiag():790
        outdata = numpy.array([float(n.strip()) for n in outdata[7:]])
        ndata = sd['mpsi+1'] * (sd['nspecies'] * sd['mpdata1d'] +
                                sd['nfield'] * sd['mfdata1d'])
        if len(outdata) // ndata != sd['ndstep']:
            clog.debug("Filling datakeys: %s ..." % 'ndstep')
            sd.update({'ndstep': len(outdata) // ndata})
            outdata = outdata[:sd['ndstep'] * ndata]

        # reshape outdata
        outdata = outdata.reshape((ndata, sd['ndstep']), order='F')

        # 3. data1di(0:mpsi,mpdata1d), mpdata1d=3
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[7:10]))
        sd.update({'i-particle-flux': outdata[:sd['mpsi+1'], :]})
        index0, index1 = sd['mpsi+1'], 2 * sd['mpsi+1']
        sd.update({'i-energy-flux':  outdata[index0:index1, :]})
        index0, index1 = 2 * sd['mpsi+1'], 3 * sd['mpsi+1']
        sd.update({'i-momentum-flux':  outdata[index0:index1, :]})

        # 4. data1de(0:mpsi,mpdata1d)
        if sd['nspecies'] > 1 and sd['nhybrid'] > 0:
            clog.debug("Filling datakeys: %s ..." % str(self._datakeys[10:13]))
            index0, index1 = index1, index1 + sd['mpsi+1']
            sd.update({'e-particle-flux': outdata[index0:index1, :]})
            index0, index1 = index1, index1 + sd['mpsi+1']
            sd.update({'e-energy-flux': outdata[index0:index1, :]})
            index0, index1 = index1, index1 + sd['mpsi+1']
            sd.update({'e-momentum-flux': outdata[index0:index1, :]})

        # 5. data1df(0:mpsi,mpdata1d)
        if ((sd['nspecies'] == 2 and sd['nhybrid'] == 0) or
                (sd['nspecies'] == 3 and sd['nhybrid'] > 0)):
            clog.debug("Filling datakeys: %s ..." % str(self._datakeys[13:16]))
            index0, index1 = index1, index1 + sd['mpsi+1']
            sd.update({'f-particle-flux': outdata[index0:index1, :]})
            index0, index1 = index1, index1 + sd['mpsi+1']
            sd.update({'f-energy-flux': outdata[index0:index1, :]})
            index0, index1 = index1, index1 + sd['mpsi+1']
            sd.update({'f-momentum-flux': outdata[index0:index1, :]})

        # 6. field00(0:mpsi,nfield), nfield=3
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[16:19]))
        index0 = sd['mpsi+1'] * sd['nspecies'] * sd['mpdata1d']
        index1 = index0 + sd['mpsi+1']
        sd.update({'field00-phi': outdata[index0:index1, :]})
        index0, index1 = index1, index1 + sd['mpsi+1']
        sd.update({'field00-apara': outdata[index0:index1, :]})
        index0, index1 = index1, index1 + sd['mpsi+1']
        sd.update({'field00-fluidne': outdata[index0:index1, :]})

        # 7. fieldrms(0:mpsi,nfield)
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[19:22]))
        index0, index1 = index1, index1 + sd['mpsi+1']
        sd.update({'fieldrms-phi': outdata[index0:index1, :]})
        index0, index1 = index1, index1 + sd['mpsi+1']
        sd.update({'fieldrms-apara': outdata[index0:index1, :]})
        index0, index1 = index1, index1 + sd['mpsi+1']
        sd.update({'fieldrms-fluidne': outdata[index0:index1, :]})

        return sd


class _Data1dDigger(Digger):
    '''
    :meth:`_dig` for Data1dFluxDigger, Data1dFieldDigger
    cutoff x, y of data
    '''
    __slots__ = []

    def _dig(self, **kwargs):
        '''
        kwargs
        ------
        *tcutoff*: [t0,t1]
            X[x0:x1], data[:,x0:x1] where t0<=X[x0:x1]<=t1
        *pcutoff*: [p0,p1]
            Y[y0:y1], data[y0:y1,:] where p0<=Y[y0:y1]<=p1
        '''
        acckwargs = {}
        data, tstep, ndiag = self.pckloader.get_many(
            self.srckeys[0], *self.extrakeys)
        y, x = data.shape
        dt = tstep * ndiag
        X, Y = numpy.arange(1, x + 1) * dt, numpy.arange(0, y)
        x0, x1 = 0, X.size
        if 'tcutoff' in kwargs:
            t0, t1 = kwargs['tcutoff']
            index = numpy.where((X >= t0) & (X < t1 + dt))[0]
            if index.size > 0:
                x0, x1 = index[0], index[-1]+1
                X = X[x0:x1]
                acckwargs['tcutoff'] = kwargs['tcutoff']
            else:
                dlog.warning('Cannot cutoff: %s <= time <= %s!' % (t0, t1))
        y0, y1 = 0, Y.size
        if 'pcutoff' in kwargs:
            p0, p1 = kwargs['pcutoff']
            index = numpy.where((Y >= p0) & (Y < p1+1))[0]
            if index.size > 0:
                y0, y1 = index[0], index[-1]+1
                Y = Y[y0:y1]
                acckwargs['pcutoff'] = kwargs['pcutoff']
            else:
                dlog.warning('Cannot cutoff: %s <= ipsi <= %s!' % (p0, p1))
        # update
        data = data[y0:y1, x0:x1]
        return dict(time=X, ipsi=Y, Z=data, title=self._get_title(),
                    xlabel=r'time($R_0/c_s$)', ylabel=r'$r$(mpsi)'), acckwargs


class Data1dFluxDigger(_Data1dDigger):
    '''particle, energy and momentum flux of ion, electron, fastion.'''
    __slots__ = ['particle']
    itemspattern = ['^(?P<s>data1d)/(?P<particle>(?:i|e|f))'
                    + r'-(?P<flux>(?:particle|energy|momentum))-flux']
    commonpattern = ['gtc/tstep', 'gtc/ndiag']
    __particles = dict(i='ion', e='electron', f='fastion')

    def _set_fignum(self, numseed=None):
        self.particle = self.__particles[self.section[1]]
        self._fignum = '%s_%s_flux' % (self.particle, self.section[2])

    def _get_title(self):
        title = '%s %s flux' % (self.particle, self.section[2])
        if self.particle == 'ion':
            return 'thermal %s' % title
        elif self.particle == 'fastion':
            return title.replace('fastion', 'fast ion')


field_tex_str = {
    'phi': r'\phi',
    'apara': r'A_{\parallel}',
    'fluidne': r'fluidne'
}


class Data1dFieldDigger(Digger):
    '''field00 and fieldrms of phi, a_para, fluidne'''
    __slots__ = []
    itemspattern = ['^(?P<s>data1d)/field(?P<par>(?:00|rms))'
                    + '-(?P<field>(?:phi|apara|fluidne))']
    commonpattern = ['gtc/tstep', 'gtc/ndiag']
    __cnames = dict(phi='flow', apara='current', fluidne='fluidne')

    def _set_fignum(self, numseed=None):
        if self.section[1] == '00':
            self._fignum = 'zonal_%s' % self.__cnames[self.section[2]]
        else:
            self._fignum = '%s_rms' % self.section[2]

    def _get_title(self):
        if self.section[1] == '00':
            return self.fignum.replace('_', ' ')
        else:
            return r'$%s rms$' % field_tex_str[self.section[2]]
