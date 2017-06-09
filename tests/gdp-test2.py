#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import logging
import gdpy3.read as gdr
from gdpy3.plot import data1d, history

log0 = logging.getLogger('test')
log1 = logging.getLogger('gdp')

CasePath = '/home/IFTS_shmilee/201703XX-residual-ZF/n18-T'
#CasePath = '/home/IFTS_shmilee/201703XX-residual-ZF/obo-4T-50dots-0.4'

if __name__ == '__main__':
    log1.setLevel(10)
    dictobj = gdr.read(CasePath)
    zf = data1d.Data1dFigureV110922(dictobj, 'zonal_flow')
    rzf = data1d.Data1dFigureV110922(dictobj, 'residual_zonal_flow')
    f3phi = history.HistoryFigureV110922(dictobj, 'fieldmode3_phi')
    for gf in [zf, rzf, f3phi]:
        gf.calculate(
            #region_start=120, region_end=400,
            #region_start=20, region_end=120,
            #plot_method='plot_surface',
            plot_method='pcolormesh',
        )
        log0.info('calculation: %s ' % gf.calculation)
        input('Enter to continue, show: ')
        gf.show()
        input('Enter to continue, close: ')
        gf.close()
    input('Enter to exit. ')
