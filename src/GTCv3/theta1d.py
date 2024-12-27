#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2024 shmilee

'''
Source fortran code:

1. info:
    open(iotheta1d,file='theta1d.out',status='replace')
    write(iotheta1d,101) ndstep, the_nfield, the_niflux
    write(iotheta1d,101) the_fields
    write(iotheta1d,101) the_ifluxes
    do i=1,the_niflux
        write(iotheta1d,101) the_igrid1(i)-the_igrid0(i)+1
    end do

2. data:
    do nfidx=1,the_nfield
        nf=the_fields(nfidx)
        if (nf==1) then
            do i=1,the_niflux
                write(iotheta1d,101) phi(0,the_igrid0(i):the_igrid1(i))/(rho0*rho0)
            end do
        else if (nf==2) then
            do i=1,the_niflux
                write(iotheta1d,101) sapara(0,the_igrid0(i):the_igrid1(i))
            end do
        else if (nf==3) then
            do i=1,the_niflux
                write(iotheta1d,101) sfluidne(0,the_igrid0(i):the_igrid1(i))
            end do
        end if
    end do
'''


import numpy as np
from .. import tools
from ..cores.converter import Converter, clog
from ..cores.digger import Digger, dlog
from .gtc import Ndigits_tstep
from .snapshot import (
    field_tex_str,
    _snap_fieldtime_fft,
    _snap_fieldtime_fft__post_dig
)

_all_Converters = ['Theta1dConverter']
_all_Diggers = ['Theta1dDigger', 'Theta1dFFTDigger']
__all__ = _all_Converters + _all_Diggers


