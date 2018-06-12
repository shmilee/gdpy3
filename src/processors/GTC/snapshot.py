# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Source fortran code:

v110922
-------

1. snapshot.F90:316-321, ::
    ! parameters: # of species, fields, and grids in velocity, radius, poloidal, toroidal; T_up
    write(iosnap,101)nspecies,nfield,nvgrid,mpsi+1,mtgrid+1,mtoroidal
    write(iosnap,102)1.0/emax_inv

    ! write out particle radial profile and pdf, and 2D field
    write(iosnap,102)profile,pdf,poloidata,fluxdata

2. profile(0:mpsi,6,nspecies), snapshot.F90:20-22:66-77

nspecies: 1=ion, 2=electron, 3=EP

radial profiles(6): density, flow, energy of fullf and delf

3. pdf(nvgrid,4,nspecies), snapshot.F90:24-25:79-82

distribution function(4): energy, pitch angle of fullf and delf

4. poloidata(0:mtgrid,0:mpsi,nfield+2), snapshot.F90:236-307

field quantities: phi, a_para, fluidne. Last two coloumn of poloidal for coordinates

5. fluxdata(0:mtgrid,mtoroidal,nfield), snapshot.F90:236-270

field quantities: phi, a_para, fluidne.
'''

import numpy as np
from ..core import (
    DigCore, LayCore, log,
    FigInfo, SharexTwinxFigInfo, PcolorFigInfo
)

__all__ = ['SnapshotDigCoreV110922', 'SnapshotLayCoreV110922']


class SnapshotDigCoreV110922(DigCore):
    '''
    Snapshot Data

    1) ion, electron, EP radial profiles.
       Profile 2d array is profile[r,6].
       6 profiles order:
       fullf density, delf density, fullf flow,
       delf flow, fullf energy, delf energy.
    2) ion, electron, EP distribution function in:
       energy, pitch angle of fullf and delf.
       pdf 2d array is pdf[nvgrid,4].
       4 pdf order: fullf energy, delf energy,
       fullf pitch angle, delf pitch angle.
    3) phi, a_para, fluidne on ploidal plane
       poloidata 2d array is poloidata[theta,r].
    4) phi, a_para, fluidne on flux surface
       fluxdata 2d array is fluxdata[theta,zeta].
    '''
    __slots__ = []
    itemspattern = ['^(?P<section>snap\d{5})\.out$',
                    '.*/(?P<section>snap\d{5})\.out$']
    default_section = 'snap99999'
    _datakeys = (
        # 1. parameters
        'nspecies', 'nfield', 'nvgrid', 'mpsi+1',
        'mtgrid+1', 'mtoroidal', 'T_up',
        # 2. profile(0:mpsi,6,nspecies)
        'ion-profile', 'electron-profile', 'fastion-profile',
        # 3. pdf(nvgrid,4,nspecies)
        'ion-pdf', 'electron-pdf', 'fastion-pdf',
        # 4. poloidata(0:mtgrid,0:mpsi,nfield+2)
        'poloidata-phi', 'poloidata-apara', 'poloidata-fluidne',
        'poloidata-x', 'poloidata-z',
        # 5. fluxdata(0:mtgrid,mtoroidal,nfield)
        'fluxdata-phi', 'fluxdata-apara', 'fluxdata-fluidne')

    def _convert(self):
        '''Read 'snap%05d.out' % istep.'''
        with self.rawloader.get(self.files) as f:
            log.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        # 1. parameters
        log.debug("Filling datakeys: %s ..." % str(self._datakeys[:7]))
        for i, key in enumerate(self._datakeys[:6]):
            sd.update({key: int(outdata[i].strip())})
        # 1. T_up, 1.0/emax_inv
        sd.update({'T_up': float(outdata[6].strip())})

        outdata = np.array([float(n.strip()) for n in outdata[7:]])

        # 2. profile(0:mpsi,6,nspecies)
        tempsize = sd['mpsi+1'] * 6 * sd['nspecies']
        tempshape = (sd['mpsi+1'], 6, sd['nspecies'])
        tempdata = outdata[:tempsize].reshape(tempshape, order='F')
        log.debug("Filling datakey: %s ..." % 'ion-profile')
        sd.update({'ion-profile': tempdata[:, :, 0]})
        if sd['nspecies'] > 1:
            log.debug("Filling datakey: %s ..." % 'electron-profile')
            sd.update({'electron-profile': tempdata[:, :, 1]})
        else:
            sd.update({'electron-profile': []})
        if sd['nspecies'] > 2:
            log.debug("Filling datakey: %s ..." % 'fastion-profile')
            sd.update({'fastion-profile': tempdata[:, :, 2]})
        else:
            sd.update({'fastion-profile': []})

        # 3. pdf(nvgrid,4,nspecies)
        index0 = tempsize
        tempsize = sd['nvgrid'] * 4 * sd['nspecies']
        index1 = index0 + tempsize
        tempshape = (sd['nvgrid'], 4, sd['nspecies'])
        tempdata = outdata[index0:index1].reshape(tempshape, order='F')
        log.debug("Filling datakey: %s ..." % 'ion-pdf')
        sd.update({'ion-pdf': tempdata[:, :, 0]})
        if sd['nspecies'] > 1:
            log.debug("Filling datakey: %s ..." % 'electron-pdf')
            sd.update({'electron-pdf': tempdata[:, :, 1]})
        else:
            sd.update({'electron-pdf': []})
        if sd['nspecies'] > 2:
            log.debug("Filling datakey: %s ..." % 'fastion-pdf')
            sd.update({'fastion-pdf': tempdata[:, :, 2]})
        else:
            sd.update({'fastion-pdf': []})

        # 4. poloidata(0:mtgrid,0:mpsi,nfield+2), nfield=3
        log.debug("Filling datakeys: %s ..." % str(self._datakeys[13:18]))
        tempsize = sd['mtgrid+1'] * sd['mpsi+1'] * (sd['nfield'] + 2)
        index0, index1 = index1, index1 + tempsize
        tempshape = (sd['mtgrid+1'], sd['mpsi+1'], sd['nfield'] + 2)
        tempdata = outdata[index0:index1].reshape(tempshape, order='F')
        sd.update({'poloidata-phi': tempdata[:, :, 0]})
        sd.update({'poloidata-apara': tempdata[:, :, 1]})
        sd.update({'poloidata-fluidne': tempdata[:, :, 2]})
        sd.update({'poloidata-x': tempdata[:, :, 3]})
        sd.update({'poloidata-z': tempdata[:, :, 4]})

        # 5. fluxdata(0:mtgrid,mtoroidal,nfield)
        log.debug("Filling datakeys: %s ..." % str(self._datakeys[18:]))
        tempsize = sd['mtgrid+1'] * sd['mtoroidal'] * sd['nfield']
        index0, index1 = index1, index1 + tempsize
        tempshape = (sd['mtgrid+1'], sd['mtoroidal'], sd['nfield'])
        tempdata = outdata[index0:index1].reshape(tempshape, order='F')
        sd.update({'fluxdata-phi': tempdata[:, :, 0]})
        sd.update({'fluxdata-apara': tempdata[:, :, 1]})
        sd.update({'fluxdata-fluidne': tempdata[:, :, 2]})

        return sd


class ProfilePdfFigInfo(SharexTwinxFigInfo):
    '''Figures of ion, electron, fastion radial profiles and pdf.'''
    __slots__ = ['particle', 'pf']
    figurenums = ['%s_%s' % (p, pf)
                  for p in ['ion', 'electron', 'fastion']
                  for pf in ['profile', 'pdf']]
    numpattern = r'^%s_%s$' % (r'(?P<particle>(?:ion|electron|fastion))',
                               r'(?P<pf>(?:profile|pdf))')

    def _get_srckey_extrakey(self, fignum):
        groupdict = self._pre_check_get(fignum, 'particle', 'pf')
        self.particle = groupdict['particle']
        self.pf = groupdict['pf']
        if self.pf == 'profile':
            return ['mpsi+1', '%s-profile' % self.particle], ['gtc/tstep']
        else:
            return ['nvgrid', '%s-pdf' % self.particle], ['gtc/tstep']

    def _get_data_X_Y_title_etc(self, data):
        X = np.arange(data[self.srckey[0]])
        YDATA = data[self.srckey[1]]
        if YDATA.size > 0 and self.pf == 'profile':
            YINFO = [{'left': [(YDATA[:, 0], 'density f')],
                      'right': [(YDATA[:, 1], r'density $\delta f$')],
                      'lylabel': '$f$', 'rylabel': r'$\delta f$',
                      }, {'left': [(YDATA[:, 2], 'flow f')],
                          'right': [(YDATA[:, 3], r'flow $\delta f$')],
                          'lylabel': '$f$', 'rylabel': r'$\delta f$',
                          }, {
                'left': [(YDATA[:, 4], 'energy f')],
                'right': [(YDATA[:, 5], r'energy $\delta f$')],
                'lylabel': '$f$', 'rylabel': r'$\delta f$',
            }]
        elif YDATA.size > 0 and self.pf == 'pdf':
            YINFO = [{
                'left': [(YDATA[:, 0], 'energy f')],
                'right': [(YDATA[:, 1], r'energy $\delta f$')],
                'lylabel': '$f$', 'rylabel': r'$\delta f$',
            }, {
                'left': [(YDATA[:, 2], 'pitch angle f')],
                'right': [(YDATA[:, 3], r'pitch angle $\delta f$')],
                'lylabel': '$f$', 'rylabel': r'$\delta f$',
            }]
        else:
            YINFO = []
        istep = int(self.groups.replace('snap', ''))
        title = ('%s %s, istep=%d, time=%s$R_0/c_s$'
                 % (self.particle, self.pf, istep, istep * data['gtc/tstep']))
        xlabel = 'r (mpsi)' if self.pf == 'profile' else 'nvgrid'
        return dict(X=X, YINFO=YINFO, title=title, xlabel=xlabel,
                    xlim=[0, np.max(X)])


class FieldFluxPloidalFigInfo(PcolorFigInfo):
    '''Figures of phi, a_para, fluidne on flux surface or ploidal plane.'''
    __slots__ = ['field', 'pf']
    figurenums = ['%s_%s' % (f, pf)
                  for f in ['phi', 'apara', 'fluidne']
                  for pf in ['flux', 'ploidal']]
    numpattern = '^(?P<field>(?:phi|apara|fluidne))_(?P<pf>(?:flux|ploidal))$'
    default_plot_method = 'contourf'

    def _get_srckey_extrakey(self, fignum):
        groupdict = self._pre_check_get(fignum, 'field', 'pf')
        self.field = groupdict['field']
        self.pf = groupdict['pf']
        if self.pf == 'flux':
            return ['fluxdata-%s' % self.field], ['gtc/tstep']
        else:
            Zkey = 'poloidata-%s' % self.field
            return ['poloidata-x', 'poloidata-z', Zkey], ['gtc/tstep'],

    def _get_data_X_Y_Z_title_etc(self, data):
        if self.pf == 'flux':
            Z = data['fluxdata-%s' % self.field]
            y, x = Z.shape if Z.size > 0 else (0, 0)
            X = np.arange(0, x) / x * 2 * np.pi
            Y = np.arange(0, y) / y * 2 * np.pi
            xlabel, ylabel = r'$\zeta$', r'$\theta$'
        else:
            X, Y = data['poloidata-x'], data['poloidata-z']
            Z = data['poloidata-%s' % self.field]
            xlabel, ylabel = r'$X(R_0)$', r'$Z(R_0)$'
        istep = int(self.groups.replace('snap', ''))
        pf = 'flux surface' if self.pf == 'flux' else 'ploidal plane'
        ttl = r'$%s$ on %s' % (self.field, pf)
        ttl = ttl.replace('phi', '\phi').replace('apara', 'A_{\parallel}')
        title = (r'%s, istep=%d, time=%s$R_0/c_s$'
                 % (ttl, istep, istep * data['gtc/tstep']))
        return dict(X=X, Y=Y, Z=Z, title=title, xlabel=xlabel, ylabel=ylabel)

    def _serve(self, plotter, AxStrus, add_style):
        '''patch mpl:: *AxStrus*'''
        if plotter.name.startswith('mpl::'):
            try:
                data = AxStrus[0]['data']
                data.append([len(data) + 1, 'set_aspect', ('equal',), dict()])
            except Exception:
                log.error("Failed to patch %s!" % self.fullnum, exc_info=1)
        return AxStrus, add_style


class FieldSpectrumFigInfo(FigInfo):
    '''Figures of field poloidal and parallel spectra.'''
    __slots__ = ['field']
    figurenums = ['%s_spectrum' % f for f in ['phi', 'apara', 'fluidne']]
    numpattern = r'^(?P<field>(?:phi|apara|fluidne))_spectrum$'

    def __init__(self, fignum, scope, groups):
        groupdict = self._pre_check_get(fignum, 'field')
        self.field = groupdict['field']
        super(FieldSpectrumFigInfo, self).__init__(
            fignum, scope, groups,
            ['mtgrid+1', 'mtoroidal', 'fluxdata-%s' % self.field],
            ['gtc/tstep'], 'template_z111p_axstructs')

    def calculate(self, data, **kwargs):
        '''
        kwargs
        ------
        *mmode*, *pmode*: int
            set poloidal or parallel range
        '''
        field, it = self.field, int(self.groups.replace('snap', ''))
        fstr = field.replace('phi', '\phi').replace('apara', 'A_{\parallel}')
        timestr = 'istep=%d, time=%s$R_0/c_s$' % (it, it * data['gtc/tstep'])
        mtgrid1, mtoroidal = data['mtgrid+1'], data['mtoroidal']
        fluxdata = data['fluxdata-%s' % self.field]
        if fluxdata.size == 0:
            log.warning("No data for %s." % self.fullnum)
            return
        if fluxdata.shape != (mtgrid1, mtoroidal):
            log.error("Invalid fluxdata shape!")
            return
        mtgrid = mtgrid1 - 1
        maxmmode = int(mtgrid / 2 + 1)
        maxpmode = int(mtoroidal / 2 + 1)
        mmode, pmode = kwargs.get('mmode', None), kwargs.get('pmode', None)
        if not(isinstance(mmode, int) and mmode <= maxmmode):
            mmode = mtgrid // 5
        if not(isinstance(pmode, int) and pmode <= maxpmode):
            pmode = mtoroidal // 3
        log.parm("Poloidal and parallel range: m=%s, p=%s. Maximal m=%s, p=%s"
                 % (mmode, pmode, maxmmode, maxpmode))
        self.layout['mmode'] = dict(
            widget='IntSlider',
            rangee=(1, maxmmode, 1),
            value=mmode,
            description='mmode:')
        self.layout['pmode'] = dict(
            widget='IntSlider',
            rangee=(1, maxpmode, 1),
            value=pmode,
            description='pmode:')
        X1, Y1 = np.arange(1, mmode + 1), np.zeros(mmode)
        X2, Y2 = np.arange(1, pmode + 1), np.zeros(pmode)
        for i in range(mtoroidal):
            yy = np.fft.fft(fluxdata[:, i])
            Y1[0] = Y1[0] + (abs(yy[0]))**2
            for j in range(1, mmode):
                Y1[j] = Y1[j] + (abs(yy[j]))**2 + (abs(yy[mtgrid - j]))**2
        Y1 = np.sqrt(Y1 / mtoroidal) / mtgrid
        for i in range(mtgrid):
            yy = np.fft.fft(fluxdata[i, :])
            Y2[0] = Y2[0] + (abs(yy[0]))**2
            for j in range(1, pmode):
                Y2[j] = Y2[j] + (abs(yy[j]))**2 + (abs(yy[mtoroidal - j]))**2
        Y2 = np.sqrt(Y2 / mtgrid) / mtoroidal
        ax1_calc = dict(LINE=[(X1, Y1, 'm=%d, p=%d' % (mmode, pmode))],
                        xlabel='mtgrid', ylabel='poloidal spectrum',
                        xlim=[0, mmode], legend_kwargs=dict(loc='best'))
        ax2_calc = dict(LINE=[(X2, Y2, 'm=%d, p=%d' % (mmode, pmode))],
                        xlabel='mtoroidal', ylabel='parallel spectrum',
                        xlim=[1, pmode], legend_kwargs=dict(loc='best'))
        self.calculation = {
            'zip_results': [('template_line_axstructs', 211, ax1_calc),
                            ('template_line_axstructs', 212, ax2_calc)],
            'suptitle': r'$%s$, %s' % (fstr, timestr),
        }


class FieldProfileFigInfo(FigInfo):
    '''Figures of field and rms radius poloidal profile.'''
    __slots__ = ['field']
    figurenums = ['%s_profile' % f for f in ['phi', 'apara', 'fluidne']]
    numpattern = r'^(?P<field>(?:phi|apara|fluidne))_profile$'

    def __init__(self, fignum, scope, groups):
        groupdict = self._pre_check_get(fignum, 'field')
        self.field = groupdict['field']
        super(FieldProfileFigInfo, self).__init__(
            fignum, scope, groups,
            ['mpsi+1', 'mtgrid+1', 'poloidata-%s' % self.field],
            ['gtc/tstep'], 'template_z111p_axstructs')

    def calculate(self, data, **kwargs):
        '''
        kwargs
        ------
        *itgrid*, *ipsi*: int
            set poloidal and radius cut
        '''
        field, it = self.field, int(self.groups.replace('snap', ''))
        fstr = field.replace('phi', '\phi').replace('apara', 'A_{\parallel}')
        timestr = 'istep=%d, time=%s$R_0/c_s$' % (it, it * data['gtc/tstep'])
        mpsi1, mtgrid1 = data['mpsi+1'], data['mtgrid+1']
        pdata = data['poloidata-%s' % self.field]
        if pdata.size == 0:
            log.warning("No data for %s." % self.fullnum)
            return
        if pdata.shape != (mtgrid1, mpsi1):
            log.error("Invalid poloidata shape!")
            return
        itgrid, ipsi = kwargs.get('itgrid', None), kwargs.get('ipsi', None)
        if not(isinstance(itgrid, int) and itgrid < mtgrid1):
            itgrid = 0
        if not(isinstance(ipsi, int) and ipsi < mpsi1):
            ipsi = (mpsi1 - 1) // 2
        log.parm("Poloidal and radius cut: itgrid=%s, ipsi=%s. "
                 "Maximal itgrid=%s, ipsi=%s."
                 % (itgrid, ipsi, mtgrid1 - 1, mpsi1 - 1))
        self.layout['itgrid'] = dict(
            widget='IntSlider',
            rangee=(0, mtgrid1 - 1, 1),
            value=itgrid,
            description='itgrid:')
        self.layout['ipsi'] = dict(
            widget='IntSlider',
            rangee=(0, mpsi1 - 1, 1),
            value=ipsi,
            description='ipsi:')
        X1, Y11 = np.arange(0, mpsi1), pdata[itgrid, :]
        X2 = np.arange(0, mtgrid1) / mtgrid1 * 2 * np.pi
        Y21 = pdata[:, ipsi]
        # f*f [ f[i,j]*f[i,j] ]; np.sum, axis=0, along col
        Y12 = np.sqrt(np.sum(pdata * pdata, axis=0) / mtgrid1)
        Y22 = np.sqrt(np.sum(pdata * pdata, axis=1) / mpsi1)
        ax1_calc = dict(
            X=X1, xlabel='r(mpsi)',
            YINFO=[{'left': [(Y11, 'point value')], 'right': [(Y12, 'rms')],
                    'lylabel': 'point value', 'rylabel': 'RMS'}],
            title=r'radius profile: itgrid=%d ($\theta=%.2f=%.2f\degree$)' % (
                itgrid, X2[itgrid], itgrid / mtgrid1 * 360))
        ax2_calc = dict(
            X=X2, xlabel=r'$\theta$',
            YINFO=[{'left': [(Y21, 'point value')], 'right': [(Y22, 'rms')],
                    'lylabel': 'point value', 'rylabel': 'RMS'}],
            title='poloidal profile: ipsi=%d' % ipsi)
        self.calculation = {
            'zip_results': [
                ('template_sharex_twinx_axstructs', 211, ax1_calc),
                ('template_sharex_twinx_axstructs', 212, ax2_calc)],
            'suptitle': r'$%s$, %s' % (fstr, timestr),
        }


class SnapshotLayCoreV110922(LayCore):
    '''
    Snapshot Figures
    '''
    __slots__ = []
    itemspattern = ['^(?P<section>snap\d{5})$']
    default_section = 'snap99999'
    figinfoclasses = [ProfilePdfFigInfo, FieldFluxPloidalFigInfo,
                      FieldSpectrumFigInfo, FieldProfileFigInfo]
