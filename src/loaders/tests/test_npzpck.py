# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

import os
import unittest
import tempfile
import numpy

from . import DATA


class TestNpzPckLoader(unittest.TestCase):
    '''
    Test class NpzPckLoader
    '''

    def setUp(self):
        from ..npzpck import NpzPckLoader
        self.NpzPckLoader = NpzPckLoader
        self.tmpfile = tempfile.mktemp(suffix='-test.npz')
        numpy.savez_compressed(self.tmpfile, **DATA)

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_npzloader_init(self):
        loader = self.NpzPckLoader(self.tmpfile)
        self.assertSetEqual(set(loader.datakeys), set(DATA.keys()))
        self.assertSetEqual(set(loader.datagroups), {'test'})
        self.assertMultiLineEqual(loader.description, 'test data')

    def test_npzloader_get(self):
        loader = self.NpzPckLoader(self.tmpfile)
        self.assertTrue(
            numpy.array_equal(loader.get('test/array'), DATA['test/array']))
        self.assertEqual(loader.get('test/float'), 3.1415)
