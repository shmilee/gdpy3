# -*- coding: utf-8 -*-

# Copyright (c) 2019-2023 shmilee

'''
Source fortran code:

v3.21-222-g12dd9b6
------------------

shmilee.F90, subroutine zetapsi3d_init
  do i=1, size(r_params)
      j_list(i)=int(r_params(i)/2.0*real(mtdiag))
  end do
  mzeach=min(zgridmax,mtheta(iflux))/mtoroidal

shmilee.F90, subroutine zetapsi3d_diagnosis
  write(fdum,'("phi_dir/zetapsi3d",i5.5,"_tor",i4.4,".out")') (mstepall+istep),myrank_toroidal
  open(iozetapsi,file=trim(fdum),status='replace')
  if(myrank_toroidal==0)then
    ! parameters: shape of data; all selected j, last one is mtdiag; and field info
    write(iozetapsi,101)mzeach,mpsi+1, size(j_list), j_list, zetapsi3d_nfield, zetapsi3d_fields
  endif
  write(iozetapsi,102)zp3d !(mzeach,0:mpsi,size(j_list),zetapsi3d_nfield)

v3.21-250-g43c648b
------------------

shmilee.F90, subroutine zetapsi3d_diagnosis
  write(fdum,'("phi_dir/zetapsi3d",i5.5,".out")') (mstepall+istep)
  open(iozetapsi,file=trim(fdum),status='replace')
  ! parameters: shape of data; all selected j, last one is mtdiag; and field info
  write(iozetapsi,101) mzeach, mpsi+1, size(j_list), j_list, zetapsi3d_nfield, zetapsi3d_fields, mtoroidal
  write(iozetapsi,102) allzp3d !(mzeach,0:mpsi,size(j_list),zetapsi3d_nfield,mtoroidal)
'''
import re
import numpy as np

from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog
from .snapshot import SnapshotFieldmDigger
from .gtc import Ndigits_tstep
from .. import tools

_all_Converters = ['ZetaPsi3DConverter', 'ZetaPsi3DoldConverter']
_all_Diggers = ['ZetaPsi3DDigger', 'ZetaPsi3DCorrLenDigger',
                'ZetaPsi3DFieldnDigger', 'ZetaPsi3DFieldnkzetaDigger']
__all__ = _all_Converters + _all_Diggers


class ZetaPsi3DConverter(Converter):
    '''
    Diagnosis field(zeta,psi) Data for selected theta

    Shape of array data is (mzeach*mtoroidal,mpsi+1)
    '''
    __slot__ = []
    nitems = '?'
    itemspattern = ['^phi_dir/(?P<section>zetapsi3d\d{5})\.out$',
                    '.*/phi_dir/(?P<section>zetapsi3d\d{5})\.out$']
    _datakeys = (
        # 1. parameters
        'mzeach', 'mpsi+1', 'nj', 'j_list', 'nfield', 'zp3d_fields',
        'mtoroidal',
        # 2. field(zeta,psi,nj),
        'phi', 'apara', 'fluidne',  # -%d % j
        'densityi', 'temperi', 'densitye', 'tempere', 'densityf', 'temperf'
    )

    @property
    def group(self):
        return self._group.replace('zetapsi3d', 'zp3d')

    @property
    def groupnote(self):
        return self._group

    def _convert(self):
        '''Read 'phi_dir/zetapsi3d%05d.out'.'''
        with self.rawloader.get(self.files) as fid:
            # parameters
            mzeach, mpsi1, nj = (int(fid.readline()) for j in range(3))
            j_list = [int(fid.readline()) for j in range(nj)]
            nfield = int(fid.readline())
            zp3d_fields = [int(fid.readline().strip()) for v in range(nfield)]
            fields_name = []
            for nf in zp3d_fields:
                fields_name.append(self._datakeys[6+nf])  # nf=1 -> phi
            assert len(fields_name) == nfield
            mtoroidal = int(fid.readline())
            # data
            shape = (mzeach, mpsi1, nj, nfield, mtoroidal)
            outdata = np.array([float(n.strip()) for n in fid.readlines()])
        outdata = outdata.reshape(shape, order='F')
        # 1. parameters
        clog.debug("Filling datakeys: %s ..." % 'mzeach, nj, j_list')
        sd = dict(mzeach=mzeach, nj=nj, j_list=j_list)
        # 2. data
        for nf in range(nfield):
            for idx, j in enumerate(j_list):
                key = r'%s-%d' % (fields_name[nf], j)
                fdata = outdata[:, :, idx, nf, :]
                fdata = fdata.transpose(0, 2, 1)  # sawp 2nd and 3rd axes
                fdata = fdata.reshape(-1, mpsi1)  # flatten 1st, 2nd axes
                clog.debug("Filling datakeys: %s ..." % key)
                sd[key] = fdata
        return sd


