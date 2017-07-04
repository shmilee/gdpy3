#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import logging
import gdpy3.read as gdr
from gdpy3.plot import data1d, history, snapshot, trackparticle

log0 = logging.getLogger('test')
log1 = logging.getLogger('gdp')

#CasePath = '/home/IFTS_shmilee/201703XX-residual-ZF/n18-T'
#CasePath = '/home/IFTS_shmilee/201703XX-residual-ZF/obo-4T-50dots-0.4'
CasePath = '/home/IFTS_shmilee/20170527-ITG-nonlinear/n14-D/'
#CasePath = '/home/IFTS_shmilee/n18-T/tstep'


if __name__ == '__main__':
    log1.setLevel(10)
    dictobj = gdr.read(CasePath)
    d1 = data1d.Data1dFigureV110922(
        dictobj,
        'ion_flux',
        #'ion_energy_flux',
        #'electron_flux',
        #'zonal_flow',
        #'residual_zonal_flow',
        #'phi_rms',
        #figurestyle=['ggplot'],
    )
    his = history.HistoryFigureV110922(
        dictobj,
        #'ion',
        'ion_flux',
        #'field_phi',
        #'field_apara',
        #'mode3_phi',
        #'mode3_apara',
    )
    track = trackparticle.TrackParticleFigureV110922(
        dictobj,
        'orbit_2d_ion',
        #'orbit_3d_ion',
        #'orbit_2d_electron',
    )
    snap = snapshot.SnapshotFigureV110922(
        dictobj,
        #'ion_profile',
        #'ion_pdf',
        #'electron_profile',
        #'electron_pdf',
        #'fastion_pdf',
        #'phi_flux',
        #'apara_flux',
        #'fluidne_flux',
        #'phi_spectrum',
        #'apara_spectrum',
        #'phi_ploidal',
        #'apara_ploidal',
        #'fluidne_ploidal',
        'phi_profile',
        #'apara_profile',
        #'fluidne_profile',
        group='snap00400',
        #figurestyle=['ggplot'],
    )
    for gf in [
            #d1,
            #his,
            #track,
            snap,
            ]:
        gf.calculate(
            # region_start=120, region_end=400,
            #plot_method='plot_surface',
            #plot_method='pcolormesh',
            #plot_method='contourf',
            #plot_args=[10],
            #plot_kwargs=dict(rstride=10, cstride=10),
            #colorbar=False,
            grid_alpha=0.3,
            #surface_contourf=['x', 'y', 'z'],
            #key='random', index=range(5,14),
            key='in-', index=range(1, 10),
            #xlim=[20,80],
            #ylabel_rotation=45,
            #mmode=194,
            #pmode=12,
            #itgrid=80, ipsi=10,
        )
        if 'orbit_2d' in gf.name:
            gf.figurestyle = ['gdpy3-notebook',
                              {'figure.figsize': (12.0, 12.0)}]
        log0.info('calculation: %s ' % gf.calculation)
        input('Enter to continue, show: ')
        gf.draw()
        #gf.figure.savefig('test.png')
        gf.show()
        input('Enter to continue, close: ')
        gf.close()
