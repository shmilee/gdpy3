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

import numpy as np
from .. import tools
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog
from .gtc import Ndigits_tstep

_all_Converters = ['Data1dConverter']
_all_Diggers = ['Data1dFluxDigger', 'Data1dFieldDigger',
                'Data1dMeanFluxDigger', 'Data1dMeanFieldDigger',
                'Data1dFFTFieldDigger',
                'Data1dZFshearDigger', 'Data1dZFshearVSDigger']
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
    itemspattern = [r'^(?P<section>data1d)\.out$',
                    r'.*/(?P<section>data1d)\.out$']
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
        outdata = np.array([float(n.strip()) for n in outdata[7:]])
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
        X, Y = np.arange(1, x + 1) * dt, np.arange(0, y)
        X = np.around(X, 8)
        if self.kwoptions is None:
            self.kwoptions = dict(
                tcutoff=dict(widget='FloatRangeSlider',
                             rangee=[X[0], X[-1], np.around(dt*7, 8)],
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
            index = np.where((X >= t0) & (X < t1 + dt))[0]
            if index.size > 0:
                x0, x1 = index[0], index[-1]+1
                acckwargs['tcutoff'] = [X[x0], X[x1-1]]
                X = X[x0:x1]
            else:
                dlog.warning('Cannot cutoff: %s <= time <= %s!' % (t0, t1))
        y0, y1 = 0, Y.size
        if 'pcutoff' in kwargs:
            p0, p1 = kwargs['pcutoff']
            index = np.where((Y >= p0) & (Y < p1+1))[0]
            if index.size > 0:
                y0, y1 = index[0], index[-1]+1
                acckwargs['pcutoff'] = [Y[y0], Y[y1-1]]
                Y = Y[y0:y1]
            else:
                dlog.warning('Cannot cutoff: %s <= ipsi <= %s!' % (p0, p1))
        ylabel = r'$\psi$(mpsi)'
        cutoff_idx = [y0, y1, x0, x1]
        # use_ra, by rpsi
        if kwargs.get('use_ra', False):
            try:
                rpsi, a = self.pckloader.get_many('gtc/sprpsi', 'gtc/a_minor')
                rr = rpsi / a
                Y = rr[y0:y1]
            except Exception:
                dlog.warning("Cannot use r/a!", exc_info=1)
            else:
                ylabel = r'$r/a$'
                acckwargs['use_ra'] = True
        # update
        data = data[y0:y1, x0:x1]
        return dict(X=X, Y=Y, Z=data, cutoff_idx=cutoff_idx,
                    title=self._get_title(),
                    ylabel=ylabel, xlabel=r'time($R_0/c_s$)'), acckwargs

    def _post_dig(self, results):
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
        index = np.where((X >= mt0) & (X <= mt1))[0]
        if index.size > 0:
            start, end = index[0], index[-1]
        else:
            dlog.warning('Cannot set mean time: %s <= t <= %s!' % (mt0, mt1))
            start, end = int(len(X)*0.7), len(X)-1
        mt0, mt1 = X[start], X[end]
        dlog.parm("Set mean time: [%s,%s], index: [%s,%s]."
                  % (X[start], X[end], start, end))
        selectZ = Z[:, start:end]
        meanZ = np.average(selectZ, axis=1)
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
    :meth:`_dig` for Data1dFFTFluxDigger (ignore), Data1dFFTFieldDigger
    '''
    __slots__ = []
    post_template = ('tmpl_z111p', 'tmpl_contourf', 'tmpl_line')

    def _dig(self, kwargs):
        '''*fft_tselect*: [t0,t1], t0 float
            X[x0:x1], data[:,x0:x1] where t0<=X[x0:x1]<=t1
        *fft_pselect*: [p0,p1], p0 int
            Y[y0:y1], data[y0:y1,:] where p0<=Y[y0:y1]<=p1
        *fft_unit_rho0*: bool
            normalize FFT kr by rho0 or not, default True
        *fft_autoxlimit*: bool
            auto set short xlimt for FFT results or not, default True
        *fft_mean_krlimit*: tuple of float, (%.2f, %.2f)
            set |kr| (or |kr*rho0|) limit to average, default (0, max(|kr|))
        *fft_mean_order*: int
            use |field_k|^fft_mean_order as weight to average(|kr|), default 2
        '''
        results, acckwargs = super(_Data1dFFTDigger, self)._dig(kwargs)
        X, Y, Z = results['X'], results['Y'], results['Z']
        tcutoff = acckwargs['tcutoff']
        pcutoff = acckwargs['pcutoff']
        use_ra = acckwargs['use_ra']
        fft_tselect = kwargs.get('fft_tselect', tcutoff)
        fft_pselect = kwargs.get('fft_pselect', pcutoff)
        fft_unit_rho0 = kwargs.get('fft_unit_rho0', True)
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
                    value=True,
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
            index = np.where((X >= s0) & (X <= s1))[0]
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
            pY = np.arange(pcutoff[0], pcutoff[1]+1)
            if use_ra and pY.size != Y.size:
                dlog.error("Wrong pY size: %d != %d" % (pY.size, Y.size))
            index = np.where((pY >= s0) & (pY <= s1))[0]
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
        dy = np.diff(Y).mean() if use_ra else 1.0
        tf, yf, af, pf = tools.fft2(dt, dy, select_Z)
        M, N = select_Z.shape
        pf = pf / M / N * 2.0
        # yf unit
        acckwargs['fft_unit_rho0'] = False
        yf_label = r'$k_r$(1/a)' if use_ra else r'$k_r$(1/mpsi)'
        if fft_unit_rho0:
            try:
                a, rho0 = self.pckloader.get_many('gtc/a_minor', 'gtc/rho0')
                if not use_ra:
                    rpsi = self.pckloader['gtc/sprpsi']
                    yf = yf/np.diff(rpsi).mean() * a
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
            idx_t = np.where(pf_tmax >= minlimit)[0][-1]
            idx_y = np.where(pf_ymax >= minlimit)[0][-1]
            tf_xlimit, yf_xlimit = round(tf[idx_t], 3),  round(yf[idx_y], 3)
        else:
            acckwargs['fft_autoxlimit'] = False
            tf_xlimit, yf_xlimit = None, None
        # yf average
        mean_krlimit = kwargs.get('fft_mean_krlimit', (0, yf[-1]))
        mean_order = kwargs.get('fft_mean_order', 2)
        mean_kr = 0.0
        krlim0, krlim1 = round(mean_krlimit[0], 2), round(mean_krlimit[1], 2)
        mean_krlimit = krlim0, krlim1
        i0, i1 = np.where((krlim0 <= yf) & (yf <= krlim1))[0][[0, -1]]
        weights = abs(pf_ymax[i0:i1+1])**mean_order
        if sum(weights) != 0:
            mean_kr = np.average(abs(yf[i0:i1+1]), weights=weights)
        acckwargs.update(
            fft_mean_krlimit=mean_krlimit, fft_mean_order=mean_order)
        if 'fft_mean_krlimit' not in self.kwoptions:
            self.kwoptions.update(
                fft_mean_krlimit=dict(widget='FloatRangeSlider',
                                      rangee=(0.0, round(yf[-1], 2), 0.05),
                                      value=mean_krlimit,
                                      description='mean kr limit:'),
                fft_mean_order=dict(widget='IntSlider',
                                    rangee=(2, 8, 2),
                                    value=2,
                                    description='mean kr weight order:'))
        results.update(
            select_X=select_X, select_Y=select_Y,
            tf=tf, yf=yf, pf=pf,
            tf_label=r'$\omega$($c_s/R_0$)', yf_label=yf_label,
            pf_tmax=pf_tmax, pf_ymax=pf_ymax,
            tf_xlimit=tf_xlimit, yf_xlimit=yf_xlimit,
            mean_krlimit=mean_krlimit, mean_kr=mean_kr, mean_order=mean_order,
        )
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
        (krlim0, krlim1), kr = r['mean_krlimit'], r['mean_kr']
        lineY = [0, r['pf_ymax'].max()]
        meaneq = r'$\langle|$%s$|\rangle_{|f00_k|^%d}$=' % (
            r['yf_label'], r['mean_order'])
        zip_results.extend([
            ('tmpl_line', 223, dict(
                LINE=[(r['tf'], r['pf_tmax'], r'max(axis=$k_r$)')],
                xlabel=r['tf_label'], xlim=[-tf_xlimit, tf_xlimit])),
            ('tmpl_line', 224, dict(
                LINE=[(r['yf'], r['pf_ymax'], r'max(axis=$\omega$)'),
                      ([krlim0, krlim0], lineY, r'mean limit0=%s' % krlim0),
                      ([krlim1, krlim1], lineY, r'mean limit1=%s' % krlim1),
                      ([kr, kr], lineY, r'%s=%.6f' % (meaneq, kr))],
                xlabel=r['yf_label'], xlim=[-yf_xlimit, yf_xlimit])),
        ])
        return dict(zip_results=zip_results)


class Data1dFFTFieldDigger(_Data1dFFTDigger, Data1dFieldDigger):
    '''FFT field00 and fieldrms of phi, a_para, fluidne'''
    __slots__ = []

    def _set_fignum(self, numseed=None):
        super(Data1dFFTFieldDigger, self)._set_fignum(numseed=numseed)
        self._fignum = '%s_fft' % self._fignum


class Data1dZFshearDigger(_Data1dDigger):
    '''Zonal flow shear rate by phi00, normalized by c_sH/R_0.'''
    __slots__ = []
    itemspattern = ['^(?P<s>data1d)/field00-phi']
    commonpattern = ['gtc/tstep', 'gtc/ndiag', 'gtc/sprpsi', 'gtc/rho0']
    post_template = ('tmpl_z111p', 'tmpl_contourf', 'tmpl_line')

    def _set_fignum(self, numseed=None):
        self._fignum = 'zonal_shear'
        self.kwoptions = None

    def _get_title(self):
        return self._fignum

    def _dig(self, kwargs):
        '''*meanra*: [r0,r1], float
            When use_ra=True, RMS shearZF[y0:y1,:] where r0<=rr[y0:y1]/a<=r1
        '''
        results, acckwargs = super(Data1dZFshearDigger, self)._dig(kwargs)
        time, Y, ZF = results.pop('X'), results.pop('Y'), results.pop('Z')
        rpsi, rho0 = self.pckloader.get_many(*self.extrakeys[-2:])
        y0, y1, _, _ = results['cutoff_idx']
        rpsi = rpsi[y0:y1]
        EZF = np.divide(np.gradient(ZF, axis=0).T, np.gradient(rpsi)).T
        shearZF = np.divide(np.gradient(EZF, axis=0).T, np.gradient(rpsi)).T
        shearZF = rho0 * shearZF  # c_sH/R_0
        shearZFrms = None
        pcut0, pcut1 = acckwargs['pcutoff']
        meanYcut = None
        meanYindex = 0, Y.size
        if 'meanra' in kwargs and kwargs.get('use_ra', False):
            rr = Y
            r0, r1 = kwargs['meanra']
            index = np.where((rr >= r0) & (rr < r1))[0]
            if index.size > 0:
                pi0, pi1 = index[0], index[-1]+1
                shearZFrms = np.sqrt(np.mean(shearZF[pi0:pi1, :]**2, axis=0))
                acckwargs['meanra'] = [rr[pi0], rr[pi1-1]]
                meanYcut = [Y[pi0], Y[pi1-1]]
                meanYindex = (pi0, pi1)
                dlog.info('shear RMS mean between: %s<r/a<%s' % (*meanYcut,))
            else:
                dlog.warning('Invalid meanra: %s <= r/a <= %s!' % (r0, r1))
        else:
            dlog.warning("Not use meanra or use_ra=False!")
        if shearZFrms is None:
            shearZFrms = np.sqrt(np.mean(shearZF**2, axis=0))
            acckwargs['meanra'] = [0, 1]
        if 'meanra' not in self.kwoptions:
            self.kwoptions['meanra'] = dict(
                widget='FloatRangeSlider',
                rangee=[0.0, 1.0, 0.05],
                value=[0.0, 1.0],
                description='shear meanra:')
        results.update(
            time=time, Y=Y, ZF=ZF, EZF=EZF, shearZF=shearZF,
            shearZFrms=shearZFrms, meanYcut=meanYcut, meanYindex=meanYindex)
        return results, acckwargs

    def _post_dig(self, results):
        r = results
        ax1 = dict(
            X=r['time'], Y=r['Y'], Z=r['ZF'], title=r'$\phi_{00}$',
            xlabel=r['xlabel'], ylabel=r['ylabel'])
        ax2 = dict(
            X=r['time'], Y=r['Y'], Z=r['EZF'], title=r'$E_{r,00}$',
            xlabel=r['xlabel'], ylabel=r['ylabel'])
        ax3 = dict(
            X=r['time'], Y=r['Y'], Z=r['shearZF'], title=r'$ZF_{shear}$',
            xlabel=r['xlabel'], ylabel=r['ylabel'])
        ax4 = dict(
            LINE=[(r['time'], r['shearZFrms'], 'shear RMS')],
            title='RMS of zonal shear rate', xlabel=r['xlabel'])
        zip_results = [
            ('tmpl_contourf', 221, ax1), ('tmpl_contourf', 222, ax2),
            ('tmpl_contourf', 223, ax3), ('tmpl_line', 224, ax4)]
        if r['meanYcut'] is not None:
            t0, t1 = r['time'][0], r['time'][-1]
            Y0, Y1 = r['meanYcut']
            zip_results.append(
                ('tmpl_line', 223, dict(LINE=[
                    ([t0, t1, t1, t0, t0], [Y0, Y0, Y1, Y1, Y0], r'RMS'),
                ])))
        return dict(zip_results=zip_results)


class Data1dZFshearVSDigger(Data1dZFshearDigger):
    '''Zonal flow shear rate vs gamma of phirms, particle chi.'''
    __slots__ = []
    nitems = '+'
    itemspattern = ['^(?P<s>data1d)/field00-phi',
                    '^(?P<s>data1d)/fieldrms-phi',
                    '^(?P<s>data1d)/i-energy-flux']

    def _set_fignum(self, numseed=None):
        self._fignum = 'zonal_shear_vs'
        self.kwoptions = None

    def _dig(self, kwargs):
        '''*particle*: str, default 'i'
            chi_rms of 'i':ion, 'e':electron or 'f':fastion
        '''
        results, acckwargs = super(Data1dZFshearVSDigger, self)._dig(kwargs)
        time, Y = results['time'], results['Y']
        shearZF, shearZFrms = results['shearZF'], results['shearZFrms']
        cutoff_idx = results['cutoff_idx']
        mp0, mp1 = results['meanYindex']
        particle = None
        if 'particle' in kwargs and kwargs['particle'] in ('i', 'e', 'f'):
            if 'data1d/%s-energy-flux' % kwargs['particle'] in self.pckloader:
                particle = kwargs['particle']
            else:
                dlog.warning('particle %s not found!' % kwargs['particle'])
        if particle:
            key = 'data1d/%s-energy-flux' % particle
        else:
            particle, key = 'i', 'data1d/i-energy-flux'
        dlog.warning('Use chi rms of particle %s.' % particle)
        acckwargs['particle'] = particle
        if 'particle' not in self.kwoptions:
            self.kwoptions['particle'] = dict(
                widget='Dropdown',
                options=['i', 'e', 'f'],
                value='i',
                description='particle:')
        phirms = self.pckloader.get('data1d/fieldrms-phi')
        chi = self.pckloader.get(key)
        y0, y1, x0, x1 = cutoff_idx
        cutphirms = phirms[y0:y1, x0:x1]
        cutchi = chi[y0:y1, x0:x1]
        meanphirms = np.sqrt(np.mean(phirms[mp0:mp1, x0:x1]**2, axis=0))
        meanchi = np.sqrt(np.mean(chi[mp0:mp1, x0:x1]**2, axis=0))
        gammaphirms = np.gradient(np.log(meanphirms)) / np.gradient(time)
        gammachi = np.gradient(np.log(meanchi)) / np.gradient(time)
        results.update(particle=particle, phirms=cutphirms, chi=cutchi,
                       gammaphirms=gammaphirms, gammachi=gammachi)
        return results, acckwargs

    def _post_dig(self, results):
        r = results
        ax1 = dict(
            X=r['time'], Y=r['Y'], Z=r['shearZF'], title=r'$ZF_{shear}$',
            xlabel=r['xlabel'], ylabel=r['ylabel'])
        ax2 = dict(
            X=r['time'], Y=r['Y'], Z=r['phirms'], title=r'$\phi_{RMS}$',
            xlabel=r['xlabel'], ylabel=r['ylabel'])
        ax3 = dict(
            X=r['time'], Y=r['Y'], Z=r['chi'],
            title=r'$\chi_{%s}$' % r['particle'],
            xlabel=r['xlabel'], ylabel=r['ylabel'])
        tex = r'$ZF_{shear}$ vs $\gamma_{\phi}, \chi_{%s}$' % r['particle']
        ax4 = dict(
            LINE=[
                (r['time'], r['shearZFrms'], 'ZF shear'),
                (r['time'], r['gammaphirms'], r'$\gamma_{\phi}$'),
                (r['time'], r['gammachi'], r'$dln\chi/dt$'),
            ],
            title=r'RMS: %s' % tex,
            xlabel=r['xlabel'])
        zip_results = [
            ('tmpl_contourf', 221, ax1), ('tmpl_contourf', 222, ax2),
            ('tmpl_contourf', 223, ax3), ('tmpl_line', 224, ax4)]
        if r['meanYcut'] is not None:
            t0, t1 = r['time'][0], r['time'][-1]
            Y0, Y1 = r['meanYcut']
            ax99 = dict(LINE=[
                ([t0, t1, t1, t0, t0], [Y0, Y0, Y1, Y1, Y0], r'RMS mean')
            ])
            zip_results.extend([
                ('tmpl_line', 221, ax99),
                ('tmpl_line', 222, ax99),
                ('tmpl_line', 223, ax99),
            ])
        return dict(zip_results=zip_results)
