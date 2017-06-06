#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import logging
import gdpy3.read as gdr
import gdpy3.plot.data1d as data1d

log = logging.getLogger('gdpy3')
log0 = logging.getLogger('gdc')
log1 = logging.getLogger('gdr')
log2 = logging.getLogger('gdp')

if __name__ == '__main__':
    log2.setLevel(10)
    dictobj = gdr.read('/home/IFTS_shmilee/2017-D/obo-4T-50dots-0.2',
                       extension='hdf5')
    #zf = data1d.Data1dFigureV110922('residual_zonal_flow', dictobj)
    zf = data1d.Data1dFigureV110922('zonal_flow', dictobj)
    # zf.calculate(plot_method='plot_surface')
    zf.plot(plot_method='pcolormesh')
    zf.show()
    zf.figure.savefig(zf.Name + '.png')
    input()
