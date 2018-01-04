# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

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
class TestHdf5FileLoader(unittest.TestCase):
    '''
    Test class Hdf5FileLoader
    '''

    def setUp(self):
        from ..hdf5file import Hdf5FileLoader
        self.Hdf5FileLoader = Hdf5FileLoader
        self.tmpfile = tempfile.mktemp(suffix='-test.hdf5')
        with h5py.File(self.tmpfile, 'w-') as h5f:
            fgrp = h5f.create_group('test')
            for key in DATA.keys():
                if key.startswith('test/'):
                    fgrp.create_dataset(key.replace('test/', ''),
                            data=DATA[key])
                else:
                    h5f.create_dataset(key, data=DATA[key])

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_loader_init(self):
        loader = self.Hdf5FileLoader(self.tmpfile)
        self.assertSetEqual(set(loader.datakeys), set(DATA.keys()))
        self.assertSetEqual(set(loader.datagroups), {'test'})
        self.assertMultiLineEqual(loader.description, 'test data')

    def test_loader_get(self):
        loader = self.Hdf5FileLoader(self.tmpfile)
        self.assertTrue(
                numpy.array_equal(loader.get('test/array'), DATA['test/array']))
        self.assertEqual(loader.get('test/float'), 3.1415)
