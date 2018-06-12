# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Source fortran code:

v110922
-------

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
from ..core import DigCore, LayCore, FigInfo, LineFigInfo, PcolorFigInfo, log

__all__ = ['EquilibriumDigCoreV110922', 'EquilibriumLayCoreV110922']


class EquilibriumDigCoreV110922(DigCore):
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
    itemspattern = ['^(?P<section>equilibrium)\.out$',
                    '.*/(?P<section>equilibrium)\.out$']
    default_section = 'equilibrium'
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
            log.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        # 1. first part
        log.debug("Filling datakeys: %s ..." % str(self._datakeys[:3]))
        sd.update({'nplot-1d': int(outdata[0].strip()),
                   'nrad': int(outdata[1].strip())})
        size1 = (sd['nplot-1d'] + 1) * sd['nrad']
        shape1 = ((sd['nplot-1d'] + 1), sd['nrad'])
        data1 = numpy.array([float(n.strip()) for n in outdata[2:2 + size1]])
        data1 = data1.reshape(shape1, order='C')
        sd.update({'1d-data': data1})
        # 2. second part
        log.debug("Filling datakeys: %s ..." % str(self._datakeys[3:6]))
        index2 = 2 + size1
        sd.update({'nplot-2d': int(outdata[index2].strip()),
                   'mpsi-over-mskip+1': int(outdata[index2 + 1].strip()),
                   'lst': int(outdata[index2 + 2].strip())})
        log.debug("Filling datakeys: %s ..." % str(self._datakeys[6:]))
        size2 = (sd['nplot-2d'] + 2) * sd['mpsi-over-mskip+1'] * sd['lst']
        shape2 = ((sd['nplot-2d'] + 2), sd['mpsi-over-mskip+1'] * sd['lst'])
        data2 = numpy.array([float(n.strip())
                             for n in outdata[index2 + 3:index2 + 3 + size2]])
        data2 = data2.reshape(shape2, order='C')
        shape3 = (sd['mpsi-over-mskip+1'], sd['lst'])
        for i, key in enumerate(self._datakeys[6:]):
            sd.update({key: data2[i].reshape(shape3, order='F')})

        return sd


class Plot1DPsiFigInfo(LineFigInfo):
    '''Figures X -> psi of radius, Z_eff, E_r, rotation, shear ...'''
    __slots__ = ['d1']
    _misc = {
        'minor_r': dict(
            title='inverse aspec-ratio from profile data', index=2),
        'major_r': dict(title='major radius from profile data', index=3),
        'zeff': dict(title=r'$Z_{eff}$', index=16),
        'tor_rotation': dict(title='toroidal rotation', index=17),
        'Er': dict(title=r'$E_r$', index=18),
        'shear': dict(title='shear d(ln(q))/dpsi', index=20),
        'r': dict(title='minor radius r(psi)', index=23),
    }
    figurenums = ['%s:psi' % d1 for d1 in _misc.keys()]
    numpattern = r'^(?P<d1>(?:%s)):psi$' % '|'.join(_misc.keys())

    def _get_srckey_extrakey(self, fignum):
        groupdict = self._pre_check_get(fignum, 'd1')
        self.d1 = groupdict['d1']
        return ['1d-data'], []

    def _get_data_LINE_title_etc(self, data):
        X = data['1d-data'][0]
        title = self._misc[self.d1]['title']
        Y = data['1d-data'][self._misc[self.d1]['index']]
        return dict(LINE=[(X, Y)], title=title,
                    xlabel='psi', xlim=[min(X), max(X)])


