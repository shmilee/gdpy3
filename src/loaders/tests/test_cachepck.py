# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

import unittest
import numpy

from . import DATA, DATA_C


class TestCachePckLoader(unittest.TestCase):
    '''
    Test class CachePckLoader
    '''

    def setUp(self):
        from ..cachepck import CachePckLoader
        self.CachePckLoader = CachePckLoader

    def test_cacheloader_init(self):
        loader = self.CachePckLoader(DATA_C)
        self.assertSetEqual(set(loader.datakeys), set(DATA.keys()))
        self.assertSetEqual(set(loader.datagroups), {'test', 'te/st'})
        self.assertMultiLineEqual(loader.description, 'test data')

    def test_cacheloader_get(self):
        loader = self.CachePckLoader(DATA_C)
        self.assertTrue(
            numpy.array_equal(loader.get('test/array'), DATA['test/array']))
        self.assertEqual(loader.get('test/float'), 3.1415)
        self.assertEqual(loader.get('te/st/int'), 1)
