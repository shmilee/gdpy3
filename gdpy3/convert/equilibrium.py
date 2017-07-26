# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

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

import os
import numpy
from .datablock import DataBlock

__all__ = ['EquilibriumBlockV110922']


class EquilibriumBlockV110922(DataBlock):
    '''
    Equilibrium data

    1) first part, 1D radial plots. Shape of 1D data is (nrad,).
        'nplot-1d', 'nrad',
        'radial-axis-using-poloidal-flux-function',
        'sqaure-root-of-normalized-toroidal-flux-function-is0',
        'minor-radius-is0', 'major-radius-is0',
        'Te', '-d(ln(Te))-over-dr', 'ne', '-d(ln(ne))-over-dr',
        'Ti', '-d(ln(Ti))-over-dr', 'ni', '-d(ln(ni))-over-dr',
        'Tf', '-d(ln(Tf))-over-dr', 'nf', '-d(ln(nf))-over-dr',
        'zeff', 'toroidal-rotation', 'radial-electric-field', 'q-profile',
        'd(ln(q))-over-dpsi', 'gcurrent-profile', 'pressure-profile',
        'minor-radius', 'toroidal-flux', 'rgpsi', 'psitor', 'psirg',
        'error-of-spline-cos', 'error-of-spline-sin',
    2) second part, 2D contour plots on poloidal plane.
       Shape of 2D data is (mpsi-over-mskip+1, lst).
        'nplot-2d', 'mpsi-over-mskip+1', 'lst',
        'mesh-points-on-X', 'mesh-points-on-Z', 'b-field',
        'Jacobian', 'icurrent', 'zeta2phi', 'delb'

    Attributes
    ----------
    file: str
        File path of GTC ``equilibrium.out`` to convert
    group: str of data group
    datakeys: tuple
        data keys of physical quantities in ``equilibrium.out``
    data: dict of converted data
    '''
    __slots__ = []
    _Datakeys = (
        # 1. first part, 1D
        'nplot-1d', 'nrad',
        # 0) datap # TODO single
        'radial-axis-using-poloidal-flux-function',
        # 1) data1d #TODO group 1-29
        'sqaure-root-of-normalized-toroidal-flux-function-is0',
        # 2-3) data1d
        'minor-radius-is0', 'major-radius-is0',
        # 4-7) data1d
        'Te', '-d(ln(Te))-over-dr', 'ne', '-d(ln(ne))-over-dr',
        # 8-11) data1d
        'Ti', '-d(ln(Ti))-over-dr', 'ni', '-d(ln(ni))-over-dr',
        # 12-15) data1d
        'Tf', '-d(ln(Tf))-over-dr', 'nf', '-d(ln(nf))-over-dr',
        # 16-19) data1d
        'zeff', 'toroidal-rotation', 'radial-electric-field', 'q-profile',
        # 20-22) data1d
        'd(ln(q))-over-dpsi', 'gcurrent-profile', 'pressure-profile',
        # 23-27) data1d
        'minor-radius', 'toroidal-flux', 'rgpsi', 'psitor', 'psirg',
        # 28-29) data1d
        'error-of-spline-cos', 'error-of-spline-sin',
        # 2. second part, 2D
        'nplot-2d', 'mpsi-over-mskip+1', 'lst',
        'mesh-points-on-X', 'mesh-points-on-Z',
        'b-field', 'Jacobian', 'icurrent', 'zeta2phi', 'delb')

    def convert(self):
        '''Read equilibrium.out

        convert the .out data to self.data as a dict,
        save list in data dict as numpy.array.
        '''
        with open(self.file, 'r') as f:
            outdata = f.readlines()

        sd = self.data
        # 1. first part # TODO
        sd.update({'nplot-1d': int(outdata[0].strip()),
                   'nrad': int(outdata[1].strip())})
        size1 = (sd['nplot-1d'] + 1) * sd['nrad']
        shape1 = ((sd['nplot-1d'] + 1), sd['nrad'])
        data1 = numpy.array([float(n.strip()) for n in outdata[2:2 + size1]])
        data1 = data1.reshape(shape1, order='C')
        for i, key in enumerate(self.datakeys[2:32]):
            sd.update({key: data1[i]})
        # 2. second part
        index2 = 2 + size1
        sd.update({'nplot-2d': int(outdata[index2].strip()),
                   'mpsi-over-mskip+1': int(outdata[index2 + 1].strip()),
                   'lst': int(outdata[index2 + 2].strip())})
        size2 = (sd['nplot-2d'] + 2) * sd['mpsi-over-mskip+1'] * sd['lst']
        shape2 = ((sd['nplot-2d'] + 2), sd['mpsi-over-mskip+1'] * sd['lst'])
        data2 = numpy.array([float(n.strip())
                             for n in outdata[index2 + 3:index2 + 3 + size2]])
        data2 = data2.reshape(shape2, order='C')
        shape3 = (sd['mpsi-over-mskip+1'], sd['lst'])
        for i, key in enumerate(self.datakeys[35:]):
            sd.update({key: data2[i].reshape(shape3, order='F')})
