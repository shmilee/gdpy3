# -*- coding: utf-8 -*-

# Copyright (c) 2019-2020 shmilee

'''
Source fortran code:

eqplot.F90, subroutine eqplot

1. first part, 1D radial plots, datap(lsp),data1d(lsp)
  write(ieq,101)nplot,nrad
  write(ieq,102)datap
  !!! 1
  write(ieq,102)data1d
  ...
  !!! 29
  write(ieq,102)data1d

2. second part, 2D contour plots on poloidal plane,
datax(mpsi/mskip+1,lst),dataz(mpsi/mskip+1,lst),data2d(mpsi/mskip+1,lst,5)
  write(ieq,101)nplot,mpsi/mskip+1,lst
  !0-1: mesh points on (X,Z)
  write(ieq,102)datax,dataz
  !2: b-field
  write(ieq,102)data2d(:,:,1)
  !3: Jacobian
  write(ieq,102)data2d(:,:,2)
  !4: icurrent
  write(ieq,102)data2d(:,:,3)
  !5: zeta2phi
  write(ieq,102)data2d(:,:,4)
  !6: delb
  write(ieq,102)data2d(:,:,5)

'''

import numpy
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog

_all_Converters = ['EquilibriumConverter']
_all_Diggers = ['EquilibriumPsi1DDigger', 'EquilibriumRadial1DDigger',
                'EquilibriumErro1DDigger', 'EquilibriumPoloidalDigger',
                'EquilibriumMeshDigger', 'EquilibriumThetaDigger']
__all__ = _all_Converters + _all_Diggers


class EquilibriumConverter(Converter):
    '''
    Equilibrium data

    1) first part, 1D radial plots. 'nplot-1d', 'nrad'. 'nplot-1d' + 1 = 30.
       Shape of '1d-data' is ('nplot-1d' + 1, nrad). 30 plots order:
       0'radial-axis-using-poloidal-flux-function',
       1'sqaure-root-of-normalized-toroidal-flux-function',
       2'minor-radius', 3'major-radius',
       4'Te', 5'-d(ln(Te))/dr', 6'ne', 7'-d(ln(ne))/dr',
       8'Ti', 9'-d(ln(Ti))/dr', 10'ni', 11'-d(ln(ni))/dr',
       12'Tf', 13'-d(ln(Tf))/dr', 14'nf', 15'-d(ln(nf))/dr',
       16'zeff', 17'toroidal-rotation', 18'radial-electric-field',
       19'q-profile', 20'd(ln(q))/dpsi',
       21'gcurrent-profile', 22'pressure-profile',
       23'minor-radius', 24'toroidal-flux', 25'rgpsi', 26'psitor', 27'psirg',
       28'error-of-spline-cos', 29'error-of-spline-sin'.

    2) second part, 2D contour plots on poloidal plane.
       'nplot-2d', 'mpsi/mskip+1', 'lst'.
       Shape of 2D data is (mpsi/mskip+1, lst).
       'mesh-points-on-X', 'mesh-points-on-Z',
       'b-field', 'Jacobian', 'icurrent', 'zeta2phi', 'delb'.
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = ['^(?P<section>equilibrium)\.out$',
                    '.*/(?P<section>equilibrium)\.out$']
    _datakeys = (
        # 1. first part, 1D
        'nplot-1d', 'nrad', '1d-data',
        # 2. second part, 2D
        'nplot-2d', 'mpsi-over-mskip+1', 'lst',
        'mesh-points-on-X', 'mesh-points-on-Z',
        'b-field', 'Jacobian', 'icurrent', 'zeta2phi', 'delb')

    def _convert(self):
        '''Read 'equilibrium.out'.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        # 1. first part
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:3]))
        sd.update({'nplot-1d': int(outdata[0].strip()),
                   'nrad': int(outdata[1].strip())})
        size1 = (sd['nplot-1d'] + 1) * sd['nrad']
        shape1 = ((sd['nplot-1d'] + 1), sd['nrad'])
        data1 = numpy.array([float(n.strip()) for n in outdata[2:2 + size1]])
        data1 = data1.reshape(shape1, order='C')
        sd.update({'1d-data': data1})
        # 2. second part
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[3:6]))
        index2 = 2 + size1
        sd.update({'nplot-2d': int(outdata[index2].strip()),
                   'mpsi-over-mskip+1': int(outdata[index2 + 1].strip()),
                   'lst': int(outdata[index2 + 2].strip())})
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[6:]))
        size2 = (sd['nplot-2d'] + 2) * sd['mpsi-over-mskip+1'] * sd['lst']
        shape2 = ((sd['nplot-2d'] + 2), sd['mpsi-over-mskip+1'] * sd['lst'])
        data2 = numpy.array([float(n.strip())
                             for n in outdata[index2 + 3:index2 + 3 + size2]])
        data2 = data2.reshape(shape2, order='C')
        shape3 = (sd['mpsi-over-mskip+1'], sd['lst'])
        for i, key in enumerate(self._datakeys[6:]):
            sd.update({key: data2[i].reshape(shape3, order='F')})

        return sd