class ZetaPsi3DoldConverter(ZetaPsi3DConverter):
    __slot__ = []
    nitems = '+'
    itemspattern = ['^phi_dir/(?P<section>zetapsi3d\d{5})_tor\d{4}\.out$',
                    '.*/phi_dir/(?P<section>zetapsi3d\d{5})_tor\d{4}\.out$']
    _short_files_subs = (0, '^(.*\d{5}_tor)\d{4}\.out$', r'\1*.out')

    def _convert(self):
        '''Read 'phi_dir/zetapsi3d%05d_tor%04d.out'.'''
        fdata = []
        # tor0000.out
        f = self.files[0]
        with self.rawloader.get(f) as fid:
            # parameters
            mzeach, mpsi1, nj = (int(fid.readline()) for j in range(3))
            j_list = [int(fid.readline()) for j in range(nj)]
            nfield = int(fid.readline())
            zp3d_fields = [int(fid.readline().strip()) for v in range(nfield)]
            fields_name = []
            for nf in zp3d_fields:
                fields_name.append(self._datakeys[6+nf])  # nf=1 -> phi
            assert len(fields_name) == nfield
            # data
            shape = (mzeach, mpsi1, nj, nfield)
            outdata = np.array([float(n.strip()) for n in fid.readlines()])
            fdata.extend(outdata.reshape(shape, order='F'))
        # tor0001.out ...
        for f in self.files[1:]:
            with self.rawloader.get(f) as fid:
                outdata = np.array([float(n.strip()) for n in fid.readlines()])
                fdata.extend(outdata.reshape(shape, order='F'))
        fdata = np.array(fdata)
        mtoroidal = len(self.files)
        assert fdata.shape == (mzeach*mtoroidal, mpsi1, nj, nfield)
        # 1. parameters
        clog.debug("Filling datakeys: %s ..." % 'mzeach, nj, j_list')
        sd = dict(mzeach=mzeach, nj=nj, j_list=j_list)
        # 2. data
        for nf in range(nfield):
            for idx, j in enumerate(j_list):
                key = r'%s-%d' % (fields_name[nf], j)
                clog.debug("Filling datakeys: %s ..." % key)
                sd[key] = fdata[:, :, idx, nf]
        return sd


field_tex_str = {
    'phi': r'\phi',
    'apara': r'A_{\parallel}',
    'fluidne': r'fluid n_e',
    'densityi': r'\delta n_i',
    'densitye': r'\delta n_e',
    'densityf': r'\delta n_f',
    'temperi': r'\delta T_i',
    'tempere': r'\delta T_e',
    'temperf': r'\delta T_f',
}


