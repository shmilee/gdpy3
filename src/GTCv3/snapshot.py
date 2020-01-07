# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
Source fortran code:

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
from .. import tools
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog

_all_Converters = ['SnapshotConverter']
_all_Diggers = ['SnapshotProfilePdfDigger', 'SnapshotFieldFluxDigger',
                'SnapshotFieldPoloidalDigger', 'SnapshotFieldSpectrumDigger',
                'SnapshotFieldProfileDigger', 'SnapshotFieldmDigger']
__all__ = _all_Converters + _all_Diggers


class SnapshotConverter(Converter):
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
    3) phi, a_para, fluidne on poloidal plane
       poloidata 2d array is poloidata[theta,r].
    4) phi, a_para, fluidne on flux surface
       fluxdata 2d array is fluxdata[theta,zeta].
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = ['^(?P<section>snap\d{5,7})\.out$',
                    '.*/(?P<section>snap\d{5,7})\.out$']
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
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        # 1. parameters
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:7]))
        for i, key in enumerate(self._datakeys[:6]):
            sd.update({key: int(outdata[i].strip())})
        # 1. T_up, 1.0/emax_inv
        sd.update({'T_up': float(outdata[6].strip())})

        outdata = np.array([float(n.strip()) for n in outdata[7:]])

        # 2. profile(0:mpsi,6,nspecies)
        tempsize = sd['mpsi+1'] * 6 * sd['nspecies']
        tempshape = (sd['mpsi+1'], 6, sd['nspecies'])
        tempdata = outdata[:tempsize].reshape(tempshape, order='F')
        clog.debug("Filling datakey: %s ..." % 'ion-profile')
        sd.update({'ion-profile': tempdata[:, :, 0]})
        if sd['nspecies'] > 1:
            clog.debug("Filling datakey: %s ..." % 'electron-profile')
            sd.update({'electron-profile': tempdata[:, :, 1]})
        if sd['nspecies'] > 2:
            clog.debug("Filling datakey: %s ..." % 'fastion-profile')
            sd.update({'fastion-profile': tempdata[:, :, 2]})

        # 3. pdf(nvgrid,4,nspecies)
        index0 = tempsize
        tempsize = sd['nvgrid'] * 4 * sd['nspecies']
        index1 = index0 + tempsize
        tempshape = (sd['nvgrid'], 4, sd['nspecies'])
        tempdata = outdata[index0:index1].reshape(tempshape, order='F')
        clog.debug("Filling datakey: %s ..." % 'ion-pdf')
        sd.update({'ion-pdf': tempdata[:, :, 0]})
        if sd['nspecies'] > 1:
            clog.debug("Filling datakey: %s ..." % 'electron-pdf')
            sd.update({'electron-pdf': tempdata[:, :, 1]})
        if sd['nspecies'] > 2:
            clog.debug("Filling datakey: %s ..." % 'fastion-pdf')
            sd.update({'fastion-pdf': tempdata[:, :, 2]})

        # 4. poloidata(0:mtgrid,0:mpsi,nfield+2), nfield=3
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[13:18]))
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
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[18:]))
        tempsize = sd['mtgrid+1'] * sd['mtoroidal'] * sd['nfield']
        index0, index1 = index1, index1 + tempsize
        tempshape = (sd['mtgrid+1'], sd['mtoroidal'], sd['nfield'])
        tempdata = outdata[index0:index1].reshape(tempshape, order='F')
        sd.update({'fluxdata-phi': tempdata[:, :, 0]})
        sd.update({'fluxdata-apara': tempdata[:, :, 1]})
        sd.update({'fluxdata-fluidne': tempdata[:, :, 2]})

        return sd


def _snap_get_timestr(snapgroup, pckloader):
    istep = int(snapgroup.replace('snap', ''))
    tstep = pckloader.get('gtc/tstep')
    return r'istep=%d, time=%s$R_0/c_s$' % (istep, istep * tstep)


