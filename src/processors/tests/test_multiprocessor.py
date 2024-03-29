# -*- coding: utf-8 -*-

# Copyright (c) 2020-2021 shmilee

import os
import unittest
import tempfile
import shutil
import multiprocessing

from .. import get_processor
from ..lib import *

register_Processor('TDP', '.tests', 'T')


class TestMultiprocessProcessor(unittest.TestCase):
    '''
    Test Multiprocess Processor class.
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

    def test_processor_multi_dig(self):
        gdp = get_processor(self.tmp, name='TDP', parallel='multiprocess')
        out = gdp.multi_dig(self.figlabel)
        accfiglabel, results, template = out[0]
        self.assertTrue(accfiglabel in gdp.diggedlabels)

    def test_processor_multi_dig_save2file(self):
        gdpcls = get_processor(name='TDP', parallel='multiprocess')
        gdpcls.dig_acceptable_time = 0
        gdp = gdpcls(self.tmp)
        out = gdp.multi_dig(self.figlabel)
        accfiglabel, results, template = out[0]
        self.assertTrue(accfiglabel in gdp.resfileloader.datagroups)

    def test_processor_multi_visplt(self):
        gdp = get_processor(self.tmp, name='TDP', parallel='multiprocess')
        accfiglabels = gdp.multi_visplt(self.figlabel, savepath=self.tmp)
        # not in main process, but in worker process
        self.assertTrue(accfiglabels[0][0][0] not in gdp.visplter.figures)

    def test_processor_multi_dig_visplt_callback(self):
        gdp = get_processor(self.tmp, name='TDP', parallel='multiprocess')
        global X2, get_X  # fix: Can't pickle local object
        manager = multiprocessing.Manager()
        X2 = manager.list()

        def get_X(accfiglabel, res):
            X2.append((accfiglabel, res['x'], os.getpid()))

        accfiglabels = gdp.multi_visplt(
            *([self.figlabel]*2), savepath=self.tmp, callback=get_X)
        out = gdp.multi_dig(self.figlabel, post=False)
        a, results, t = out[0]
        self.assertEqual(a, X2[0][0])  # same accfiglabel
        self.assertEqual(a, X2[1][0])  # same accfiglabel
        self.assertListEqual(results['x'], X2[0][1])  # same result
        self.assertListEqual(results['x'], X2[1][1])  # same result
        self.assertNotEqual(X2[0][2], X2[1][2])  # different pid