class Plot1DrFigInfo(LineFigInfo):
    '''Figures X -> r of psi, radial grid'''
    __slots__ = ['d1']
    _misc = {'psi': dict(title='psi(r)', index=0),
             'rg': dict(title='rg(r)', index=25)}
    figurenums = ['%s:r' % d1 for d1 in _misc.keys()]
    numpattern = r'^(?P<d1>(?:%s)):r$' % '|'.join(_misc.keys())

    def _get_srckey_extrakey(self, fignum):
        groupdict = self._pre_check_get(fignum, 'd1')
        self.d1 = groupdict['d1']
        return ['nrad', '1d-data'], []

    def _get_data_LINE_title_etc(self, data):
        X = data['1d-data'][23] / data['1d-data'][23][data['nrad'] - 1]
        title = self._misc[self.d1]['title']
        Y = data['1d-data'][self._misc[self.d1]['index']]
        return dict(LINE=[(X, Y)], title=title,
                    xlabel='r', xlim=[min(X), max(X)])


class Plot1DPsirFigInfo(FigInfo):
    '''Figures X -> psi, r of q, shear, gcurrent, pressure, tor flux ...'''
    __slots__ = ['d1']
    _misc = {
        'q': dict(title='q profile', index=19),
        'shear': dict(title='shear d(ln(q))/dpsi', index=20),
        'gcurrent': dict(title='gcurrent profile', index=21),
        'pressure': dict(title='pressure profile', index=22),
        'tor_flux': dict(title='toroidal flux', index=24),
        'rg': dict(title='radial grid', index=25),
    }
    figurenums = ['%s:psi-r' % d1 for d1 in _misc.keys()]
    numpattern = r'^(?P<d1>(?:%s)):psi-r$' % '|'.join(_misc.keys())

    def __init__(self, fignum, scope, groups):
        groupdict = self._pre_check_get(fignum, 'd1')
        self.d1 = groupdict['d1']
        super(Plot1DPsirFigInfo, self).__init__(
            fignum, scope, groups, ['nrad', '1d-data'], [],
            'template_z111p_axstructs')

    def calculate(self, data, **kwargs):
        lsp1 = data['nrad']
        X1 = data['1d-data'][0]
        X2 = data['1d-data'][23] / data['1d-data'][23][lsp1 - 1]
        title = self._misc[self.d1]['title']
        Y = data['1d-data'][self._misc[self.d1]['index']]
        ax1_calc = dict(LINE=[(X1, Y)], title='%s (psi)' % title,
                        xlabel='psi', xlim=[min(X1), max(X1)])
        ax2_calc = dict(LINE=[(X2, Y)], title='%s (r)' % title,
                        xlabel='r', xlim=[min(X2), max(X2)])
        self.calculation = {
            'zip_results': [('template_line_axstructs', 211, ax1_calc),
                            ('template_line_axstructs', 212, ax2_calc)],
        }


class Plot1DParticleFigInfo(FigInfo):
    '''Figures of ion, electron, fastion T, n'''
    __slots__ = ['particle']
    figurenums = ['%s' % p for p in ['ion', 'electron', 'fastion']]
    numpattern = '^(?P<particle>(?:ion|electron|fastion))$'

    def __init__(self, fignum, scope, groups):
        groupdict = self._pre_check_get(fignum, 'particle')
        self.particle = groupdict['particle']
        super(Plot1DParticleFigInfo, self).__init__(
            fignum, scope, groups, ['nrad', '1d-data'], [],
            'template_z111p_axstructs')

    def calculate(self, data, **kwargs):
        lsp1 = data['nrad']
        X1 = data['1d-data'][23] / data['1d-data'][23][lsp1 - 1]
        X2 = data['1d-data'][0]
        if self.particle == 'ion':
            s, l1, r1, l2, r2 = 'i', 9, 11, 8, 10
        elif self.particle == 'electron':
            s, l1, r1, l2, r2 = 'e', 5, 7, 4, 6
        elif self.particle == 'fastion':
            s, l1, r1, l2, r2 = 'f', 13, 15, 12, 14
        ax1_calc = dict(X=X1, ylabel_rotation=0, YINFO=[{
            'left': [(data['1d-data'][l1], r'-dln$T_%s$/dpsi' % s)],
            'right':[(data['1d-data'][r1], r'-dln$n_%s$/dpsi' % s)],
            'lylabel': r'$T_%s$' % s, 'rylabel': r'$n_%s$' % s,
        }])
        ax2_calc = dict(X=X2, ylabel_rotation=0, YINFO=[{
            'left': [(data['1d-data'][l2], r'$T_%s$(psi)' % s)],
            'right':[(data['1d-data'][r2], r'$n_%s$(psi)' % s)],
            'lylabel': r'$T_%s$' % s, 'rylabel': r'$n_%s$' % s,
        }])
        self.calculation = {
            'zip_results': [
                ('template_sharex_twinx_axstructs', 211, ax1_calc),
                ('template_sharex_twinx_axstructs', 212, ax2_calc)],
            'suptitle': self.particle,
        }


