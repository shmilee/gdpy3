# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

import os
import unittest
import tempfile
import numpy
try:
    import h5py
    HAVE_H5PY = True
except ImportError:
    HAVE_H5PY = False

from . import DATA


@unittest.skipUnless(HAVE_H5PY, "requires h5py")
class TestHdf5PckLoader(unittest.TestCase):
    '''
    Test class Hdf5PckLoader
    '''

    def setUp(self):
        from ..hdf5pck import Hdf5PckLoader
        self.Hdf5PckLoader = Hdf5PckLoader
        self.tmpfile = tempfile.mktemp(suffix='-test.hdf5')
        with h5py.File(self.tmpfile, 'w-') as h5f:
            fgrp = h5f.create_group('test')
            sgrp = h5f.create_group('te/st')
            for key in DATA.keys():
                if key.startswith('test/'):
                    fgrp.create_dataset(key.replace('test/', ''),
                                        data=DATA[key])
                elif key.startswith('te/st/'):
                    sgrp.create_dataset(key.replace('te/st/', ''),
                                        data=DATA[key])
                else:
                    h5f.create_dataset(key, data=DATA[key])

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_hdf5loader_init(self):
        loader = self.Hdf5PckLoader(self.tmpfile)
        self.assertSetEqual(set(loader.datakeys), set(DATA.keys()))
        self.assertSetEqual(set(loader.datagroups), {'test', 'te/st'})
        self.assertMultiLineEqual(loader.description, 'test data')

    def test_hdf5loader_get(self):
        loader = self.Hdf5PckLoader(self.tmpfile)
        self.assertTrue(
            numpy.array_equal(loader.get('test/array'), DATA['test/array']))
        self.assertEqual(loader.get('test/float'), 3.1415)
        self.assertEqual(loader.get('te/st/int'), 1)
