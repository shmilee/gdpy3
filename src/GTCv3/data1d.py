# -*- coding: utf-8 -*-

# Copyright (c) 2019-2021 shmilee

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
from .gtc import Ndigits_tstep

_all_Converters = ['Data1dConverter']
_all_Diggers = ['Data1dFluxDigger', 'Data1dFieldDigger',
                'Data1dMeanFluxDigger', 'Data1dMeanFieldDigger',
                'Data1dFFTFieldDigger']
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
            self.srckeys[0], *self.extrakeys[:2])
        tstep = round(tstep, Ndigits_tstep)
        y, x = data.shape
        dt = tstep * ndiag
        X, Y = numpy.arange(1, x + 1) * dt, numpy.arange(0, y)
        X = numpy.around(X, 8)
        if self.kwoptions is None:
            self.kwoptions = dict(
                tcutoff=dict(widget='FloatRangeSlider',
                             rangee=[X[0], X[-1], 1.0],
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

    def _get_title(self):
        raise NotImplementedError()


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
            return 'zonal %s' % self.__cnames[self.section[2]]
        else:
            return r'$%s rms$' % field_tex_str[self.section[2]]


class _Data1dMeanDigger(_Data1dDigger):
    '''
    :meth:`_dig` for Data1dMeanFluxDigger, Data1dMeanFieldDigger
    '''
    __slots__ = []
    post_template = ('tmpl_z111p', 'tmpl_contourf', 'tmpl_line')

    def _dig(self, kwargs):
        '''*mean_time*: [t0, t1], float
            mean data[:,x0:x1] where t0<=time[x0:x1]<=t1
            default t0, t1 = time[-1]*0.7, time[-1]
        *mean_smooth*: bool
            smooth results or not, default False
        '''
        results, acckwargs = super(_Data1dMeanDigger, self)._dig(kwargs)
        X, Y, Z = results['X'], results['Y'], results['Z']
        t0, t1 = acckwargs['tcutoff']
        use_ra = acckwargs['use_ra']
        mt0, mt1 = kwargs.get('mean_time', [X[-1]*0.7, X[-1]])
        smooth = bool(kwargs.get('mean_smooth', False))
        index = numpy.where((X >= mt0) & (X <= mt1))[0]
        if index.size > 0:
            start, end = index[0], index[-1]
        else:
            dlog.warning('Cannot set mean time: %s <= t <= %s!' % (mt0, mt1))
            start, end = int(len(X)*0.7), len(X)-1
        mt0, mt1 = X[start], X[end]
        dlog.parm("Set mean time: [%s,%s], index: [%s,%s]."
                  % (X[start], X[end], start, end))
        selectZ = Z[:, start:end]
        meanZ = numpy.average(selectZ, axis=1)
        if smooth:
            meanZ = tools.savgolay_filter(meanZ, info='Z mean')
        if 'mean_time' not in self.kwoptions:
            self.kwoptions.update(dict(
                mean_time=dict(
                    widget='FloatRangeSlider',
                    rangee=self.kwoptions['tcutoff']['rangee'].copy(),
                    value=[mt0, mt1],
                    description='mean time:'),
                mean_smooth=dict(widget='Checkbox',
                                 value=False,
                                 description='mean smooth'),
            ))
        acckwargs.update(dict(mean_time=[mt0, mt1], mean_smooth=smooth))
        results.update(dict(mean_time=[mt0, mt1], meanZ=meanZ))
        return results, acckwargs

    def _post_dig(self, results):
        r = results
        mt0, mt1 = r['mean_time']
        LINE = [([mt0, mt0], r['Y'][[0, -1]], 'mean t0'),
                ([mt1, mt1], r['Y'][[0, -1]], 'mean t1')]
        zip_results = [
            ('tmpl_contourf', 121, dict(
                X=r['X'], Y=r['Y'], Z=r['Z'], title=r['title'],
                xlabel=r'time($R_0/c_s$)', ylabel=r['ylabel'])),
            ('tmpl_line', 121, dict(LINE=LINE)),
            ('tmpl_line', 122, dict(
                LINE=[(r['meanZ'], r['Y'], 'mean')],
                ylim=[r['Y'][0], r['Y'][-1]], ylabel=r['ylabel'],
                xlabel=r'mean Z'))]
        return dict(zip_results=zip_results)


class Data1dMeanFluxDigger(_Data1dMeanDigger, Data1dFluxDigger):
    '''particle, energy and momentum mean flux of ion, electron, fastion.'''
    __slots__ = []

    def _set_fignum(self, numseed=None):
        super(Data1dMeanFluxDigger, self)._set_fignum(numseed=numseed)
        self._fignum = '%s_mean' % self._fignum


class Data1dMeanFieldDigger(_Data1dMeanDigger, Data1dFieldDigger):
    '''mean field00 and fieldrms of phi, a_para, fluidne'''
    __slots__ = []

    def _set_fignum(self, numseed=None):
        super(Data1dMeanFieldDigger, self)._set_fignum(numseed=numseed)
        self._fignum = '%s_mean' % self._fignum


class _Data1dFFTDigger(_Data1dDigger):
    '''
    :meth:`_dig` for Data1dFFTFluxDigger, Data1dFFTFieldDigger
    '''
    __slots__ = []
    post_template = ('tmpl_z111p', 'tmpl_line')

    def _dig(self, kwargs):
        '''*fft_tselect*: [t0,t1], t0 float
            X[x0:x1], data[:,x0:x1] where t0<=X[x0:x1]<=t1
        *fft_pselect*: [p0,p1], p0 int
            Y[y0:y1], data[y0:y1,:] where p0<=Y[y0:y1]<=p1
        *fft_unit_rho0*: bool
            set Y unit of FFT results to rho0 or not, default False
        *fft_autoxlimit*: bool
            auto set short xlimt for FFT results or not, default True
        '''
        results, acckwargs = super(_Data1dFFTDigger, self)._dig(kwargs)
        X, Y, Z = results['X'], results['Y'], results['Z']
        tcutoff = acckwargs['tcutoff']
        pcutoff = acckwargs['pcutoff']
        use_ra = acckwargs['use_ra']
        fft_tselect = kwargs.get('fft_tselect', tcutoff)
        fft_pselect = kwargs.get('fft_pselect', pcutoff)
        fft_unit_rho0 = kwargs.get('fft_unit_rho0', False)
        fft_autoxlimit = kwargs.get('fft_autoxlimit', True)
        if 'fft_tselect' not in self.kwoptions:
            self.kwoptions.update(dict(
                fft_tselect=dict(
                    widget='FloatRangeSlider',
                    rangee=self.kwoptions['tcutoff']['rangee'].copy(),
                    value=self.kwoptions['tcutoff']['value'].copy(),
                    description='FFT time select:'),
                fft_pselect=dict(
                    widget='IntRangeSlider',
                    rangee=self.kwoptions['pcutoff']['rangee'].copy(),
                    value=self.kwoptions['pcutoff']['value'].copy(),
                    description='FFT mpsi select:'),
                fft_unit_rho0=dict(
                    widget='Checkbox',
                    value=False,
                    description='FFT unit rho0'),
                fft_autoxlimit=dict(
                    widget='Checkbox',
                    value=True,
                    description='FFT xlimit: auto'),
            ))
        # fft_tselect
        it0, it1, dt = 0, X.size, X[1] - X[0]
        acckwargs['fft_tselect'] = tcutoff
        if (fft_tselect != tcutoff
                and (fft_tselect[0] >= tcutoff[0]
                     or fft_tselect[1] <= tcutoff[1])):
            s0, s1 = fft_tselect
            index = numpy.where((X >= s0) & (X <= s1))[0]
            if index.size > 0:
                it0, it1 = index[0], index[-1]+1
                acckwargs['fft_tselect'] = [X[it0], X[it1-1]]
            else:
                dlog.warning("Can't select: %s <= fft time <= %s!" % (s0, s1))
        # fft_pselect
        ip0, ip1 = 0, Y.size
        acckwargs['fft_pselect'] = pcutoff
        if (fft_pselect != pcutoff
                and fft_pselect[0] >= pcutoff[0]
                and fft_pselect[1] <= pcutoff[1]):
            s0, s1 = fft_pselect
            pY = numpy.arange(pcutoff[0], pcutoff[1]+1)
            if use_ra and pY.size != Y.size:
                # arr2 lost 2 points
                if pY.size - Y.size == 1:
                    pY = pY[1:] if pcutoff[0] == 0 else pY[:-1]
                elif pY.size - Y.size == 2:
                    pY = pY[1:-1]
                else:
                    dlog.error("Wrong pY size: %d != %d" % (pY.size, Y.size))
            index = numpy.where((pY >= s0) & (pY <= s1))[0]
            if index.size > 0:
                ip0, ip1 = index[0], index[-1]+1
                acckwargs['fft_pselect'] = [pY[ip0], pY[ip1-1]]
            else:
                dlog.warning("Can't select: %s <= fft ipsi <= %s!" % (s0, s1))
        # select FFT data
        if (it0, it1) == (0, X.size) and (ip0, ip1) == (0, Y.size):
            select_Z = Z
            select_X, select_Y = None, None
        else:
            select_Z = Z[ip0:ip1, it0:it1]
            select_X = X[[it0, it1-1, it1-1, it0, it0]]
            select_Y = Y[[ip0, ip0, ip1-1, ip1-1, ip0]]
        dy = numpy.diff(Y).mean() if use_ra else 1.0
        tf, yf, af, pf = tools.fft2(dt, dy, select_Z)
        # yf unit
        acckwargs['fft_unit_rho0'] = False
        yf_label = r'$k_r$(1/a)' if use_ra else r'$k_r$(1/mpsi)'
        if fft_unit_rho0:
            try:
                a, rho0 = self.pckloader.get_many('gtc/a_minor', 'gtc/rho0')
                if not use_ra:
                    arr2 = self.pckloader.get('gtc/arr2')
                    yf = yf/numpy.diff(arr2[:, 1]).mean() * a
                yf = yf*rho0/a
            except Exception:
                dlog.warning("Cannot use unit rho0!", exc_info=1)
            else:
                yf_label = r'$k_r\rho_0$'
                acckwargs['fft_unit_rho0'] = True
        # max line
        pf_tmax = pf.max(axis=0)
        pf_ymax = pf.max(axis=1)
        pf_max = pf_tmax.max()
        # tf, yf xlimit
        if fft_autoxlimit:
            acckwargs['fft_autoxlimit'] = True
            minlimit = pf_max * 5.0e-2
            idx_t = numpy.where(pf_tmax >= minlimit)[0][-1]
            idx_y = numpy.where(pf_ymax >= minlimit)[0][-1]
            tf_xlimit, yf_xlimit = round(tf[idx_t], 3),  round(yf[idx_y], 3)
        else:
            acckwargs['fft_autoxlimit'] = False
            tf_xlimit, yf_xlimit = None, None
        results.update(dict(
            select_X=select_X, select_Y=select_Y,
            tf=tf, yf=yf, pf=pf,
            tf_label=r'$\omega$($c_s/R_0$)', yf_label=yf_label,
            pf_tmax=pf_tmax, pf_ymax=pf_ymax,
            tf_xlimit=tf_xlimit, yf_xlimit=yf_xlimit,
        ))
        return results, acckwargs

    def _post_dig(self, results):
        r = results
        zip_results = [('tmpl_contourf', 221, dict(
            X=r['X'], Y=r['Y'], Z=r['Z'], title=r['title'],
            xlabel=r'time($R_0/c_s$)', ylabel=r['ylabel']))]
        if r['select_X'] is not None:
            zip_results.append(
                ('tmpl_line', 221, dict(
                    LINE=[(r['select_X'], r['select_Y'], 'FFT region')]))
                # legend_kwargs=dict(loc='upper left'),
            )
        title2 = r'FFT of %s' % r['title']
        if r['tf_xlimit']:
            tf_xlimit, yf_xlimit = r['tf_xlimit'], r['yf_xlimit']
            tf_xlimit2 = min(tf_xlimit*2.0, r['tf'][-1])
            yf_xlimit2 = min(yf_xlimit*2.0, r['yf'][-1])
        else:
            tf_xlimit, yf_xlimit = r['tf'][-1], r['yf'][-1]
            tf_xlimit2, yf_xlimit2 = tf_xlimit, yf_xlimit
        zip_results.append(
            ('tmpl_contourf', 222, dict(
                X=r['tf'], Y=r['yf'], Z=r['pf'], title=title2,
                xlabel=r['tf_label'], ylabel=r['yf_label'],
                xlim=[-tf_xlimit2, tf_xlimit2],
                ylim=[-yf_xlimit2, yf_xlimit2]))
        )
        zip_results.extend([
            ('tmpl_line', 223, dict(
                LINE=[(r['tf'], r['pf_tmax'], 'max')], xlabel=r['tf_label'],
                xlim=[-tf_xlimit, tf_xlimit])),
            ('tmpl_line', 224, dict(
                LINE=[(r['yf'], r['pf_ymax'], 'max')], xlabel=r['yf_label'],
                xlim=[-yf_xlimit, yf_xlimit])),
        ])
        return dict(zip_results=zip_results)


class Data1dFFTFieldDigger(_Data1dFFTDigger, Data1dFieldDigger):
    '''FFT field00 and fieldrms of phi, a_para, fluidne'''
    __slots__ = []

    def _set_fignum(self, numseed=None):
        super(Data1dFFTFieldDigger, self)._set_fignum(numseed=numseed)
        self._fignum = '%s_fft' % self._fignum