class ZetaPsi3DDigger(Digger):
    '''field(zeta,psi) at theta=j/mtdiag*2pi'''
    __slots__ = ['field', '_deg', '_rad', 'thetastr', 'timestr']
    nitems = '+'
    itemspattern = ['^(?P<section>zp3d\d{5})/(?P<field>(?:phi|apara|fluidne|densityi'
                    + '|temperi|densitye|tempere|densityf|temperf))-(?P<j>\d+)']
    commonpattern = ['gtc/tstep', 'gtc/arr2', 'gtc/a_minor', 'gtc/mtdiag',
                     '^(?P<section>zp3d\d{5})/j_list']
    post_template = 'tmpl_contourf'

    def _set_fignum(self, numseed=None):
        self.field = self.section[1]
        j = int(self.section[2])
        self._deg, self._rad,  self.thetastr = self._get_deg_rad_thetastr(j)
        self._fignum = '%s_%03d' % (self.field, round(self._deg))
        _, self.timestr = self._get_timestr()
        self.kwoptions = None

    _deg_rad_thetastr_timestr_cache = {}

    def _get_deg_rad_thetastr(self, j):
        ''' Return deg, rad, thetastr '''
        cache_key = (self.pckloader, j, 'deg&rad&thetastr')
        if cache_key not in self._deg_rad_thetastr_timestr_cache:
            k = self.pckloader.refind(self.commonpattern[-1])[0]
            j_list = self.pckloader.get(k)
            assert j in j_list
            mtdiag = self.pckloader.get('gtc/mtdiag')
            for _j in j_list:  # cache all
                part = _j / mtdiag
                deg, rad = part*360, part*2*np.pi
                s1 = r'$\theta=%.3f=%g^\circ$' % (round(rad, ndigits=3), deg)
                _ckey = (self.pckloader, _j, 'deg&rad&thetastr')
                self._deg_rad_thetastr_timestr_cache[_ckey] = (deg, rad, s1)
        return self._deg_rad_thetastr_timestr_cache[cache_key]

    def _get_timestr(self):
        ''' Return time, timestr '''
        cache_key = (self.pckloader, self.group, 'time&timestr')
        if cache_key not in self._deg_rad_thetastr_timestr_cache:
            istep = int(re.match('.*zp3d(\d{5,7}).*', self.group).groups()[0])
            tstep = self.pckloader.get('gtc/tstep')
            time = round(istep * tstep, Ndigits_tstep)
            s2 = r'istep=%d, time=%s$R_0/c_s$' % (istep, time)
            self._deg_rad_thetastr_timestr_cache[cache_key] = (time, s2)
        return self._deg_rad_thetastr_timestr_cache[cache_key]

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *use_ra*: bool
            use psi or r/a, default False
        '''
        Z = self.pckloader.get(self.srckeys[0])
        y, x = Z.shape
        if self.kwoptions is None:
            self.kwoptions = dict(
                use_ra=dict(widget='Checkbox',
                            value=False,
                            description='X: r/a'))
        fstr = field_tex_str[self.field]
        # use_ra, arr2 [1,mpsi-1], so y0>=1, y1<=mpsi
        if kwargs.get('use_ra', False):
            try:
                arr2, a = self.pckloader.get_many('gtc/arr2', 'gtc/a_minor')
                rr = arr2[:, 1] / a  # index [0, mpsi-2]
                x0 = 1
                x1 = x - 1
                X = rr[x0-1:x1-1]
                Z = Z[:, x0:x1]
            except Exception:
                dlog.warning("Cannot use r/a!", exc_info=1)
            else:
                title = r'$%s(\zeta,r)$, %s, %s' % (
                    fstr, self.thetastr, self.timestr)
                xlabel = r'$r/a$'
                acckwargs = dict(use_ra=True)
        else:
            title = r'$%s(\zeta,\psi)$, %s, %s' % (
                fstr, self.thetastr, self.timestr)
            xlabel = r'$\psi$(mpsi)'
            acckwargs = dict(use_ra=False)
            X = np.arange(0, x)
        return dict(X=X, Y=np.arange(0, y) / y * 2 * np.pi, Z=Z,
                    xlabel=xlabel, ylabel=r'$\zeta$', title=title), acckwargs

    def _post_dig(self, results):
        return results


class BreakDigDoc(Digger):
    pass


class ZetaPsi3DCorrLenDigger(BreakDigDoc, ZetaPsi3DDigger):
    '''field(zeta,psi) correlation (d_zeta, d_psi) at at theta=j/mtdiag*2pi'''
    __slots__ = []
    post_template = ('tmpl_z111p', 'tmpl_contourf', 'tmpl_line')

    def _set_fignum(self, numseed=None):
        super(ZetaPsi3DCorrLenDigger, self)._set_fignum(numseed=numseed)
        self._fignum = '%s_%03d_corrlen' % (self.field, round(self._deg))
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *mdpsi*, *mdzeta*: int
            set dpsi dzeta range, max mpsi//2, mzeta//2
        *use_ra*: bool
            use psi or r/a, default True
        '''
        Z = self.pckloader.get(self.srckeys[0])
        y, x = Z.shape
        # use_ra, arr2 [1,mpsi-1], so y0>=1, y1<=mpsi
        if kwargs.get('use_ra', True):
            try:
                arr2, a = self.pckloader.get_many('gtc/arr2', 'gtc/a_minor')
                rr = arr2[:, 1] / a  # index [0, mpsi-2]
                Z = Z[:, 1:x-1]
                y, x = Z.shape
            except Exception:
                dlog.warning("Cannot use r/a!", exc_info=1)
                use_ra = False
            else:
                use_ra = True
        else:
            use_ra = False
        # if Z size is too large, cal corr will be very slow
        max_x, max_y = 400, 1536
        step_x = round(x/max_x) if x > max_x else 1
        step_y = round(y/max_y) if y > max_y else 1
        if step_x != 1 or step_y != 1:
            if use_ra:
                rr = rr[::step_x]
            Z = Z[::step_y, ::step_x]
            dlog.parm('Too large data of %s(zeta,psi), slice it: %s -> %s'
                      % (self.field, (y, x), Z.shape))
            y, x = Z.shape
        else:
            dlog.parm('Shape of %s(zeta,psi) is %s.' % (self.field, (y, x)))
        maxmdpsi, maxmdzeta = int(x/2+1), int(y/2+1)
        mdpsi, mdzeta = kwargs.get('mdpsi', None), kwargs.get('mdzeta', None)
        if not (isinstance(mdpsi, int) and mdpsi <= maxmdpsi):
            mdpsi = x // 2
        if not (isinstance(mdzeta, int) and mdzeta <= maxmdzeta):
            Zz = Z[:, int(Z.argmax(axis=1).mean())]
            Zz = tools.savgolay_filter(Zz, info='field(zeta)')
            index = (np.diff(np.sign(np.gradient(Zz))) < 0).nonzero()[0]
            mdzeta = int(np.diff(index).mean())
            # print(Zz,index)
            # print('---------------')
            # print(mdzeta, mdzeta < y//32, y//8)
            mdzeta *= 4 if mdzeta < y//32 else 3
            mdzeta = min(mdzeta, y//8)
        acckwargs = dict(mdpsi=mdpsi, mdzeta=mdzeta, use_ra=use_ra)
        dlog.parm("Use dpsi dzeta range: mdpsi=%s, mdzeta=%s. "
                  "Maximal mdpsi=%s, mdzeta=%s"
                  % (mdpsi, mdzeta, maxmdpsi, maxmdzeta))
        if self.kwoptions is None:
            self.kwoptions = dict(
                mdpsi=dict(
                    widget='IntSlider',
                    rangee=(1, maxmdpsi, 1),
                    value=mdpsi,
                    description='mdpsi:'),
                mdzeta=dict(
                    widget='IntSlider',
                    rangee=(1, maxmdzeta, 1),
                    value=mdzeta,
                    description='mdzeta:'),
                use_ra=dict(widget='Checkbox',
                            value=True,
                            description='X: r/a'))
        Xpsi = np.arange(0, mdpsi) * step_x
        Y = np.arange(0, mdzeta) * step_y / y * 2 * np.pi
        fstr = field_tex_str[self.field]
        if use_ra:
            # print(rr, rr.size, Z.shape, step_x)
            title1 = r'Correlation $%s(\Delta\zeta,\Delta r)$, %s, %s' % (
                fstr, self.thetastr, self.timestr)
            xlabel = r'$\Delta r/a$'
            tau, vdz, X = tools.correlation(
                Z, 0, y, 0, x, mdzeta, mdpsi, ruler_c=rr)
        else:
            title1 = r'Correlation $%s(\Delta\zeta,\Delta\psi)$, %s, %s' % (
                fstr, self.thetastr, self.timestr)
            xlabel = r'$\Delta\psi(mpsi)$'
            tau, vdz, vdp = tools.correlation(Z, 0, y, 0, x, mdzeta, mdpsi)
            X = Xpsi
        mtau = tau.max(axis=0)
        index = np.where(mtau <= 1.0/np.e)[0]
        if index.size > 0:
            # line intersection
            i, j = index[0] - 1,  index[0]
            Lpsi, y = tools.intersection_4points(
                Xpsi[i], mtau[i], Xpsi[j], mtau[j],
                Xpsi[i], 1.0/np.e, Xpsi[j], 1.0/np.e)
            if use_ra:
                L, y = tools.intersection_4points(
                    X[i], mtau[i], X[j], mtau[j],
                    X[i], 1.0/np.e, X[j], 1.0/np.e)
            else:
                L = Lpsi
        else:
            L, Lpsi = X[-1], Xpsi[-1]  # over mdpsi
            dlog.parm("Increase mdpsi to find correlation length!")
        if use_ra:
            title2 = r'$C(\Delta r)$, $C_r(\Delta r=%.6f)=1/e$' % L
            dlog.parm("Find correlation length: L=%.6f, Lpsi=%.3f" % (L, Lpsi))
        else:
            title2 = r'$C(\Delta\psi)$, $C(\Delta\psi=%.3f)=1/e$' % Lpsi
            dlog.parm("Find correlation length: Lpsi=%.3f" % Lpsi)
        mtauz, Lz, title3 = self._find_correLz(tau, Y)
        return dict(X=X, Y=Y, tau=tau, mtau=mtau, L=L, Lpsi=Lpsi,
                    xlabel=xlabel, title1=title1, title2=title2,
                    xname=r'r' if use_ra else r'\psi',
                    Lr=L, mtauz=mtauz, Lz=Lz, title3=title3), acckwargs

    @staticmethod
    def _find_correLz(tau, Y):
        mtau = tau.max(axis=1)
        index = np.where(mtau <= 1.0/np.e)[0]
        if index.size > 0:
            # line intersection
            i, j = index[0] - 1,  index[0]
            Lz, y = tools.intersection_4points(
                Y[i], mtau[i], Y[j], mtau[j],
                Y[i], 1.0/np.e, Y[j], 1.0/np.e)
        else:
            Lz = Y[-1]  # over mdzeta
            dlog.parm("Increase mdzeta to find correlation length!")
        title3 = r'$C(\Delta\zeta)$, $C(\Delta\zeta=%.3f)=1/e$' % Lz
        dlog.parm("Find correlation length: Lzeta=%.3f" % Lz)
        return mtau, Lz, title3

    def _post_dig(self, results):
        r = results
        ax1_calc = dict(
            X=r['X'], Y=r['Y'], Z=r['tau'], clabel_levels=[1/np.e],
            title=r['title1'], xlabel=r['xlabel'], ylabel=r'$\Delta\zeta$')
        ax2_calc = dict(
            LINE=[
                (r['X'], r['mtau'], r'$C_r(\Delta %s)$' % r['xname']),
                ([r['X'][0], r['X'][-1]], [1/np.e, 1/np.e], '1/e'),
            ],
            title=r['title2'],
            xlabel=r['xlabel'],
            xlim=[r['X'][0], r['X'][-1]],
            ylim=[0 if r['mtau'].min() > 0 else r['mtau'].min(), 1],
        )
        if 'mtauz' in results and 'Lz' in results:
            mtauz, Lz, title3 = r['mtauz'], r['Lz'], r['title3']
        else:
            # maybe old results, without Lz
            mtauz, Lz, title3 = self._find_correLz(r['tau'], r['Y'])
        ax3_calc = dict(
            LINE=[
                (r['Y'], mtauz, r'$C_r(\Delta\zeta)$'),
                ([r['Y'][0], r['Y'][-1]], [1/np.e, 1/np.e], '1/e'),
            ],
            title=title3,
            xlabel=r'$\Delta\zeta$',
            xlim=[r['Y'][0], r['Y'][-1]],
            ylim=[0 if mtauz.min() > 0 else mtauz.min(), 1],
        )
        return dict(zip_results=[
            ('tmpl_contourf', 211, ax1_calc),
            ('tmpl_line', 223, ax2_calc),
            ('tmpl_line', 224, ax3_calc),
        ])


class ZetaPsi3DFieldnDigger(ZetaPsi3DDigger, SnapshotFieldmDigger):
    '''profile of field_n'''
    __slots__ = []
    nitems = '+'
    commonpattern = ['gtc/tstep', 'gtc/arr2', 'gtc/a_minor', 'gtc/mpsi']
    post_template = 'tmpl_line'

    def _set_fignum(self, numseed=None):
        super(ZetaPsi3DFieldnDigger, self)._set_fignum(numseed=numseed)
        self._fignum = '%s_%03d_n' % (self.field, round(self._deg))
        self.kwoptions = None

    def _dig(self, kwargs):
        data, dt, arr2, a, mpsi = self.pckloader.get_many(
            *self.srckeys, *self.common)
        mpsi1 = mpsi + 1
        Lz, Lr = data.shape
        if Lr != mpsi1:
            dlog.error("Invalid %s(zeta,psi) shape!" % self.field)
            return {}, {}
        rr = arr2[:, 1] / a
        fieldn = []
        for ipsi in range(1, mpsi1 - 1):
            y = data[:, ipsi]
            dy_ft = np.fft.fft(y)*Lz / 8  # why *Lz / 8
            fieldn.append(abs(dy_ft[:Lz//2]))
        fieldn = np.array(fieldn).T
        zlist, acckwargs, rr_s, Y_s, dr, dr_fwhm, envY, envXp, envYp, envXmax, envYmax = \
            self._remove_add_some_lines(fieldn, rr, kwargs)
        fstr = field_tex_str[self.field]
        return dict(
            rr=rr, fieldn=fieldn, zlist=zlist,
            rr_s=rr_s, Y_s=Y_s, dr=dr, dr_fwhm=dr_fwhm,
            envY=envY, envXp=envXp, envYp=envYp,
            envXmax=envXmax, envYmax=envYmax,
            title=r'$\left|%s,_n(r)\right|$, %s, %s' % (
                fstr, self.thetastr, self.timestr)
        ), acckwargs

    def _post_dig(self, results):
        r = results
        if r['zlist'] == 'all':
            mz, _ = r['fieldn'].shape
            zlist = range(mz)
        else:
            zlist = r['zlist']
        LINE = [(r['rr'], r['fieldn'][z, :]) for z in zlist]
        if r['dr'] != 'n':
            LINE.append(
                (r['rr_s'], r['Y_s'], r'$\delta r/a(gap,fwhm)=%.6f,%.6f$'
                 % (r['dr'], r['dr_fwhm'])))
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


class ZetaPsi3DFieldnkzetaDigger(BreakDigDoc, ZetaPsi3DFieldnDigger):
    '''contour/average profile of field_n or density_n'''
    __slots__ = []
    post_template = ('tmpl_z111p', 'tmpl_contourf', 'tmpl_line')

    def _set_fignum(self, numseed=None):
        super(ZetaPsi3DFieldnkzetaDigger, self)._set_fignum(numseed=numseed)
        self._fignum = '%skzeta' % self._fignum
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *n_max*: int, default mzeta//5
        *mean_weight_order*: int
            use fieldn^mean_weight_order as weight to average(n), default 4
        '''
        if self.kwoptions is None:
            self.kwoptions = dict(
                mean_weight_order=dict(widget='IntSlider',
                                       rangee=(2, 8, 2),
                                       value=4,
                                       description='mean n weight order:'))
        data, _ = super(ZetaPsi3DFieldnkzetaDigger, self)._dig(kwargs)
        rr, fieldn, title = data['rr'], data['fieldn'], data['title']
        maxnmode = fieldn.shape[0]*2//5  # (mzeta//2)*2//5
        n_max = kwargs.get('n_max', None)
        if not (isinstance(n_max, int) and n_max <= maxnmode):
            n_max = maxnmode
        n = np.arange(1, n_max + 1)
        fieldn = fieldn[:n_max, :]
        order = kwargs.get('mean_weight_order', 2)
        rho0, a = self.pckloader.get_many('gtc/rho0', 'gtc/a_minor')
        n2_r = np.array([np.average(n**order, weights=fieldn[:, i]**order)
                         for i in range(rr.size)])
        mean_n = np.power(n2_r, 1.0/order)
        kzrho0 = mean_n/(1+rr*a*np.cos(self._rad))*rho0
        dlog.parm("at r=0.5a, mean n=%.1f." % mean_n[rr.size//2])
        if 'n_max' not in self.kwoptions:
            self.kwoptions['n_max'] = dict(widget='IntSlider',
                                           rangee=(10, maxnmode, 10),
                                           value=maxnmode,
                                           description='n max limit:')
        acckwargs = dict(n_max=n_max, mean_weight_order=order)
        return dict(rr=rr, n=n, fieldn=fieldn, title=title,
                    mean_n=mean_n, kzrho0=kzrho0), acckwargs

    def _post_dig(self, results):
        r = results
        zip_results = [
            ('tmpl_contourf', 211, dict(
                X=r['rr'], Y=r['n'], Z=r['fieldn'], title=r['title'],
                xlabel=r'$r/a$', ylabel=r'n')),
            ('tmpl_line', 211, dict(LINE=[(r['rr'], r['mean_n'], 'mean n')])),
            ('tmpl_line', 212, dict(
                LINE=[(r['rr'], r['kzrho0'], r'mean n')],
                xlabel='r/a', ylabel=r'$k_{\zeta}\rho_0$')),
        ]
        return dict(zip_results=zip_results)
