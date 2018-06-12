# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

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

import numpy as np
from .. import tools
from ..core import DigCore, LayCore, FigInfo, SharexTwinxFigInfo, log

__all__ = ['HistoryDigCoreV110922', 'HistoryLayCoreV110922']


class HistoryDigCoreV110922(DigCore):
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
    itemspattern = ['^(?P<section>history)\.out$',
                    '.*/(?P<section>history)\.out$']
    default_section = 'history'
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
            log.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        # 1. diagnosis.F90:opendiag():734-735
        log.debug("Filling datakeys: %s ..." % str(self._datakeys[:7]))
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
        log.debug("Filling datakeys: %s ..." % str(self._datakeys[10:13]))
        index0 = sd['nspecies'] * sd['mpdiag']
        index1 = index0 + sd['mfdiag']
        sd.update({'fieldtime-phi': outdata[index0:index1, :]})
        index0, index1 = index1, index1 + sd['mfdiag']
        sd.update({'fieldtime-apara': outdata[index0:index1, :]})
        index0, index1 = index1, index1 + sd['mfdiag']
        sd.update({'fieldtime-fluidne': outdata[index0:index1, :]})

        # 5. fieldmode(2,modes,nfield)
        log.debug("Filling datakeys: %s ..." % str(self._datakeys[13:]))
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


class ParticleFigInfo(SharexTwinxFigInfo):
    '''Figures of ion, electron, fastion history'''
    __slots__ = ['particle', 'pf']
    figurenums = ['%s%s' % (p, pf)
                  for p in ['ion', 'electron', 'fastion']
                  for pf in ['', '_flux']]
    numpattern = '^(?P<particle>(?:ion|electron|fastion))(?P<pf>(?:_flux|))$'

    def _get_srckey_extrakey(self, fignum):
        groupdict = self._pre_check_get(fignum, 'particle', 'pf')
        self.particle = groupdict['particle']
        self.pf = groupdict['pf']
        return ['ndstep', '%s' % self.particle], ['gtc/tstep', 'gtc/ndiag']

    def _get_data_X_Y_title_etc(self, data):
        dt = data['gtc/tstep'] * data['gtc/ndiag']
        X = np.arange(1, data['ndstep'] + 1) * dt
        YDATA = data['%s' % self.particle]
        if YDATA.size > 0 and self.pf == '':
            YINFO = [{
                'left': [(YDATA[0], r'density $\delta f$')],
                'right': [(YDATA[1], r'entropy $\delta f^2$')],
                'lylabel': r'$\delta f$', 'rylabel': r'$\delta f^2$',
            }, {
                'left': [(YDATA[2], r'flow u')],
                'right': [(YDATA[3], r'$\delta u$')],
                'lylabel': '$u$', 'rylabel': r'$\delta u$',
            }, {
                'left': [(YDATA[4], r'energy $E-1.5$')],
                'right': [(YDATA[5], r'entropy $\delta E$')],
                'lylabel': r'$E$', 'rylabel': r'$\delta E$',
            }]
        elif YDATA.size > 0 and self.pf == '_flux':
            YINFO = [{'left': [(YDATA[6], 'particle flux')], 'right': [], },
                     {'left': [(YDATA[7], 'momentum flux')], 'right': [], },
                     {'left': [(YDATA[8], 'energy flux')], 'right': [], }]
        else:
            YINFO = []
        title = 'particle %s' % self.fignum.replace('_', ' ')
        return dict(X=X, YINFO=YINFO, title=title,
                    xlabel=r'time($R_0/c_s$)', xlim=[0, np.max(X)])


class FieldFigInfo(SharexTwinxFigInfo):
    '''Figures of phi, apara, fluidne history'''
    __slots__ = ['field']
    figurenums = ['field_%s' % f for f in ['phi', 'apara', 'fluidne']]
    numpattern = r'^field_(?P<field>(?:phi|apara|fluidne))$'

    def _get_srckey_extrakey(self, fignum):
        field = self._pre_check_get(fignum, 'field')['field']
        self.field = field
        return ['ndstep', 'fieldtime-%s' % field], ['gtc/tstep', 'gtc/ndiag']

    @staticmethod
    def __replace_str(field):
        '''replace phi -> \phi, apara -> a_{\parallel}, etc'''
        strmap = (('phi00', 'phi_{p00}'),
                  ('apara00', 'a_{\parallel 00}'),
                  ('fluidne00', 'fluidne_{00}'),
                  ('phi', '\phi'),
                  ('apara', 'a_{\parallel}'),)
        result = field
        for i, j in strmap:
            result = result.replace(i, j)
        return result

    def _get_data_X_Y_title_etc(self, data):
        dt = data['gtc/tstep'] * data['gtc/ndiag']
        X = np.arange(1, data['ndstep'] + 1) * dt
        YDATA = data['fieldtime-%s' % self.field]
        fstr = self.__replace_str(self.field)
        if YDATA.size > 0:
            YINFO = [{'left': [(YDATA[0], '$%s$' % fstr)],
                      'right': [(YDATA[3], '$%s RMS$' % fstr)],
                      'lylabel': '$%s$' % fstr, 'rylabel': '$RMS$', },
                     {'left': [(YDATA[1], '$%s00$' % fstr)],
                      'right': [(YDATA[2], '$%s00 RMS$' % fstr)],
                      'lylabel': '$%s00$' % fstr, 'rylabel': '$RMS$', }]
        else:
            YINFO = []
        title = r'$%s (\theta=\zeta=0), %s00 (i=iflux)$' % (fstr, fstr)
        return dict(X=X, YINFO=YINFO, title=title,
                    xlabel=r'time($R_0/c_s$)', xlim=[0, np.max(X)])


