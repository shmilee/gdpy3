# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

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
from .. import tools
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog

_all_Converters = ['Data1dConverter']
_all_Diggers = ['Data1dFluxDigger', 'Data1dMeanFluxDigger',
                'Data1dFieldDigger', 'Data1dMeanFieldDigger']
__all__ = _all_Converters + _all_Diggers


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
    post_template = 'tmpl_contourf'

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *tcutoff*: [t0,t1], t0 float
            X[x0:x1], data[:,x0:x1] where t0<=X[x0:x1]<=t1
        *pcutoff*: [p0,p1], p0 int
            Y[y0:y1], data[y0:y1,:] where p0<=Y[y0:y1]<=p1
        *use_ra*: bool
            use psi or r/a, default False
        '''
        data, tstep, ndiag = self.pckloader.get_many(
            self.srckeys[0], *self.extrakeys)
        y, x = data.shape
        dt = tstep * ndiag
        X, Y = numpy.arange(1, x + 1) * dt, numpy.arange(0, y)
        if self.kwoptions is None:
            self.kwoptions = dict(
                tcutoff=dict(widget='FloatRangeSlider',
                             rangee=[X[0], X[-1], dt],
                             value=[X[0], X[-1]],
                             description='time cutoff:'),
                pcutoff=dict(widget='IntRangeSlider',
                             rangee=[Y[0], Y[-1], 1],
                             value=[Y[0], Y[-1]],
                             description='mpsi cutoff:'),
                use_ra=dict(widget='Checkbox',
                            value=False,
                            description='Y: r/a'))
        acckwargs = {'tcutoff': [X[0], X[-1]], 'pcutoff': [Y[0], Y[-1]],
                     'use_ra': False}
        x0, x1 = 0, X.size
        if 'tcutoff' in kwargs:
            t0, t1 = kwargs['tcutoff']
            index = numpy.where((X >= t0) & (X < t1 + dt))[0]
            if index.size > 0:
                x0, x1 = index[0], index[-1]+1
                acckwargs['tcutoff'] = [X[x0], X[x1-1]]
                X = X[x0:x1]
            else:
                dlog.warning('Cannot cutoff: %s <= time <= %s!' % (t0, t1))
        y0, y1 = 0, Y.size
        if 'pcutoff' in kwargs:
            p0, p1 = kwargs['pcutoff']
            index = numpy.where((Y >= p0) & (Y < p1+1))[0]
            if index.size > 0:
                y0, y1 = index[0], index[-1]+1
                acckwargs['pcutoff'] = [Y[y0], Y[y1-1]]
                Y = Y[y0:y1]
            else:
                dlog.warning('Cannot cutoff: %s <= ipsi <= %s!' % (p0, p1))
        ylabel = r'$\psi$(mpsi)'
        # use_ra, arr2 [1,mpsi-1], so y0>=1, y1<=mpsi
        if kwargs.get('use_ra', False):
            try:
                arr2, a = self.pckloader.get_many('gtc/arr2', 'gtc/a_minor')
                rr = arr2[:, 1] / a  # index [0, mpsi-2]
                if y0 < 1:
                    y0 = 1
                if y1 > y - 1:
                    y1 = y - 1
                Y = rr[y0-1:y1-1]
            except Exception:
                dlog.warning("Cannot use r/a!", exc_info=1)
            else:
                ylabel = r'$r/a$'
                acckwargs['use_ra'] = True
        # update
        data = data[y0:y1, x0:x1]
        return dict(X=X, Y=Y, Z=data, ylabel=ylabel,
                    title=self._get_title()), acckwargs

    def _post_dig(self, results):
        results.update(xlabel=r'time($R_0/c_s$)')
        return results


class _Data1dMeanDigger(_Data1dDigger):
    '''
    :meth:`_dig` for Data1dMeanFluxDigger, Data1dMeanFieldDigger
    '''
    __slots__ = []
    post_template = 'tmpl_z111p'

    def _dig(self, kwargs):
        '''*mean_select*: str 'iflux' or 'peak'
            default 'mean_iflux'
        *mean_iflux*: [i0, i1], i0 int
            mean data[y0:y1,:] where i0<=mpsi[y0:y1]<=i1
            default i0, i1 = (y0+y1)//2, (y0+y1)//2
        *mean_peak_limit*: float
            set percentage of the min value near peak, default 1.0/e
            mean data[y0:y1,t] where [y0,y1] near the peak
        *mean_peak_greedy*: bool
            if greedy is True, then search from edge, else from peak.
            default False
        *mean_z_abs*: bool
            use z or sqrt(z**2), default False
        *mean_smooth*: bool
            smooth results or not, default True
        *mean_z_weight_order*: int
            use 'abs(z)^mean_z_weight_order * dy' as weight, default 0
        '''
        results, acckwargs = super(_Data1dMeanDigger, self)._dig(kwargs)
        X, Y, Z = results['X'], results['Y'], results['Z']
        y0, y1 = acckwargs['pcutoff']
        use_ra = acckwargs['use_ra']
        select = kwargs.get('mean_select', 'iflux')
        iflux = kwargs.get('mean_iflux', [(y1+y0)//2, (y1+y0)//2])
        peak_limit = kwargs.get('mean_peak_limit', 1.0/numpy.e)
        peak_greedy = bool(kwargs.get('mean_peak_greedy', False))
        z_abs = bool(kwargs.get('mean_z_abs', False))
        smooth = bool(kwargs.get('mean_smooth', True))
        weight_order = kwargs.get('mean_z_weight_order', 0)
        if select == 'iflux':
            i0, i1 = iflux
            if i0 < y0:
                i0 = y0
            if i1 > y1:
                i1 = y1
            # [y0:y1] -> [0:y1-y0]
            i0, i1 = i0-y0, i1-y0
            if z_abs:
                selectZ = numpy.abs(Z[i0:i1+1])
                weight = selectZ**weight_order
            else:
                selectZ = Z[i0:i1+1]
                weight = numpy.abs(selectZ)**weight_order
            if i0 < i1:
                dY = numpy.array([numpy.gradient(Y[i0:i1+1])]).T
                # weight = numpy.repeat(dY, len(X), axis=1) * weight
                weight = numpy.tile(dY, (1, len(X))) * weight
            meanZ = numpy.average(selectZ, axis=0, weights=weight)
            upY = numpy.linspace(Y[i1], Y[i1], len(X))
            downY = numpy.linspace(Y[i0], Y[i0], len(X))
            midY, maxY = None, None
        else:
            maxZ = Z.max(axis=0)
            maxidx = Z.argmax(axis=0)
            meanZ, upY, downY, midY = [], [], [], []
            maxY = Y[maxidx]
            for t in range(len(X)):
                tZ = Z[:, t]
                nY, ntZ = tools.near_peak(
                    tZ, X=Y, intersection=True, lowerlimit=peak_limit,
                    select='one', greedy=peak_greedy)
                if z_abs:
                    ntZ = numpy.abs(ntZ)
                    weight = numpy.gradient(nY) * ntZ**weight_order
                else:
                    weight = numpy.gradient(nY) * numpy.abs(ntZ)**weight_order
                upY.append(nY[-1])
                downY.append(nY[0])
                midY.append(numpy.average(nY, weights=weight))
                meanZ.append(numpy.average(ntZ, weights=weight))
            upY, downY = numpy.array(upY), numpy.array(downY)
            midY, meanZ = numpy.array(midY), numpy.array(meanZ)
            if smooth:
                upY = tools.savgol_golay_filter(numpy.array(upY), info='up')
                downY = tools.savgol_golay_filter(
                    numpy.array(downY), info='down')
                maxY = tools.savgol_golay_filter(Y[maxidx], info='max')
                midY = tools.savgol_golay_filter(numpy.array(midY), info='mid')
                # min(Y) <= up, down, max, mid <= max(Y)
                ymin, ymax = Y.min(), Y.max()
                upY[upY > ymax] = ymax
                downY[downY < ymin] = ymin
                maxY[maxY > ymax] = ymax
                maxY[maxY < ymin] = ymin
                midY[midY > ymax] = ymax
                midY[midY < ymin] = ymin
        if smooth:
            meanZ = tools.savgol_golay_filter(meanZ, info='Z mean')
        if 'mean_select' not in self.kwoptions:
            self.kwoptions.update(dict(
                mean_select=dict(
                    widget='Dropdown',
                    options=['iflux', 'peak'],
                    value='iflux',
                    description='select mean:'),
                mean_iflux=dict(
                    widget='IntRangeSlider',
                    rangee=self.kwoptions['pcutoff']['rangee'].copy(),
                    value=iflux,
                    description='mean iflux:'),
                mean_peak_limit=dict(
                    widget='FloatSlider',
                    rangee=(0, 1, 0.05),
                    value=1.0/numpy.e,
                    description='mean peak limit:'),
                mean_peak_greedy=dict(widget='Checkbox',
                                      value=False,
                                      description='mean peak greedy'),
                mean_z_abs=dict(widget='Checkbox',
                                value=False,
                                description='mean z abs'),
                mean_smooth=dict(widget='Checkbox',
                                 value=True,
                                 description='mean smooth'),
                mean_z_weight_order=dict(widget='IntSlider',
                                         rangee=(0, 6, 1),
                                         value=0,
                                         description='mean z weight order:')
            ))
        acckwargs.update(dict(
            mean_select=select, mean_iflux=iflux,
            mean_peak_limit=peak_limit, mean_peak_greedy=peak_greedy,
            mean_z_abs=z_abs, mean_smooth=smooth,
            mean_z_weight_order=weight_order))
        results.update(dict(
            meanZ=meanZ, upY=upY, maxY=maxY, midY=midY, downY=downY))
        return results, acckwargs

    def _post_dig(self, results):
        r = results
        LINE = [(r['X'], r['downY'], 'down'), (r['X'], r['upY'], 'up')]
        if r['maxY'] is not None:
            LINE.insert(0, (r['X'], r['maxY'], 'max'))
        if r['midY'] is not None:
            LINE.insert(0, (r['X'], r['midY'], 'mean'))
        zip_results = [
            ('tmpl_contourf', 211, dict(
                X=r['X'], Y=r['Y'], Z=r['Z'], title=r['title'],
                xlabel=r'time($R_0/c_s$)', ylabel=r['ylabel'])),
            ('tmpl_line', 211, dict(LINE=LINE)),
            ('tmpl_line', 212, dict(
                LINE=[(r['X'], r['meanZ'], 'mean')],
                xlabel=r'time($R_0/c_s$)'))]
        return dict(zip_results=zip_results)


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
        self.kwoptions = None

    def _get_title(self):
        title = '%s %s flux' % (self.particle, self.section[2])
        if self.particle == 'ion':
            return 'thermal %s' % title
        elif self.particle == 'fastion':
            return title.replace('fastion', 'fast ion')
        else:
            return title


class Data1dMeanFluxDigger(_Data1dMeanDigger, Data1dFluxDigger):
    '''particle, energy and momentum mean flux of ion, electron, fastion.'''
    __slots__ = []

    def _set_fignum(self, numseed=None):
        super(Data1dMeanFluxDigger, self)._set_fignum(numseed=numseed)
        self._fignum = '%s_mean' % self._fignum


field_tex_str = {
    'phi': r'\phi',
    'apara': r'A_{\parallel}',
    'fluidne': r'fluid n_e'
}


class Data1dFieldDigger(_Data1dDigger):
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
        self.kwoptions = None

    def _get_title(self):
        if self.section[1] == '00':
            return self.fignum.replace('_', ' ')
        else:
            return r'$%s rms$' % field_tex_str[self.section[2]]


class Data1dMeanFieldDigger(_Data1dMeanDigger, Data1dFieldDigger):
    '''mean field00 and fieldrms of phi, a_para, fluidne'''
    __slots__ = []

    def _set_fignum(self, numseed=None):
        super(Data1dMeanFieldDigger, self)._set_fignum(numseed=numseed)
        self._fignum = '%s_mean' % self._fignum
