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
from .block import Block, log

__all__ = ['EquilibriumBlockV110922']


class EquilibriumBlockV110922(Block):
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
        'nplot-1d', 'nrad', '1d-data',
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
            log.ddebug("Read file '%s'." % self.file)
            outdata = f.readlines()

        sd = self.data
        # 1. first part
        log.debug("Filling datakeys: %s ..." % str(self.datakeys[:3]))
        sd.update({'nplot-1d': int(outdata[0].strip()),
                   'nrad': int(outdata[1].strip())})
        size1 = (sd['nplot-1d'] + 1) * sd['nrad']
        shape1 = ((sd['nplot-1d'] + 1), sd['nrad'])
        data1 = numpy.array([float(n.strip()) for n in outdata[2:2 + size1]])
        data1 = data1.reshape(shape1, order='C')
        sd.update({'1d-data': data1})
        # 2. second part
        log.debug("Filling datakeys: %s ..." % str(self.datakeys[3:6]))
        index2 = 2 + size1
        sd.update({'nplot-2d': int(outdata[index2].strip()),
                   'mpsi-over-mskip+1': int(outdata[index2 + 1].strip()),
                   'lst': int(outdata[index2 + 2].strip())})
        log.debug("Filling datakeys: %s ..." % str(self.datakeys[6:]))
        size2 = (sd['nplot-2d'] + 2) * sd['mpsi-over-mskip+1'] * sd['lst']
        shape2 = ((sd['nplot-2d'] + 2), sd['mpsi-over-mskip+1'] * sd['lst'])
        data2 = numpy.array([float(n.strip())
                             for n in outdata[index2 + 3:index2 + 3 + size2]])
        data2 = data2.reshape(shape2, order='C')
        shape3 = (sd['mpsi-over-mskip+1'], sd['lst'])
        for i, key in enumerate(self.datakeys[6:]):
            sd.update({key: data2[i].reshape(shape3, order='F')})