class SnapshotProfilePdfDigger(Digger):
    '''ion, electron, fastion radial profiles and pdf.'''
    __slots__ = []
    nitems = '+'
    itemspattern = ['^(?P<section>snap\d{5,7})'
                    + '/(?P<particle>(?:ion|electron|fastion))'
                    + '-(?P<pf>(?:profile|pdf))$',
                    '^(?P<s>snap\d{5,7})/mpsi\+1',
                    '^(?P<s>snap\d{5,7})/nvgrid']
    commonpattern = ['gtc/tstep']
    post_template = 'tmpl_sharextwinx'

    def _set_fignum(self, numseed=None):
        self._fignum = '%s_%s' % self.section[1:]

    def _dig(self, kwargs):
        title = '%s %s, %s' % (self.section[1], self.section[2],
                               _snap_get_timestr(self.group, self.pckloader))
        data, x1, x2 = self.pckloader.get_many(*self.srckeys)
        data = data.T
        if self.section[2] == 'profile':
            return dict(
                ipsi=np.arange(x1),
                density=data[0],
                densitydf=data[1],
                flow=data[2],
                flowdf=data[3],
                energy=data[4],
                energydf=data[5],
                title=title,
                xlabel='r (mpsi)'), {}
        else:
            return dict(
                jvgrid=np.arange(x2),
                energy=data[0],
                energydf=data[1],
                pitchangle=data[2],
                pitchangledf=data[3],
                title=title,
                xlabel='nvgrid'), {}

    def _post_dig(self, results):
        r = results
        if self.section[2] == 'profile':
            X = r['ipsi']
            YINFO = [{'left': [(r['density'], 'density f')],
                      'right': [(r['densitydf'], r'density $\delta f$')],
                      'lylabel': '$f$', 'rylabel': r'$\delta f$'},
                     {'left': [(r['flow'], 'flow f')],
                      'right': [(r['flowdf'], r'flow $\delta f$')],
                      'lylabel': '$f$', 'rylabel': r'$\delta f$'},
                     {'left': [(r['energy'], 'energy f')],
                      'right': [(r['energydf'], r'energy $\delta f$')],
                      'lylabel': '$f$', 'rylabel': r'$\delta f$'}]
        else:
            X = r['jvgrid']
            YINFO = [{'left': [(r['energy'], 'energy f')],
                      'right': [(r['energydf'], r'energy $\delta f$')],
                      'lylabel': '$f$', 'rylabel': r'$\delta f$'},
                     {'left': [(r['pitchangle'], 'pitch angle f')],
                      'right': [(r['pitchangledf'], r'pitch angle $\delta f$')],
                      'lylabel': '$f$', 'rylabel': r'$\delta f$'}]
        return dict(X=X, YINFO=YINFO, title=r['title'],
                    xlabel=r['xlabel'], xlim=[0, np.max(X)])


field_tex_str = {
    'phi': r'\phi',
    'apara': r'A_{\parallel}',
    'fluidne': r'fluid n_e'
}


class SnapshotFieldFluxDigger(Digger):
    '''phi, a_para, fluidne on flux surface.'''
    __slots__ = []
    nitems = '?'
    itemspattern = ['^(?P<section>snap\d{5,7})'
                    + '/fluxdata-(?P<field>(?:phi|apara|fluidne))']
    commonpattern = ['gtc/tstep']
    post_template = 'tmpl_contourf'

    def _set_fignum(self, numseed=None):
        self._fignum = '%s_flux' % self.section[1]

    def _dig(self, kwargs):
        title = _snap_get_timestr(self.group, self.pckloader)
        fstr = field_tex_str[self.section[1]]
        data = self.pckloader.get(self.srckeys[0])
        y, x = data.shape
        return dict(
            zeta=np.arange(0, x) / x * 2 * np.pi,
            theta=np.arange(0, y) / y * 2 * np.pi,
            field=data,
            title=r'$%s$ on flux surface, %s' % (fstr, title)), {}

    def _post_dig(self, results):
        r = results
        return dict(X=r['zeta'], Y=r['theta'], Z=r['field'],
                    title=r['title'], xlabel=r'$\zeta$',
                    ylabel=r'$\theta$', aspect='equal')