_1d_data_misc = {
    'minor_r': dict(
        title='inverse aspec-ratio from profile data', index=2),
    'major_r': dict(title='major radius from profile data', index=3),
    'Te': dict(title='Te', index=4),
    'L_Te-1': dict(title='-d(ln(Te))/dr', index=5),
    'ne': dict(title='ne', index=6),
    'L_ne-1': dict(title='-d(ln(ne))/dr', index=7),
    'Ti': dict(title='Ti', index=8),
    'L_Ti-1': dict(title='-d(ln(Ti))/dr', index=9),
    'ni': dict(title='ni', index=10),
    'L_ni-1': dict(title='-d(ln(ni))/dr', index=11),
    'Tf': dict(title='Tf', index=12),
    'L_Tf-1': dict(title='-d(ln(Tf))/dr', index=13),
    'nf': dict(title='nf', index=14),
    'L_nf-1': dict(title='-d(ln(nf))/dr', index=15),
    'zeff': dict(title=r'$Z_{eff}$', index=16),
    'tor_rotation': dict(title='toroidal rotation', index=17),
    'Er': dict(title=r'$E_r$', index=18),
    'q': dict(title='q profile', index=19),
    'shear': dict(title='shear d(ln(q))/dpsi', index=20),
    'gcurrent': dict(title='gcurrent profile', index=21),
    'pressure': dict(title='pressure profile', index=22),
    'tor_flux': dict(title='toroidal flux', index=24),
    'rg': dict(title='radial grid', index=25),
}


class EquilibriumPsi1DDigger(Digger):
    '''
    X -> psi of radius, Z_eff, rotation, E_r, q, shear, pressure ...
    and T, n of ion, electron, fastion
    '''
    __slots__ = ['_numseed']
    itemspattern = [r'^(?P<section>equilibrium)/1d-data$']
    _misc = _1d_data_misc.copy()
    _misc['r'] = dict(title='minor radius r(psi)', index=23)
    numseeds = list(_misc.keys())
    post_template = 'tmpl_line'

    def _set_fignum(self, numseed=None):
        self._fignum = '%s(psi)' % numseed
        self._numseed = numseed

    def _dig(self, kwargs):
        data = self.pckloader.get(self.srckeys[0])
        X = data[0]
        return dict(X=X, xlim=[min(X), max(X)],
                    Y=data[self._misc[self._numseed]['index']],
                    title=self._misc[self._numseed]['title']), {}

    def _post_dig(self, results):
        r = results
        return dict(LINE=[(r['X'], r['Y'])], title=r['title'],
                    xlabel=r'$\psi$', xlim=r['xlim'])


class EquilibriumRadial1DDigger(Digger):
    '''
    X -> r of psi, Z_eff, rotation, E_r, q, shear, pressure ...
    and T, n of ion, electron, fastion
    '''
    __slots__ = ['_numseed']
    itemspattern = [r'^(?P<section>equilibrium)/1d-data$']
    commonpattern = ['equilibrium/nrad']
    _misc = _1d_data_misc.copy()
    _misc['psi'] = dict(title='psi(r)', index=0)
    numseeds = list(_misc.keys())
    post_template = 'tmpl_line'

    def _set_fignum(self, numseed=None):
        self._fignum = '%s(r)' % numseed
        self._numseed = numseed

    def _dig(self, kwargs):
        data, nrad = self.pckloader.get_many(*self.srckeys, *self.extrakeys)
        X = data[23] / data[23][nrad - 1]
        return dict(X=X, xlim=[min(X), max(X)],
                    Y=data[self._misc[self._numseed]['index']],
                    title=self._misc[self._numseed]['title']), {}

    def _post_dig(self, results):
        r = results
        return dict(LINE=[(r['X'], r['Y'])], title=r['title'],
                    xlabel=r'radius $r$', xlim=r['xlim'])


class EquilibriumErro1DDigger(Digger):
    '''X -> [0, pi/2], error of spline cos, sin'''
    __slots__ = ['_numseed']
    itemspattern = [r'^(?P<section>equilibrium)/1d-data$']
    commonpattern = ['equilibrium/nrad']
    _misc = {'cos': dict(title='error of spline cos', index=28),
             'sin': dict(title='error of spline sin', index=29)}
    numseeds = list(_misc.keys())
    post_template = 'tmpl_line'

    def _set_fignum(self, numseed=None):
        self._fignum = 'error-%s' % numseed
        self._numseed = numseed

    def _dig(self, kwargs):
        data, nrad = self.pckloader.get_many(*self.srckeys, *self.extrakeys)
        X = numpy.array(range(1, nrad + 1)) * (numpy.pi / 2 / nrad)
        return dict(X=X, xlim=[min(X), max(X)],
                    Y=data[self._misc[self._numseed]['index']],
                    title=self._misc[self._numseed]['title']), {}

    def _post_dig(self, results):
        r = results
        return dict(LINE=[(r['X'], r['Y'])], title=r['title'],
                    xlabel=r'$\theta$', xlim=r['xlim'])