class ModeFigInfo(FigInfo):
    '''Figures of field modes: phi, apara, fluidne, 1-8'''
    __slots__ = ['index', 'field']
    figurenums = ['mode%s_%s' % (i, f)
                  for i in range(1, 9)
                  for f in ['phi', 'apara', 'fluidne']]
    numpattern = r'^mode(?P<index>\d)_(?P<field>(?:phi|apara|fluidne))$'

    def __init__(self, fignum, scope, groups):
        groupdict = self._pre_check_get(fignum, 'index', 'field')
        self.index = int(groupdict['index'])
        self.field = groupdict['field']
        super(ModeFigInfo, self).__init__(
            fignum, scope, groups,
            ['ndstep', 'fieldmode-%s-real' % self.field,
             'fieldmode-%s-imag' % self.field, ],
            ['gtc/%s' % k for k in ['tstep', 'ndiag', 'nmodes', 'mmodes',
                                    'qiflux', 'rgiflux', 'rho0']],
            'template_z111p_axstructs')

    def calculate(self, data, **kwargs):
        '''
        kwargs
        ------
        *growth_region*: [start, end]
            set growth region, in tstep unit(int)
        '''
        index = self.index - 1
        field = self.field
        fstr = field.replace('phi', '\phi').replace('apara', 'A_{\parallel}')
        ndstep = data['ndstep']
        yreal = data['fieldmode-%s-real' % self.field][index]
        yimag = data['fieldmode-%s-imag' % self.field][index]
        dt = data['gtc/tstep'] * data['gtc/ndiag']
        time = np.arange(1, data['ndstep'] + 1) * dt
        n = data['gtc/nmodes'][index]
        m = data['gtc/mmodes'][index]
        ktr = n * data['gtc/qiflux'] / data['gtc/rgiflux'] * data['gtc/rho0']
        # 1 original
        ax1_calc = dict(
            LINE=[(time, yreal, 'real component'),
                  (time, yimag, 'imag component'), ],
            title='$%s: n=%d, m=%d$' % (fstr, n, m),
            xlim=[0, np.max(time)], xlabel=r'time($R_0/c_s$)',
            legend_kwargs=dict(loc='upper left'),
        )
        self.calculation = {
            'zip_results': [('template_line_axstructs', 221, ax1_calc)],
            'n': n, 'm': m, 'kthetarhoi': ktr,
            'qiflux': data['gtc/qiflux'], 'rgiflux': data['gtc/rgiflux'],
        }
        # 2 log(amplitude), growth rate
        ya = np.sqrt(yreal**2 + yimag**2)
        if ya.any():
            logya = tools.savgol_golay_filter(np.log(ya), 51, 3, nodebug=True)
        else:
            # all zeros
            logya = ya
        # find growth region
        growth_region = kwargs.get('growth_region', None)
        if (growth_region and isinstance(growth_region, (list, tuple))
                and len(growth_region) == 2
                and isinstance(growth_region[0], int)
                and isinstance(growth_region[1], int)
                and growth_region[0] < growth_region[1] < ndstep):
            reg1, reg2 = growth_region
            region_len = reg2 - reg1
        else:
            reg1, region_len = tools.findgrowth(logya, 1e-4)
            if region_len == 0:
                reg1, region_len = 0, ndstep // 4
            reg2 = reg1 + region_len
        log.parm("Find growth region: [%s,%s], index: [%s,%s)."
                 % (time[reg1], time[reg2 - 1], reg1, reg2))
        # polyfit region1
        result, line = tools.fitline(
            time[reg1:reg2], logya[reg1:reg2], 1,
            info='[%s,%s] growth region' % (time[reg1], time[reg2 - 1]))
        growth = result[0][0]
        log.parm("Get growth rate: %.6f" % growth)
        ax2_calc = dict(
            LINE=[
                (time, logya),
                (time[reg1:reg2], line, r'Fitting, $\gamma=%.6f$' % growth)],
            title=r'smooth(log(amplitude)), $k_{\theta}\rho_i$=%.6f' % ktr,
            xlim=[0, np.max(time)], xlabel=r'time($R_0/c_s$)',
            legend_kwargs=dict(loc='lower right'),
        )
        self.calculation['zip_results'].append(
            ('template_line_axstructs', 222, ax2_calc))
        self.calculation.update(growth=growth)
        # 3 amplitude normalized by growth rate, real frequency
        normreal = tools.savgol_golay_filter(
            np.divide(yreal, np.exp(growth * time)), 47, 3)
        index = [i for i in tools.argrelextrema(normreal, m='both')
                 if reg1 + 0.1 * region_len <= i < reg1 + 0.9 * region_len]
        log.parm("Real argrelextrema: %s" % index)
        if len(index) >= 2:
            reg3, reg4, nT1 = index[0], index[-1], (len(index) - 1) / 2
            omega1 = 2 * np.pi * nT1 / (time[reg4] - time[reg3])
        else:
            reg3, reg4, nT1 = reg1, reg2, 0
            omega1 = 0
        normimag = tools.savgol_golay_filter(
            np.divide(yimag, np.exp(growth * time)), 47, 3)
        index = [i for i in tools.argrelextrema(normimag, m='both')
                 if reg1 + 0.1 * region_len <= i < reg1 + 0.9 * region_len]
        log.parm("Imag argrelextrema: %s" % index)
        if len(index) >= 2:
            reg5, reg6, nT2 = index[0], index[-1], (len(index) - 1) / 2
            omega2 = 2 * np.pi * nT2 / (time[reg6] - time[reg5])
        else:
            reg5, reg6, nT2 = reg1, reg2, 0
            omega2 = 0
        ax3_calc = dict(
            LINE=[
                (time, normreal, 'real component'),
                (time, normimag, 'imag component'),
                ([time[reg3], time[reg4]], [normreal[reg3], normreal[reg4]],
                    r'$\omega=%.6f,nT=%.1f$' % (omega1, nT1)),
                ([time[reg5], time[reg6]], [normimag[reg5], normimag[reg6]],
                    r'$\omega=%.6f,nT=%.1f$' % (omega2, nT2)),
            ],
            xlim=[0, np.max(time)], xlabel=r'time($R_0/c_s$)',
            ylabel='smooth normalized amplitude',
        )
        ymin = min(min(normreal[reg3:reg4]), min(normimag[reg5:reg6]))
        ymax = max(max(normreal[reg3:reg4]), max(normimag[reg5:reg6]))
        if (min(min(normreal), min(normimag)) < 20 * ymin
                or max(max(normreal), max(normimag)) > 20 * ymax):
            ax3_calc['ylim'] = [3 * ymin, 3 * ymax]
        self.calculation['zip_results'].append(
            ('template_line_axstructs', 223, ax3_calc))
        self.calculation.update(omega1=omega1, omega2=omega2)
        # 4 power spectral
        sgn = np.array([np.complex(r, i) for r, i in zip(normreal, normimag)])
        # sgn = np.array([np.complex(r, i) for r, i in zip(yreal, yimag)])
        _tf, _af, _pf = tools.fft(dt, sgn)
        index = np.argmax(_pf)
        omega3 = _tf[index]
        log.parm("Get frequency: %s, %.6f" % (index, omega3))
        ax4_calc = dict(
            LINE=[(_tf, _pf, 'power spectral'),
                  ([omega3], [_pf[index]], r'$\omega_{pmax}=%.6f$' % omega3)],
            title=r'$\phi=e^{-i(\omega*t+m*\theta-n*\zeta)}$',
            xlabel=r'$\omega$($c_s/R_0$)', xlim=[_tf[0], _tf[-1]],)
        self.calculation['zip_results'].append(
            ('template_line_axstructs', 224, ax4_calc))
        self.calculation.update(omega3=omega3)

        self.layout['growth_region'] = dict(
            widget='IntRangeSlider',
            rangee=(0, ndstep, 1),
            value=[reg1, reg2],
            description='growth region:')


class HistoryLayCoreV110922(LayCore):
    '''
    History Figures
    '''
    __slots__ = []
    itemspattern = ['^(?P<section>history)$']
    default_section = 'history'
    figinfoclasses = [ParticleFigInfo, FieldFigInfo, ModeFigInfo]
