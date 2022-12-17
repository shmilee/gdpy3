# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import unittest
import numpy
try:
    import h5py
    HAVE_H5PY = True
except ImportError:
    HAVE_H5PY = False

from . import DATA, PckLoaderTest
from ..hdf5pck import Hdf5PckLoader


@unittest.skipUnless(HAVE_H5PY, "requires h5py")
class TestHdf5PckLoader(PckLoaderTest, unittest.TestCase):
    ''' Test class Hdf5PckLoader '''
    PckLoader = Hdf5PckLoader

    def setUp(self):
        super(TestHdf5PckLoader, self).setUp()
        with h5py.File(self.tmpfile, 'w-') as h5f:
            fgrp = h5f.create_group('test')
            sgrp = h5f.create_group('te/st')
            for key in DATA.keys():
                val = DATA[key]
                if key.startswith('test/'):
                    fgrp.create_dataset(key.replace('test/', ''), data=val)
                elif key.startswith('te/st/'):
                    sgrp.create_dataset(key.replace('te/st/', ''), data=val)
                else:
                    if isinstance(val, str):
                        val = val.encode(encoding='utf-8')
                    elif isinstance(val, bytes):
                        val = numpy.void(val)
                    h5f.create_dataset(key, data=val)

    def test_hdf5loader_init(self):
        self.loader_init()

    def test_hdf5loader_get(self):
        self.loader_get()