class EquilibriumPoloidalDigger(Digger):
    '''b-field, Jacobian, icurrent, zeta2phi, delb on poloidal'''
    __slots__ = []
    nitems = '+'
    itemspattern = [r'^(?P<section>equilibrium)/'
                    + '(?P<par>(?:b-field|Jacobian|icurrent|zeta2phi|delb))$',
                    r'^(?P<section>equilibrium)/mesh-points-on-(?:X|Z)$']
    post_template = 'tmpl_contourf'

    def _set_fignum(self, numseed=None):
        self._fignum = self.section[1]

    def _dig(self, kwargs):
        Z, X, Y = self.pckloader.get_many(*self.srckeys)
        return dict(X=X, Y=Y, Z=Z, title=self.fignum), {}

    def _post_dig(self, results):
        results.update(xlabel=r'$R(R_0)$', ylabel=r'$Z(R_0)$', aspect='equal')
        return results


class EquilibriumMeshDigger(Digger):
    '''poloidal mesh'''
    __slots__ = []
    nitems = '+'
    itemspattern = [r'^(?P<section>equilibrium)/mesh-points-on-(?:X|Z)$',
                    r'^(?P<section>equilibrium)/mpsi-over-mskip\+1',
                    r'^(?P<section>equilibrium)/lst']
    post_template = 'tmpl_line'

    def _set_fignum(self, numseed=None):
        self._fignum = 'poloidal_mesh'

    def _dig(self, kwargs):
        X, Y, lsp, lst = self.pckloader.get_many(
            *self.srckeys, *self.extrakeys)
        LINE1, LINE2 = [], []
        for i in range(lsp):
            x, y = X[i], Y[i]
            x, y = numpy.append(x, x[0]), numpy.append(y, y[0])
            LINE1.append((x, y))
        for i in range(lst):
            x, y = X[:, i], Y[:, i]
            LINE2.append((x, y))
        return dict(LINEs1=numpy.array(LINE1), LINEs2=numpy.array(LINE2),
                    title='poloidal mesh', xlabel='R', ylabel='Z'), {}

    def _post_dig(self, results):
        r = results
        return dict(
            LINE=list(r['LINEs1']) + list(r['LINEs2']), title=r['title'],
            xlabel=r'$R(R_0)$', ylabel=r'$Z(R_0)$', aspect='equal')


class EquilibriumThetaDigger(Digger):
    '''X -> theta of b-field, Jacobian, icurrent zeta2phi, delb at psi=isp'''
    __slots__ = []
    nitems = '?'
    itemspattern = [r'^(?P<section>equilibrium)/'
                    + '(?P<par>(?:b-field|Jacobian|icurrent|zeta2phi|delb'
                    + '|1d-data))$']  # for 'gq_plus_I/BB'
    commonpattern = ['equilibrium/mpsi-over-mskip\+1', 'equilibrium/lst']
    post_template = 'tmpl_line'

    def _set_fignum(self, numseed=None):
        self._fignum = '%s:theta' % self.section[1]
        if self.section[1] == '1d-data':
            self._fignum = 'gq_plus_I/BB:theta'
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *isp*: int
            fix psi=isp, default 'mpsi-over-mskip+1' - 1
        '''
        Z, lsp, lst = self.pckloader.get_many(*self.srckeys, *self.extrakeys)
        isp = lsp - 1
        acckwargs = {'isp': isp}
        if 'isp' in kwargs and isinstance(kwargs['isp'], int):
            if 1 < kwargs['isp'] < lsp - 1:
                isp = kwargs['isp']
                acckwargs['isp'] = isp
        if self.kwoptions is None:
            self.kwoptions = dict(
                isp=dict(
                    widget='IntSlider',
                    rangee=(0, lsp - 1, 1),
                    value=isp,
                    description='psi=isp:'))
        dlog.parm("fix psi=isp=%d. Maximal isp=%d." % (isp, lsp - 1))
        X = 2.0 * numpy.pi * numpy.array(range(lst + 1)) / lst
        if self.fignum == 'gq_plus_I/BB:theta':
            g = Z[21][isp]
            q = Z[19][isp]
            # extrakeys, not check
            icurrent, bfield = self.pckloader.get_many(
                'equilibrium/icurrent', 'equilibrium/b-field')
            I, B = icurrent[isp], bfield[isp]
            Y = (g * q + I) / (B * B)
            title = '(gq+I)/B^2'
        else:
            Y = Z[isp]
            title = self.section[1]
        Y = numpy.append(Y, Y[0])
        title = r'%s ($\theta$) at psi=isp=%d' % (title, isp)
        return dict(X=X, Y=Y, title=title, xlim=[min(X), max(X)]), acckwargs

    _post_dig = EquilibriumErro1DDigger._post_dig
