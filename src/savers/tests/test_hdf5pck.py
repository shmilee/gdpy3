# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import numpy
import unittest
try:
    import h5py
    HAVE_H5PY = True
except ImportError:
    HAVE_H5PY = False
from . import PckSaverTest
from ..hdf5pck import Hdf5PckSaver


@unittest.skipUnless(HAVE_H5PY, "requires h5py")
class TestHdf5PckSaver(PckSaverTest, unittest.TestCase):
    ''' Test class Hdf5PckSaver '''
    PckSaver = Hdf5PckSaver

    def test_hdf5saver_iopen_close(self):
        self.saver_iopen_close()

    def test_hdf5saver_write(self):
        self.saver_write()

    def saver_get_keys(self, store):
        hdf5 = h5py.File(store, 'r')
        outkeys = set()
        hdf5.visititems(
            lambda name, obj: outkeys.add(name)
            if isinstance(obj, h5py.Dataset) else None)
        return outkeys

    def saver_get(self, store, *keys):
        hdf5 = h5py.File(store, 'r')
        res = []
        for k in keys:
            val = hdf5[k][()]
            # str <- bytes; bytes <- void
            if isinstance(val, bytes):
                val = val.decode(encoding='utf-8')
            elif isinstance(val, numpy.void):
                val = val.tobytes()
            res.append(val)
        return res

    def test_hdf5saver_write_str_byte(self):
        self.saver_write_str_byte()

    def test_hdf5saver_write_num_arr(self):
        self.saver_write_num_arr()

    def test_hdf5saver_with(self):
        self.saver_with()
