#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import logging
import gdpy3.read as gdr
from gdpy3.plot import data1d, history, trackparticle

log0 = logging.getLogger('test')
log1 = logging.getLogger('gdp')

#CasePath = '/home/IFTS_shmilee/201703XX-residual-ZF/n18-T'
#CasePath = '/home/IFTS_shmilee/201703XX-residual-ZF/obo-4T-50dots-0.4'
CasePath = '/home/IFTS_shmilee/20170527-ITG-nonlinear/n14-D/'

if __name__ == '__main__':
    log1.setLevel(10)
    dictobj = gdr.read(CasePath)
    # zf = data1d.Data1dFigureV110922(
    #    dictobj,
    #    'zonal_flow',
    #    #'residual_zonal_flow',
    #)
    # his = history.HistoryFigureV110922(
    #    dictobj,
    #    #'ion_density_entropy',
    #    #'ion_momentum',
    #    #'ion_energy',
    #    'ion_particle_momentum_flux',
    #    #'ion_energy_flux',
    #    #'field_phi',
    #    #'field_phi00',
    #    #'mode3_phi',
    #)
    track = trackparticle.TrackParticleFigureV110922(
        dictobj,
        'orbit_2d_ion',
        #'orbit_3d_ion',
        #'orbit_2d_electron',
    )
    for gf in [
            # zf,
            # his,
            track]:
        gf.calculate(
            # region_start=120, region_end=400,
            # region_start=20, region_end=120,
            # plot_method='plot_surface',
            # plot_method='pcolormesh',
            # key='random', index=range(5,14),
            key='in-', index=range(1, 10),
        )
        if 'orbit_2d' in gf.name:
            gf.figurestyle = ['gdpy3-notebook',
                              {'figure.figsize': (12.0, 12.0)}]
        log0.info('calculation: %s ' % gf.calculation)
        input('Enter to continue, show: ')
        gf.show()
        input('Enter to continue, close: ')
        gf.close()
