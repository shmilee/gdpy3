# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

'''
Source fortran code:

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

import numpy as np

from .. import tools
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog

__all__ = ['HistoryConverter', 'HistoryParticleDigger',
           'HistoryFieldDigger', 'HistoryFieldModeDigger']


class HistoryConverter(Converter):
    '''
    History Data

    1) density,entropy,flow,energy,fluxes of particle,momentum,heat
       Source: diagion, diagelectron, diagfast.
       The particle 2d array is particle[mpdiag,time].
    2) time history of field quantity at theta=zeta=0 & i=iflux
       Source: fieldtime, fieldmode: phi, a_para, fluid_ne
       The fieldtime 2d array is fieldtime[mfdiag,time].
       The fieldmode 2d array is fieldmode[modes,time].
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = ['^(?P<section>history)\.out$',
                    '.*/(?P<section>history)\.out$']
    _datakeys = (
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

    def _convert(self):
        '''Read 'history.out'.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        # 1. diagnosis.F90:opendiag():734-735
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:7]))
        for i, key in enumerate(self._datakeys[:6]):
            sd.update({key: int(outdata[i].strip())})
        # 1. tstep*ndiag
        sd.update({'tstep*ndiag': float(outdata[6].strip())})

        # 2. diagnosis.F90:opendiag():729::
        outdata = np.array([float(n.strip()) for n in outdata[7:]])
        ndata = sd['nspecies'] * sd['mpdiag'] + \
            sd['nfield'] * (2 * sd['modes'] + sd['mfdiag'])
        if len(outdata) // ndata != sd['ndstep']:
            ndstep = len(outdata) // ndata
            clog.debug("Updating datakey: %s=%d ..." % ('ndstep', ndstep))
            sd.update({'ndstep': len(outdata) // ndata})
            outdata = outdata[:sd['ndstep'] * ndata]

        # reshape outdata
        outdata = outdata.reshape((ndata, sd['ndstep']), order='F')

        # 3. partdata(mpdiag,nspecies)
        clog.debug("Filling datakey: %s ..." % 'ion')
        sd.update({'ion': outdata[:sd['mpdiag'], :]})
        if sd['nspecies'] > 1:
            clog.debug("Filling datakey: %s ..." % 'electron')
            index0, index1 = sd['mpdiag'], 2 * sd['mpdiag']
            sd.update({'electron': outdata[index0:index1, :]})
        if sd['nspecies'] > 2:
            clog.debug("Filling datakey: %s ..." % 'fastion')
            index0, index1 = 2 * sd['mpdiag'], 3 * sd['mpdiag']
            sd.update({'fastion': outdata[index0:index1, :]})

        # 4. fieldtime(mfdiag,nfield)
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[10:13]))
        index0 = sd['nspecies'] * sd['mpdiag']
        index1 = index0 + sd['mfdiag']
        sd.update({'fieldtime-phi': outdata[index0:index1, :]})
        index0, index1 = index1, index1 + sd['mfdiag']
        sd.update({'fieldtime-apara': outdata[index0:index1, :]})
        index0, index1 = index1, index1 + sd['mfdiag']
        sd.update({'fieldtime-fluidne': outdata[index0:index1, :]})

        # 5. fieldmode(2,modes,nfield)
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[13:]))
        index0, index1 = index1, index1 + 2 * sd['modes']
        sd.update({'fieldmode-phi-real': outdata[index0:index1:2, :]})
        sd.update({'fieldmode-phi-imag': outdata[index0 + 1:index1:2, :]})
        index0, index1 = index1, index1 + 2 * sd['modes']
        sd.update({'fieldmode-apara-real': outdata[index0:index1:2, :]})
        sd.update({'fieldmode-apara-imag': outdata[index0 + 1:index1:2, :]})
        index0, index1 = index1, index1 + 2 * sd['modes']
        sd.update({'fieldmode-fluidne-real': outdata[index0:index1:2, :]})
        sd.update({'fieldmode-fluidne-imag': outdata[index0 + 1:index1:2, :]})

        return sd


class HistoryParticleDigger(Digger):
    '''
    ion, electron, fastion history
    1. density, entropy, flow, energy
    2. fluxes of particle, momentum, heat
    '''
    __slots__ = []
    itemspattern = ['^(?P<s>history)/(?P<particle>(?:ion|electron|fastion))$']
    commonpattern = ['history/ndstep', 'gtc/tstep', 'gtc/ndiag']
    numseeds = ['', '_flux']
    post_template = 'tmpl_sharextwinx'

    def _set_fignum(self, numseed=None):
        self._fignum = ''.join((self.section[1], numseed))

    def _dig(self, **kwargs):
        data, ndstep, tstep, ndiag = self.pckloader.get_many(
            self.srckeys[0], *self.extrakeys)
        if self.fignum == self.section[1]:
            return dict(
                time=np.arange(1, ndstep + 1) * tstep * ndiag,
                density=data[0],
                entropy=data[1],
                flow=data[2],
                deltau=data[3],
                energy=data[4],
                deltaE=data[5],
                title='particle %s' % self.fignum), {}
        else:
            # flux
            return dict(
                time=np.arange(1, ndstep + 1) * tstep * ndiag,
                particle=data[6],
                momentum=data[7],
                energy=data[8],
                title='particle %s' % self.fignum), {}

    def _post_dig(self, results):
        r = results
        if self.fignum == self.section[1]:
            YINFO = [{
                'left': [(r['density'], r'density $\delta f$')],
                'right': [(r['entropy'], r'entropy $\delta f^2$')],
                'lylabel': r'$\delta f$', 'rylabel': r'$\delta f^2$',
            }, {
                'left': [(r['flow'], r'flow u')],
                'right': [(r['deltau'], r'$\delta u$')],
                'lylabel': '$u$', 'rylabel': r'$\delta u$',
            }, {
                'left': [(r['energy'], r'energy $E-1.5$')],
                'right': [(r['deltaE'], r'entropy $\delta E$')],
                'lylabel': r'$E$', 'rylabel': r'$\delta E$',
            }]
        else:
            YINFO = [{'left': [(r['particle'], 'particle flux')], 'right': []},
                     {'left': [(r['momentum'], 'momentum flux')], 'right': []},
                     {'left': [(['energy'], 'energy flux')], 'right': []}]
        return dict(X=r['time'], YINFO=YINFO, title=r['title'],
                    xlabel=r'time($R_0/c_s$)', xlim=[0, np.max(r['time'])])


field_tex_str = {
    'phi00': r'\phi_{p00}',
    'phi': r'\phi',
    'apara00': r'A_{\parallel 00}',
    'apara': r'A_{\parallel}',
    'fluidne00': r'fluidne_{00}',
    'fluidne': r'fluidne'
}


class HistoryFieldDigger(Digger):
    '''phi, apara, fluidne history'''
    __slots__ = ['_fstr']
    itemspattern = [r'^(?P<s>history)/fieldtime-' +
                    '(?P<field>(?:phi|apara|fluidne))$']
    commonpattern = ['history/ndstep', 'gtc/tstep', 'gtc/ndiag']
    post_template = 'tmpl_sharextwinx'

    def _set_fignum(self, numseed=None):
        self._fignum = self.section[1]
        self._fstr = field_tex_str[self._fignum]

    def _dig(self, **kwargs):
        data, ndstep, tstep, ndiag = self.pckloader.get_many(
            self.srckeys[0], *self.extrakeys)
        return dict(
            time=np.arange(1, ndstep + 1) * tstep * ndiag,
            field=data[0],
            field00=data[1],
            field00rms=data[2],
            fieldrms=data[3],
            title=r'$%s (\theta=\zeta=0), %s00 (i=iflux)$' % (
                self._fstr, self._fstr)
        ), {}

    def _post_dig(self, results):
        r = results
        YINFO = [{'left': [(r['field'], '$%s$' % self._fstr)],
                  'right': [(r['fieldrms'], '$%s RMS$' % self._fstr)],
                  'lylabel': '$%s$' % self._fstr, 'rylabel': '$RMS$', },
                 {'left': [(r['field00'], '$%s00$' % self._fstr)],
                  'right': [(r['field00rms'], '$%s00 RMS$' % self._fstr)],
                  'lylabel': '$%s00$' % self._fstr, 'rylabel': '$RMS$', }]
        return dict(X=r['time'], YINFO=YINFO, title=r['title'],
                    xlabel=r'time($R_0/c_s$)', xlim=[0, np.max(r['time'])])


class HistoryFieldModeDigger(Digger):
    '''field modes: phi, apara, fluidne, 1-8'''
    __slots__ = ['_idx']
    nitems = '+'
    itemspattern = ['^(?P<s>history)/fieldmode-' +
                    '(?P<field>(?:phi|apara|fluidne))-(?:real|imag)$']
    commonpattern = ['history/ndstep'] + [
        'gtc/%s' % k for k in ['tstep', 'ndiag', 'nmodes', 'mmodes', 'rho0',
                               'qiflux', 'rgiflux']]
    neededpattern = itemspattern + commonpattern[:-2]
    numseeds = [1, 2, 3, 4, 5, 6, 7, 8]
    post_template = 'tmpl_z111p'

    def _set_fignum(self, numseed=None):
        self._fignum = '%s_mode%s' % (self.section[1], numseed)
        self._idx = numseed
        self.kwoptions = None

    def _dig(self, **kwargs):
        '''
        kwargs
        ------
        *growth_time*: [start, end]
            set growth time, in time unit(float)
        '''
        acckwargs = {}
        fstr = field_tex_str[self.section[1]]
        yreal, yimag, ndstep, tstep, ndiag, nmodes, mmodes, rho0 = \
            self.pckloader.get_many(*self.srckeys, *self.extrakeys[:-2])
        yreal, yimag = yreal[self._idx-1], yimag[self._idx-1]
        dt = tstep * ndiag
        time = np.arange(1, ndstep + 1) * dt
        n = nmodes[self._idx-1]
        m = mmodes[self._idx-1]
        try:
            qiflux, rgiflux = self.pckloader.get_many(*self.extrakeys[-2:])
            ktr = n * qiflux / rgiflux * rho0
            dlog.parm("Get k_theta_rho0: %.6f" % ktr)
        except Exception:
            ktr = None
        # 1 original
        results = dict(time=time, yreal=yreal, yimag=yimag,
                       n=n, m=m, kthetarho0=ktr,
                       title1='$%s: n=%d, m=%d$' % (fstr, n, m))
        # 2 log(amplitude), growth rate
        title2 = r'smooth(log(amplitude))'
        if ktr:
            title2 += r', $k_{\theta}\rho_0$=%.6f' % ktr
        ya = np.sqrt(yreal**2 + yimag**2)
        if ya.any():
            logya = tools.savgol_golay_filter(np.log(ya), info='log(Amp)')
            start, end = None, None
            if 'growth_time' in kwargs:
                start, end = kwargs['growth_time']
                index = np.where((time >= start) & (time <= end))[0]
                if index.size > 0:
                    start, end = index[0], index[-1]
                    acckwargs = dict(growth_time=kwargs['growth_time'])
                else:
                    dlog.warning('Cannot set growth time: %s <= time <= %s!'
                                 % (start, end))
                    start, end = None, None
            if not start:
                start, region_len = tools.findgrowth(logya, 1e-4)
                if region_len == 0:
                    start, region_len = 0, ndstep // 4
                end = start + region_len - 1
            dlog.parm("Find growth time: [%s,%s], index: [%s,%s]."
                      % (time[start], time[end], start, end))
            # polyfit growth region
            resparm, fitya = tools.fitline(
                time[start:end+1], logya[start:end+1], 1,
                info='[%s,%s] growth time' % (time[start], time[end]))
            growth = resparm[0][0]
            dlog.parm("Get growth rate: %.6f" % growth)
        else:
            # ya all zeros
            logya = ya
            start, end = 0, 1
            fitya = logya[:2]
            growth = 0
        if self.kwoptions is None:
            fixend = (time.size - 1) if end > time.size - 1 else end
            self.kwoptions = dict(growth_time=dict(
                widget='FloatRangeSlider',
                rangee=(time[0], time[-1], dt),
                value=[time[start], time[fixend]],
                description='growth time:'))
        results.update(
            logya=logya,
            fittime=time[start:end+1],
            fitya=fitya,
            growth=growth,
            title2=title2,
        )
        # 3 amplitude normalized by growth rate, real frequency
        if ya.any():
            normyreal, reg3, reg4, nT1, omega1 = self.__get_omega(
                yreal, time, growth, start, end)
            normyimag, reg5, reg6, nT2, omega2 = self.__get_omega(
                yimag, time, growth, start, end)
            dlog.parm("Get frequency: %.6f (r), %.6f (i)" % (omega1, omega2))
        else:
            normyreal, reg3, reg4, nT1, omega1 = yreal, 0, 1, 0, 0
            normyimag, reg5, reg6, nT2, omega2 = yimag, 0, 1, 0, 0
        results.update(
            normyreal=normyreal,
            normyimag=normyimag,
            measurerealtime=[time[reg3], time[reg4]],
            measurereal=[normyreal[reg3], normyreal[reg4]],
            nT_real=nT1,
            omega_real=omega1,
            measureimagtime=[time[reg5], time[reg6]],
            measureimag=[normyimag[reg5], normyimag[reg6]],
            nT_imag=nT2,
            omega_imag=omega2,
            title3='smooth normalized amplitude',
        )
        # 4 power spectrum
        #sgn = np.array([np.complex(r, i) for r, i in zip(normyreal, normyimag)])
        sgn = np.array([np.complex(r, i) for r, i in zip(yreal, yimag)])
        _tf, _af, _pf = tools.fft(dt, sgn)
        index = np.argmax(_pf)
        omega3 = _tf[index]
        dlog.parm("Get frequency: %s, %.6f" % (index, omega3))
        results.update(
            spectrum_x=_tf,
            spectrum_p=_pf,
            spectrum_omega=omega3,
            spectrum_index=index,
            title4=r'$\phi=e^{-i(\omega*t+m*\theta-n*\zeta)}$',
        )
        return results, acckwargs

    def __get_omega(self, y, time, growth, start, end):
        normy = tools.savgol_golay_filter(
            np.divide(y, np.exp(growth * time)), info='Amp_normalized')
        index = [i for i in tools.argrelextrema(normy, m='both')
                 if 0.9*start + 0.1 * end <= i < 0.1*start + 0.9 * end]
        if len(index) >= 2:
            idx1, idx2, nT = index[0], index[-1], (len(index) - 1) / 2
            omega = 2 * np.pi * nT / (time[idx2] - time[idx1])
        else:
            idx1, idx2, nT, omega = 0, 1, 0, 0
        return normy, idx1, idx2, nT, omega

    def _post_dig(self, results):
        r = results
        ax1_calc = dict(
            LINE=[(r['time'], r['yreal'], 'real component'),
                  (r['time'], r['yimag'], 'imag component'), ],
            title=r['title1'],
            xlim=[0, np.max(r['time'])], xlabel=r'time($R_0/c_s$)',
            legend_kwargs=dict(loc='upper left'),
        )
        labelgrowth = r'Fitting, $\gamma=%.6f$' % r['growth']
        ax2_calc = dict(
            LINE=[(r['time'], r['logya']),
                  (r['fittime'], r['fitya'], labelgrowth)],
            title=r['title2'],
            xlim=[0, np.max(r['time'])], xlabel=r'time($R_0/c_s$)',
            legend_kwargs=dict(loc='lower right'),
        )
        ax3_calc = dict(
            LINE=[
                (r['time'], r['normyreal'], 'real component'),
                (r['time'], r['normyimag'], 'imag component'),
                (r['measurerealtime'], r['measurereal'],
                 r'$\omega=%.6f,nT=%.1f$' % (r['omega_real'], r['nT_real'])),
                (r['measureimagtime'], r['measureimag'],
                 r'$\omega=%.6f,nT=%.1f$' % (r['omega_imag'], r['nT_imag'])),
            ],
            xlim=[0, np.max(r['time'])], xlabel=r'time($R_0/c_s$)',
            title=r['title3'],
        )
        ymin = min(min(r['measurereal']), min(r['measureimag']))
        ymax = max(max(r['measurereal']), max(r['measureimag']))
        if (min(min(r['normyreal']), min(r['normyimag'])) < 20 * ymin
                or max(max(r['normyreal']), max(r['normyimag'])) > 20 * ymax):
            ax3_calc['ylim'] = [3 * ymin, 3 * ymax]
        max_p, min_p = max(r['spectrum_p']), min(r['spectrum_p'])
        ax4_calc = dict(
            LINE=[(r['spectrum_x'], r['spectrum_p'], 'power spectral'),
                  ([r['spectrum_omega'], r['spectrum_omega']], [min_p, max_p],
                      r'$\omega_{pmax}=%.6f$' % r['spectrum_omega'])],
            title=r['title4'], xlabel=r'$\omega$($c_s/R_0$)')
        return dict(zip_results=[
            ('tmpl_line', 221, ax1_calc), ('tmpl_line', 222, ax2_calc),
            ('tmpl_line', 223, ax3_calc), ('tmpl_line', 224, ax4_calc),
        ])