class Plot1DErroFigInfo(LineFigInfo):
    '''Figures X -> [0, pi/2], error of spline cos, sin'''
    __slots__ = ['d1']
    _misc = {'cos': dict(title='error of spline cos', index=28),
             'sin': dict(title='error of spline sin', index=29)}
    figurenums = ['error-%s' % d1 for d1 in _misc.keys()]
    numpattern = r'^error-(?P<d1>(?:%s))$' % '|'.join(_misc.keys())

    def _get_srckey_extrakey(self, fignum):
        groupdict = self._pre_check_get(fignum, 'd1')
        self.d1 = groupdict['d1']
        return ['nrad', '1d-data'], []

    def _get_data_LINE_title_etc(self, data):
        dx = numpy.pi / 2 / data['nrad']
        X = numpy.array(range(1, data['nrad'] + 1)) * dx
        title = self._misc[self.d1]['title']
        Y = data['1d-data'][self._misc[self.d1]['index']]
        return dict(LINE=[(X, Y)], title=title,
                    xlabel=r'$\theta$', xlim=[min(X), max(X)])


class Plot2DFigInfo(PcolorFigInfo):
    '''Figures of b-field, Jacobian, icurrent, zeta2phi, delb'''
    __slots__ = ['d2']
    _misc = ['b-field', 'Jacobian', 'icurrent', 'zeta2phi', 'delb']
    figurenums = [d2 for d2 in _misc]
    numpattern = r'^(?P<d2>(?:%s))$' % '|'.join(_misc)

    def _get_srckey_extrakey(self, fignum):
        groupdict = self._pre_check_get(fignum, 'd2')
        self.d2 = groupdict['d2']
        return ['mesh-points-on-X', 'mesh-points-on-Z', fignum], []

    def _get_data_X_Y_Z_title_etc(self, data):
        X, Y = data['mesh-points-on-X'], data['mesh-points-on-Z']
        Z = data[self.fignum]
        return dict(X=X, Y=Y, Z=Z, title=self.fignum,
                    xlabel='R', ylabel='Z')

    def _serve(self, plotter, AxStrus, add_style):
        '''patch mpl:: *AxStrus*'''
        if plotter.name.startswith('mpl::'):
            try:
                data = AxStrus[0]['data']
                data.append([len(data) + 1, 'set_aspect', ('equal',), dict()])
            except Exception:
                log.error("Failed to patch %s!" % self.fullnum, exc_info=1)
        return AxStrus, add_style