class Theta1dConverter(Converter):
    '''
    Theta Time Data

    1) Field diagnosis: phi, a_para, fluid_ne.
       The field 2d array is field[theta,time].
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = [r'^(?P<section>theta1d)\.out$',
                    r'.*/(?P<section>theta1d)\.out$']
    _datakeys = (
        # 1. info
        'ndstep', 'the_nfield', 'the_niflux',
        'the_fields', 'the_ifluxes', 'the_grids'
        # 2. data phi(theta,time)
        r'(?:phi|apara|fluidne)-ipsi\d+'
    )

    def _convert(self):
        '''Read 'theta1d.out'.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        # 1. parameters
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[:3]))
        for i, key in enumerate(self._datakeys[:3]):
            sd.update({key: int(outdata[i].strip())})
        nfield = sd['the_nfield']
        niflux = sd['the_niflux']
        clog.debug("Filling datakeys: %s ..." % str(self._datakeys[3:6]))
        idx = 3
        sd['the_fields'] = [int(i.strip()) for i in outdata[idx:idx+nfield]]
        idx = idx + nfield
        sd['the_ifluxes'] = [int(i.strip()) for i in outdata[idx:idx+niflux]]
        idx = idx + niflux
        sd['the_grids'] = [int(i.strip()) for i in outdata[idx:idx+niflux]]
        idx = idx + niflux
        # 2. data
        outdata = np.array([float(n.strip()) for n in outdata[idx:]])
        ngrid = sum(sd['the_grids'])
        ndata = nfield*ngrid
        if len(outdata) // ndata != sd['ndstep']:
            clog.debug("Filling datakeys: %s ..." % 'ndstep')
            sd.update({'ndstep': len(outdata) // ndata})
            outdata = outdata[:sd['ndstep'] * ndata]
        # reshape outdata
        outdata = outdata.reshape((ngrid, nfield, sd['ndstep']), order='F')
        for nfidx in range(nfield):
            if sd['the_fields'][nfidx] == 1:
                fk = 'phi'
            elif sd['the_fields'][nfidx] == 2:
                fk = 'apara'
            elif sd['the_fields'][nfidx] == 3:
                fk = 'fluidne'
            igrid0 = 0
            for i in range(niflux):
                key = '%s-ipsi%d' % (fk, sd['the_ifluxes'][i])
                igrid1 = igrid0 + sd['the_grids'][i]
                sd[key] = outdata[igrid0:igrid1, nfidx, :]
                igrid0 = igrid1
        return sd


class Theta1dDigger(Digger):
    ''' field(theta,t) of phi, a_para, fluidne at zeta=0. '''
    __slots__ = ['ipsi']
    itemspattern = [r'^(?P<s>theta1d)'
                    + r'/(?P<field>(?:phi|apara|fluidne))-ipsi(?P<ipsi>\d+)']
    commonpattern = ['gtc/tstep', 'gtc/ndiag']
    post_template = 'tmpl_contourf'

    def _set_fignum(self, numseed=None):
        self.ipsi = int(self.section[-1])
        self._fignum = '%s_%03d' % (self.section[1], self.ipsi)
        self.kwoptions = None

    def _dig(self, kwargs):
        '''
        kwargs
        ------
        *tcutoff*: [t0,t1], t0 t1 float
            t0<=time[x0:x1]<=t1
        '''
        data, tstep, ndiag = self.pckloader.get_many(
            self.srckeys[0], *self.extrakeys[:2])
        tstep = round(tstep, Ndigits_tstep)
        dt = tstep * ndiag
        y, x = data.shape
        time = np.around(np.arange(1, x + 1) * dt, 8)
        Y = np.arange(0, y) / (y-1) * 2 * np.pi
        if self.kwoptions is None:
            self.kwoptions = dict(tcutoff=dict(
                widget='FloatRangeSlider',
                rangee=[time[0], time[-1], dt],
                value=[time[0], time[-1]],
                description='time cutoff:'),
            )
        acckwargs = dict(tcutoff=[time[0], time[-1]])
        if 'tcutoff' in kwargs:
            try:
                t0, t1 = kwargs['tcutoff']
                index = np.where((time >= t0) & (time < t1 + dt))[0]
                assert index.size > 0
                x0, x1 = index[0], index[-1]+1
            except Exception:
                dlog.warning('Cannot cutoff: %s <= time <= %s!'
                             % (t0, t1), exc_info=1)
            else:
                acckwargs['tcutoff'] = [time[x0], time[x1-1]]
                time = time[x0:x1]
                data = data[:, x0:x1]
        try:
            rpsi, a = self.pckloader.get_many('gtc/sprpsi', 'gtc/a_minor')
            ra = np.round(rpsi[self.ipsi]/a, decimals=3)
        except Exception:
            pos = r'ipsi=%d, $\zeta=0$' % self.ipsi
        else:
            pos = r'r=%ga, $\zeta=0$' % ra
        fstr = field_tex_str[self.section[1]]
        title = r'$%s(\theta, t)$ at %s' % (fstr, pos)
        return dict(X=time, Y=Y, Z=data, title=title, fstr=fstr,
                    ylabel=r'$\theta$', xlabel=r'time($R_0/c_s$)'), acckwargs

    def _post_dig(self, results):
        return results


class Theta1dFFTDigger(Theta1dDigger):
    ''' FFT field(theta,t) for phi, a_para, fluidne at zeta=0. '''
    __slots__ = []
    post_template = ('tmpl_z111p', 'tmpl_contourf', 'tmpl_line')

    def _set_fignum(self, numseed=None):
        super()._set_fignum(numseed=numseed)
        self._fignum = '%s_fft_%03d' % (self.section[1], self.ipsi)

    def _dig(self, kwargs):
        results, acckwargs = super()._dig(kwargs)
        time, theta, data = results['X'], results['Y'], results['Z']
        res = _snap_fieldtime_fft(
            data, None, theta, time, self.ipsi, self.pckloader,
            self.kwoptions, kwargs, acckwargs)
        results.update(res)
        return results, acckwargs

    _dig.__doc__ = _snap_fieldtime_fft.__doc__

    def _post_dig(self, results):
        return _snap_fieldtime_fft__post_dig(results)