class SnapshotFieldPoloidalDigger(Digger):
    '''phi, a_para, fluidne on poloidal plane.'''
    __slots__ = []
    nitems = '+'
    itemspattern = ['^(?P<section>snap\d{5,7})'
                    + '/poloidata-(?P<field>(?:phi|apara|fluidne))',
                    '^(?P<s>snap\d{5,7})/poloidata-(?:x|z)']
    commonpattern = ['gtc/tstep', 'gtc/mpsi', 'gtc/arr2', 'gtc/a_minor']
    neededpattern = itemspattern + commonpattern[:-2]
    post_template = 'tmpl_z111p'

    def _set_fignum(self, numseed=None):
        self._fignum = '%s_poloi' % self.section[1]
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *circle_iflux*: int, default mpsi//2
            when iflux=[1,mpsi-1], add a circle for r(iflux)
            when iflux=0,mpsi, donot add circle
        '''
        title = _snap_get_timestr(self.group, self.pckloader)
        fstr = field_tex_str[self.section[1]]
        data, X, Z = self.pckloader.get_many(*self.srckeys)
        mpsi = self.pckloader.get('gtc/mpsi')
        circle_iflux = kwargs.get('circle_iflux', mpsi//2)
        if isinstance(circle_iflux, int) and 0 < circle_iflux < mpsi:
            dlog.parm("Add circle for iflux=%s on poloidal plane." %
                      circle_iflux)
        else:
            circle_iflux = 0
        acckwargs = dict(circle_iflux=circle_iflux)
        circle_r = 0
        if circle_iflux:
            try:
                arr2, a = self.pckloader.get_many(*self.common[-2:])
                rr = arr2[:, 1] / a  # arr2 [1,mpsi-1]
                circle_r = np.round(rr[circle_iflux-1], decimals=3)
            except Exception:
                pass
        if self.kwoptions is None:
            self.kwoptions = dict(
                circle_iflux=dict(
                    widget='IntSlider',
                    rangee=(0, mpsi, 1),
                    value=circle_iflux,
                    description='circle_iflux:'))
        return dict(
            X=X, Z=Z, field=data, circle_iflux=circle_iflux, circle_r=circle_r,
            title=r'$%s$ on poloidal plane, %s' % (fstr, title)), acckwargs

    def _post_dig(self, results):
        # ?TODO? kwargs['circle_iflux '] to postkwargs ?kwoptions?
        r = results
        zip_results = [('tmpl_contourf', 111, dict(
            X=r['X'], Y=r['Z'], Z=r['field'], title=r['title'],
            xlabel=r'$R(R_0)$', ylabel=r'$Z(R_0)$', aspect='equal'))]
        if r['circle_iflux']:
            X, Z = r['X'][:, r['circle_iflux']], r['Z'][:, r['circle_iflux']]
            if r['circle_r']:
                label = r'r(iflux=%d)=%ga' % (r['circle_iflux'], r['circle_r'])
            else:
                label = r'iflux=%d' % r['circle_iflux']
            zip_results.append(('tmpl_line', 111, dict(LINE=[
                ([], []), (X, Z, label)])))
        return dict(zip_results=zip_results)


class SnapshotFieldSpectrumDigger(Digger):
    '''field poloidal and parallel spectra.'''
    __slots__ = []
    nitems = '+'
    itemspattern = ['^(?P<section>snap\d{5,7})'
                    + '/fluxdata-(?P<field>(?:phi|apara|fluidne))',
                    '^(?P<s>snap\d{5,7})/mtgrid\+1',
                    '^(?P<s>snap\d{5,7})/mtoroidal']
    commonpattern = ['gtc/tstep']
    post_template = 'tmpl_z111p'

    def _set_fignum(self, numseed=None):
        self._fignum = '%s_spectrum' % self.section[1]
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *mmode*, *pmode*: int
            set poloidal or parallel range
        '''
        fluxdata, mtgrid1, mtoroidal = self.pckloader.get_many(*self.srckeys)
        if fluxdata.shape != (mtgrid1, mtoroidal):
            log.error("Invalid fluxdata shape!")
            return
        mtgrid = mtgrid1 - 1
        maxmmode = int(mtgrid / 2 + 1)
        maxpmode = int(mtoroidal / 2 + 1)
        mmode, pmode = kwargs.get('mmode', None), kwargs.get('pmode', None)
        if not (isinstance(mmode, int) and mmode <= maxmmode):
            mmode = mtgrid // 5
        if not (isinstance(pmode, int) and pmode <= maxpmode):
            pmode = mtoroidal // 3
        acckwargs = dict(mmode=mmode, pmode=pmode)
        dlog.parm("Poloidal and parallel range: m=%s, p=%s. Maximal m=%s, p=%s"
                  % (mmode, pmode, maxmmode, maxpmode))
        if self.kwoptions is None:
            self.kwoptions = dict(
                mmode=dict(
                    widget='IntSlider',
                    rangee=(1, maxmmode, 1),
                    value=mmode,
                    description='mmode:'),
                pmode=dict(
                    widget='IntSlider',
                    rangee=(1, maxpmode, 1),
                    value=pmode,
                    description='pmode:'))
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
        fstr = field_tex_str[self.section[1]]
        timestr = _snap_get_timestr(self.group, self.pckloader)
        return dict(
            jtgrid=X1, poloidal_spectrum=Y1, mmode=mmode,
            ktoroidal=X2, parallel_spectrum=Y2, pmode=pmode,
            title=r'$%s$, %s' % (fstr, timestr),
        ), acckwargs

    def _post_dig(self, results):
        r = results
        ax1_calc = dict(LINE=[(r['jtgrid'], r['poloidal_spectrum'])],
                        xlabel='mtgrid', ylabel='poloidal spectrum',
                        xlim=[0, r['mmode']])
        ax2_calc = dict(LINE=[(r['ktoroidal'], r['parallel_spectrum'])],
                        xlabel='mtoroidal', ylabel='parallel spectrum',
                        xlim=[1, r['pmode']])
        return dict(zip_results=[
            ('tmpl_line', 211, ax1_calc),
            ('tmpl_line', 212, ax2_calc),
        ], suptitle=r'%s, m=%d, p=%d' % (r['title'], r['mmode'], r['pmode']))


