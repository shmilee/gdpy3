# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

import os
import unittest
import tempfile
import shutil

from .. import get_processor
from ..lib import *

register_Processor('TDP', '.tests', 'T')


class TestSerialProcessor(unittest.TestCase):
    '''
    Test Serial Processor class.
    '''

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix='-test')
        os.mkdir(self.tmp)
        with open(os.path.join(self.tmp, 'test.out'), mode='w') as f:
            f.write('10\n20\n30\n40')
        self.figlabel = 'test/mnpq'

    def tearDown(self):
        if os.path.isdir(self.tmp):
            shutil.rmtree(self.tmp)

    def test_processor_register(self):
        self.assertTrue('TDP' in Processor_Lib)
        self.assertTrue('TDP' in Processor_Names)
        self.assertTrue('T' in Processor_Alias)
        with self.assertRaises(ValueError):
            find_Processor('TDP', 'nopara')
        gdpcls = find_Processor('TDP', 'off')
        self.assertTrue(isinstance(gdpcls, type))

    def test_processor_init(self):
        gdp = get_processor(self.tmp, name='TDP', parallel='off')
        self.assertTrue(gdp.rawloader is not None)
        self.assertTrue(gdp.pcksaver is not None)
        self.assertTrue(gdp.pckloader is not None)
        self.assertTrue(gdp.ressaver is not None)
        self.assertTrue(gdp.resfilesaver is not None)
        self.assertTrue(gdp.resloader is not None)
        self.assertTrue(gdp.resfileloader is not None)
        self.assertTrue(self.figlabel in gdp.availablelabels)

    def test_processor_dig(self):
        gdp = get_processor(self.tmp, name='TDP', parallel='off')
        accfiglabel, results, template = gdp.dig(self.figlabel)
        self.assertTrue(accfiglabel in gdp.diggedlabels)
        self.assertTrue(isinstance(results, dict))
        self.assertEqual(template, 'tmpl_line')

    def test_processor_dig_save2file(self):
        gdpcls = get_processor(name='TDP', parallel='off')
        gdpcls.dig_acceptable_time = 0
        gdp = gdpcls(self.tmp)
        accfiglabel, results, template = gdp.dig(self.figlabel)
        self.assertTrue(accfiglabel in gdp.resfileloader.datagroups)

    def test_processor_export(self):
        gdp = get_processor(self.tmp, name='TDP', parallel='off')
        results = gdp.export(self.figlabel)
        self.assertEqual(results['status'], 200)
        options = gdp.export(self.figlabel, what='options')
        self.assertEqual(options['digoptions'], {})

    def test_processor_visplt(self):
        gdp = get_processor(self.tmp, name='TDP', parallel='off')
        accfiglabel = gdp.visplt(self.figlabel, show=False)
        self.assertTrue(accfiglabel in gdp.visplter.figures)

    def test_processor_dig_visplt_callback(self):
        gdp = get_processor(self.tmp, name='TDP', parallel='off')
        a, results, t = gdp.dig(self.figlabel, post=False)
        X1 = [results['x']]
        X2 = []

        def get_X(res):
            X2.append(res['x'])

        accfiglabel = gdp.visplt(self.figlabel, show=False, callback=get_X)
        self.assertListEqual(X1[0], X2[0])