class Plot2DMeshFigInfo(LineFigInfo):
    '''Figure poloidal mesh'''
    __slots__ = []
    figurenums = ['poloidal_mesh']
    numpattern = r'.*'

    def _get_srckey_extrakey(self, fignum):
        groupdict = self._pre_check_get(fignum)
        return ['mpsi-over-mskip+1', 'lst',
                'mesh-points-on-X', 'mesh-points-on-Z'], []

    def _get_data_LINE_title_etc(self, data):
        X, Y = data['mesh-points-on-X'], data['mesh-points-on-Z']
        lsp, lst = data['mpsi-over-mskip+1'], data['lst']
        LINE = []
        for i in range(lsp):
            x, y = X[i], Y[i]
            x, y = numpy.append(x, x[0]), numpy.append(y, y[0])
            LINE.append((x, y))
        for i in range(lst):
            x, y = X[:, i], Y[:, i]
            LINE.append((x, y))
        return dict(LINE=LINE, title='poloidal mesh',
                    xlabel='R', ylabel='Z')

    def _serve(self, plotter, AxStrus, add_style):
        '''patch mpl:: *AxStrus*'''
        if plotter.name.startswith('mpl::'):
            try:
                data = AxStrus[0]['data']
                data.append([len(data) + 1, 'set_aspect', ('equal',), dict()])
            except Exception:
                log.error("Failed to patch %s!" % self.fullnum, exc_info=1)
        return AxStrus, add_style


class Plot2DThetaFigInfo(LineFigInfo):
    '''Figures X -> theta of b-field, Jacobian, icurrent at psi=isp'''
    __slots__ = ['d2', 'isp']
    _misc = ['b-field', 'Jacobian', 'icurrent', 'gq_plus_I/BB']
    figurenums = ['%s:theta' % d2 for d2 in _misc]
    numpattern = r'^(?P<d2>(?:%s)):theta$' % '|'.join(_misc)

    def _get_srckey_extrakey(self, fignum):
        self.d2 = self._pre_check_get(fignum, 'd2')['d2']
        if self.d2 == 'gq_plus_I/BB':
            skeys = ['1d-data', 'b-field', 'icurrent']
        else:
            skeys = [self.d2]
        return ['mpsi-over-mskip+1', 'lst'] + skeys, []

    def _get_data_LINE_title_etc(self, data):
        X = 2.0 * numpy.pi * numpy.array(range(data['lst'] + 1)) / data['lst']
        if self.d2 == 'gq_plus_I/BB':
            g = data['1d-data'][21][self.isp]
            q = data['1d-data'][19][self.isp]
            I, B = data['icurrent'][self.isp], data['b-field'][self.isp]
            Y = (g * q + I) / (B * B)
            title = '(gq+I)/B^2'
        else:
            Y = data[self.d2][self.isp]
            title = self.d2
        Y = numpy.append(Y, Y[0])
        title = r'%s ($\theta$) at psi=isp=%d' % (title, self.isp)
        return dict(LINE=[(X, Y, 'isp=%d' % self.isp)], title=title,
                    xlabel=r'$\theta$', xlim=[0, 2.0 * numpy.pi])

    def calculate(self, data, **kwargs):
        '''
        kwargs
        ------
        *isp*: int
            fix psi=isp, default 'mpsi-over-mskip+1' - 1
        *xlim*: (`left`, `right`)
            default [min(X), max(X)]
        *ylabel_rotation*: str or int
            default 'vertical'
        '''
        self.isp = data['mpsi-over-mskip+1'] - 1
        if 'isp' in kwargs:
            isp = kwargs.pop('isp')
            if isinstance(isp, int) and isp <= self.isp:
                self.isp = isp
        log.parm("fix: psi=isp=%d. Maximal isp=%d."
                 % (self.isp, data['mpsi-over-mskip+1'] - 1))
        super(Plot2DThetaFigInfo, self).calculate(data, **kwargs)
        self.layout['isp'] = dict(
            widget='IntSlider',
            rangee=(0, data['mpsi-over-mskip+1'] - 1, 1),
            value=self.isp,
            description='psi=isp:')


class EquilibriumLayCoreV110922(LayCore):
    '''
    Equilibrium Figures
    '''
    __slots__ = []
    itemspattern = ['^(?P<section>equilibrium)$']
    default_section = 'equilibrium'
    figinfoclasses = [Plot1DPsiFigInfo, Plot1DrFigInfo, Plot1DPsirFigInfo,
                      Plot1DParticleFigInfo, Plot1DErroFigInfo,
                      Plot2DFigInfo, Plot2DMeshFigInfo, Plot2DThetaFigInfo]