class SnapshotFieldProfileDigger(Digger):
    '''field and rms radius poloidal profile'''
    __slots__ = []
    nitems = '+'
    itemspattern = ['^(?P<section>snap\d{5,7})'
                    + '/poloidata-(?P<field>(?:phi|apara|fluidne))',
                    '^(?P<s>snap\d{5,7})/mpsi\+1',
                    '^(?P<s>snap\d{5,7})/mtgrid\+1']
    commonpattern = ['gtc/tstep']
    post_template = 'tmpl_z111p'

    def _set_fignum(self, numseed=None):
        self._fignum = '%s_profile' % self.section[1]
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *jtgrid*, *ipsi*: int
            set poloidal and radius cut
        '''
        pdata, mpsi1, mtgrid1 = self.pckloader.get_many(*self.srckeys)
        if pdata.shape != (mtgrid1, mpsi1):
            log.error("Invalid poloidata shape!")
            return
        jtgrid, ipsi = kwargs.get('jtgrid', None), kwargs.get('ipsi', None)
        if not (isinstance(jtgrid, int) and jtgrid < mtgrid1):
            jtgrid = 0
        if not (isinstance(ipsi, int) and ipsi < mpsi1):
            ipsi = (mpsi1 - 1) // 2
        acckwargs = dict(jtgrid=jtgrid, ipsi=ipsi)
        dlog.parm("Poloidal and radius cut: jtgrid=%s, ipsi=%s. "
                  "Maximal jtgrid=%s, ipsi=%s."
                  % (jtgrid, ipsi, mtgrid1 - 1, mpsi1 - 1))
        if self.kwoptions is None:
            self.kwoptions = dict(
                jtgrid=dict(
                    widget='IntSlider',
                    rangee=(0, mtgrid1 - 1, 1),
                    value=jtgrid,
                    description='jtgrid:'),
                ipsi=dict(
                    widget='IntSlider',
                    rangee=(0, mpsi1 - 1, 1),
                    value=ipsi,
                    description='ipsi:'))
        X1, Y11 = np.arange(0, mpsi1), pdata[jtgrid, :]
        X2 = np.arange(0, mtgrid1) / mtgrid1 * 2 * np.pi
        Y21 = pdata[:, ipsi]
        # f*f [ f[i,j]*f[i,j] ]; np.sum, axis=0, along col
        Y12 = np.sqrt(np.sum(pdata * pdata, axis=0) / mtgrid1)
        Y22 = np.sqrt(np.sum(pdata * pdata, axis=1) / mpsi1)
        fstr = field_tex_str[self.section[1]]
        timestr = _snap_get_timestr(self.group, self.pckloader)
        return dict(
            ipsi=X1, radius_profile=Y11, rms_radius_profile=Y12,
            title1=r'radius profile: jtgrid=%d ($\theta=%.2f=%.2f\degree$)' % (
                jtgrid, X2[jtgrid], jtgrid / mtgrid1 * 360),
            theta=X2, poloidal_profile=Y21, rms_poloidal_profile=Y22,
            title2='poloidal profile: ipsi=%d' % ipsi,
            suptitle=r'$%s$, %s' % (fstr, timestr)), acckwargs

    def _post_dig(self, results):
        r = results
        ax1_calc = dict(
            X=r['ipsi'], xlabel='r(mpsi)',
            YINFO=[{'left': [(r['radius_profile'], 'point value')],
                    'right': [(r['rms_radius_profile'], 'rms')],
                    'lylabel': 'point value', 'rylabel': 'RMS'}],
            title=r['title1'])
        ax2_calc = dict(
            X=r['theta'], xlabel=r'$\theta$',
            YINFO=[{'left': [(r['poloidal_profile'], 'point value')],
                    'right': [(r['rms_poloidal_profile'], 'rms')],
                    'lylabel': 'point value', 'rylabel': 'RMS'}],
            title=r['title2'])
        return dict(zip_results=[
            ('tmpl_sharextwinx', 211, ax1_calc),
            ('tmpl_sharextwinx', 212, ax2_calc),
        ], suptitle=r['suptitle'])


class SnapshotFieldmDigger(Digger):
    '''profile of field_m'''
    __slots__ = []
    nitems = '+'
    itemspattern = ['^(?P<section>snap\d{5,7})'
                    + '/poloidata-(?P<field>(?:phi|apara|fluidne))',
                    '^(?P<s>snap\d{5,7})/mpsi\+1',
                    '^(?P<s>snap\d{5,7})/mtgrid\+1']
    commonpattern = ['gtc/tstep', 'gtc/arr2', 'gtc/a_minor']
    post_template = 'tmpl_line'

    def _set_fignum(self, numseed=None):
        self._fignum = '%s_fieldm' % self.section[1]
        self.kwoptions = None

    def _dig(self, kwargs):
        timestr = _snap_get_timestr(self.group, self.pckloader)
        fstr = field_tex_str[self.section[1]]
        pdata, mpsi1, mtgrid1, dt, arr2, a = self.pckloader.get_many(
            *self.srckeys, *self.common)
        if pdata.shape != (mtgrid1, mpsi1):
            log.error("Invalid poloidata shape!")
            return
        rr = arr2[:, 1] / a
        fieldm = []
        for ipsi in range(1, mpsi1 - 1):
            y = pdata[:, ipsi]
            dy_ft = np.fft.fft(y)/mtgrid1 * 2  # why /mtgrid1 * 2
            fieldm.append(abs(dy_ft[:mtgrid1//2]))
        fieldm = np.array(fieldm).T
        jlist, acckwargs, envY, envXp, envYp, envXmax, envYmax = \
            self._remove_add_some_lines(fieldm, rr, kwargs)
        return dict(rr=rr, fieldm=fieldm, jlist=jlist,
                    envY=envY, envXp=envXp, envYp=envYp,
                    envXmax=envXmax, envYmax=envYmax,
                    title=r'$\left|{%s}_m(r)\right|$, %s' % (fstr, timestr)
                    ), acckwargs

    def _remove_add_some_lines(self, fieldm, rr, kwargs):
        '''
        kwargs
        ------
        *ymaxlimit*: float, default 0
            if (ymax of line) < ymaxlimit * (ymax of lines), then remove it.
        *envelope*: bool
            add high envelope or not, default False
        *kind*: str or odd int
            the kind of interpolation for envelope, default 'cubic'
            see class scipy.interpolate.interpolate.interp1d
        '''
        if self.kwoptions is None:
            self.kwoptions = dict(
                ymaxlimit=dict(widget='FloatSlider',
                               rangee=(0, 1, 0.05),
                               value=0.0,
                               description='ymaxlimit:'),
                envelope=dict(widget='Checkbox',
                              value=False,
                              description='add envelope'),
                kind=dict(widget='Dropdown',
                          options=['linear', 'quadratic', 'cubic', 5, 7, 11],
                          value='cubic',
                          description='interp kind:'))
        ymaxlimit = kwargs.get('ymaxlimit', 0.0)
        if isinstance(ymaxlimit, float) and 0 < ymaxlimit < 1:
            maxlimit = fieldm.max() * ymaxlimit
            jpass = fieldm.max(axis=1) >= maxlimit
            jlist = [i for i, j in enumerate(jpass) if j]
        else:
            jlist = 'all'
        envelope = kwargs.get('envelope', False)
        kind = kwargs.get('kind', 'cubic')
        if envelope:
            maxfm = fieldm.max(axis=0)
            tmp = np.gradient(maxfm, rr)
            zerolimit = tmp.max()*1e-6
            add_indexs = []
            # increase
            for i in range(len(tmp)//2):
                if tmp[i] >= - zerolimit:
                    add_indexs.append(i)
                else:
                    break
            # decrease
            for i in range(len(tmp)-1, len(tmp)//2, -1):
                if tmp[i] <= zerolimit:
                    add_indexs.append(i)
                else:
                    break
            Y = tools.high_envelope(
                maxfm, X=rr, kind=kind, add_indexs=add_indexs)
            newX, newY = tools.near_peak(
                Y, X=rr, intersection=True, lowerlimit=1.0/np.e, select='1')
            idxmax = np.argmax(newY)
            Xmax, Ymax = newX[idxmax], newY[idxmax]
        else:
            Y, newX, newY, Xmax, Ymax = 'n', 'n', 'n', 'n', 'n'
        acckwargs = dict(ymaxlimit=ymaxlimit, envelope=envelope, kind=kind)
        return jlist, acckwargs, Y, newX, newY, Xmax, Ymax

    _dig.__doc__ = _remove_add_some_lines.__doc__

    def _post_dig(self, results):
        r = results
        if r['jlist'] == 'all':
            mt, _ = r['fieldm'].shape
            jlist = range(mt)
        else:
            jlist = r['jlist']
        LINE = [(r['rr'], r['fieldm'][j, :]) for j in jlist]
        if type(r['envY']) is np.ndarray and type(r['envYp']) is np.ndarray:
            LINE.append((r['rr'], r['envY'],
                         'envelope, $r/a(max)=%.6f$' % r['envXmax']))
            dx = r['envXp'][-1] - r['envXp'][0]
            halfY = r['envYmax'] / np.e
            flatYp = np.linspace(halfY, halfY, len(r['envXp']))
            LINE.append((r['envXp'], flatYp, r'$\Delta r/a(1/e) = %.6f$' % dx))
        r0, r1 = np.round(r['rr'][[0, -1]], decimals=2)
        return dict(LINE=LINE, title=r['title'],
                    xlabel=r'$r/a$', xlim=[r0, r1])
