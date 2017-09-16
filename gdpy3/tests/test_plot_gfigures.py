# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import unittest
import tempfile

from .. import glogger
from .. import convert as gdc
from ..plot import (
    gfigure,
    data1d, history, snapshot, trackparticle,
)
from . import casedir

glogger.getGLogger('P').handlers[0].setLevel(60)


@unittest.skipUnless(os.path.isfile(os.path.join(casedir, 'gtc.out')),
                     "Can't find 'gtc.out' in '%s'!" % casedir)
class TestGFigures(unittest.TestCase):
    '''
    Test GFigure class, and
    Data1dFigure, HistoryFigure, SnapshotFigure, TrackParticleFigure
    '''

    def setUp(self):
        self.dataobj = gdc.load(casedir)
        self.tmpfile = tempfile.mktemp(suffix='-gfigure-')

    def tearDown(self):
        for fig in ['data1d', 'history', 'snapshot', 'trackparticle']:
            tmpfile = self.tmpfile + fig + '.jpg'
            if os.path.isfile(tmpfile):
                os.remove(tmpfile)

    def test_gfigure_init(self):
        with self.assertRaises(ValueError):
            gf = gfigure.GFigure({}, 'name', 'group',
                                 {'key': ['gtc/r0']},
                                 figurestyle=[])
        with self.assertRaises(ValueError):
            gf = gfigure.GFigure(self.dataobj, 'name', 'group',
                                 {'key': ['get/r0']},
                                 figurestyle=[])

        gf = gfigure.GFigure(self.dataobj, 'name', 'group',
                             {'key': ['gtc/r0']},
                             figurestyle=['gdpy3-notebook'])
        self.assertEqual(gf.Name, 'group/name')
        self.assertListEqual(gf.figurestructure['Style'], ['gdpy3-notebook'])

    @unittest.skipUnless(os.path.isfile(os.path.join(casedir, 'data1d.out')),
                         "Can't find 'data1d.out' in '%s'!" % casedir)
    def test_gfigure_data1d(self):
        gf = data1d.Data1dFigureV110922(
            self.dataobj,
            'ion_flux',
            #'ion_energy_flux',
            #'electron_flux',
            #'zonal_flow',
            #'residual_zonal_flow',
            #'phi_rms',
            # figurestyle=['ggplot'],
        )
        gf.calculate(
            # region_start=120, region_end=400,
            # plot_method='plot_surface',
            # plot_method='pcolormesh',
            # plot_method='contourf',
            # plot_args=[10],
            #plot_kwargs=dict(rstride=10, cstride=10),
            # colorbar=False,
            grid_alpha=0.3,
            #surface_contourf=['x', 'y', 'z'],
        )
        print('data1d calculation: %s ' % gf.calculation)
        gf.draw()
        tmpfile = self.tmpfile + 'data1d.jpg'
        gf.figure.savefig(tmpfile)
        # fig.show()
        input("[I]nterrupt, to see figure in %s." % tmpfile)
        gf.close()

    @unittest.skipUnless(os.path.isfile(os.path.join(casedir, 'history.out')),
                         "Can't find 'history.out' in '%s'!" % casedir)
    def test_gfigure_history(self):
        gf = history.HistoryFigureV110922(
            self.dataobj,
            #'ion',
            #'ion_flux',
            #'field_phi',
            #'field_apara',
            'mode3_phi',
            #'mode3_apara',
        )
        gf.calculate(
            # region_start=120, region_end=400,
            # hspace=0.02,
            # xlim=[20,80],
            # ylabel_rotation=45,
        )
        print('history calculation: %s ' % gf.calculation)
        gf.draw()
        tmpfile = self.tmpfile + 'history.jpg'
        gf.figure.savefig(tmpfile)
        # fig.show()
        input("[I]nterrupt, to see figure in %s." % tmpfile)
        gf.close()

    @unittest.skipUnless(os.path.isfile(os.path.join(casedir, 'snap00400.out')),
                         "Can't find 'snap00400.out' in '%s'!" % casedir)
    def test_gfigure_snapshot(self):
        gf = snapshot.SnapshotFigureV110922(
            self.dataobj,
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
        )
        gf.calculate(
            # hspace=0.02,
            # xlim=[20,80],
            # ylabel_rotation=45,
            # plot_method='plot_surface',
            # plot_method='pcolormesh',
            # plot_method='contourf',
            # plot_args=[10],
            #plot_kwargs=dict(rstride=10, cstride=10),
            # colorbar=False,
            grid_alpha=0.3,
            #surface_contourf=['x', 'y', 'z'],
            # mmode=194,
            # pmode=12,
            # itgrid=80, ipsi=10,
        )
        print('snapshot calculation: %s ' % gf.calculation)
        gf.draw()
        tmpfile = self.tmpfile + 'snapshot.jpg'
        gf.figure.savefig(tmpfile)
        # fig.show()
        input("[I]nterrupt, to see figure in %s." % tmpfile)
        gf.close()

    @unittest.skipUnless(os.path.isdir(os.path.join(casedir, 'trackp_dir')),
                         "Can't find 'trackp_dir' in '%s'!" % casedir)
    def test_gfigure_trackparticle(self):
        gf = trackparticle.TrackParticleFigureV110922(
            self.dataobj,
            'orbit_2d_ion',
            #'orbit_3d_ion',
            #'orbit_2d_electron',
        )
        gf.calculate(
            key='in-',
            index=range(1, 10),
        )
        if 'orbit_2d' in gf.name:
            gf.figurestyle = ['gdpy3-notebook',
                              {'figure.figsize': (12.0, 12.0)}]
        print('trackparticle calculation: %s ' % gf.calculation)
        gf.draw()
        tmpfile = self.tmpfile + 'trackparticle.jpg'
        gf.figure.savefig(tmpfile)
        # fig.show()
        input("[I]nterrupt, to see figure in %s." % tmpfile)
        gf.close()
