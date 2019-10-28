# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

import os
import unittest
import tempfile
try:
    import h5py
    HAVE_H5PY = True
except ImportError:
    HAVE_H5PY = False


@unittest.skipUnless(HAVE_H5PY, "requires h5py")
class TestHdf5PckSaver(unittest.TestCase):
    '''
    Test class Hdf5PckSaver
    '''

    def setUp(self):
        from ..hdf5pck import Hdf5PckSaver
        self.PckSaver = Hdf5PckSaver
        self.tmp = tempfile.mktemp(suffix='-test')
        self.tmpfile = self.tmp + Hdf5PckSaver._extension

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_hdf5saver_iopen_close(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.status)
        saver.iopen()
        self.assertTrue(saver.status)
        saver.close()
        self.assertFalse(saver.status)

    def test_hdf5saver_write(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.write('', {'ver': '1'}))
        saver.iopen()
        self.assertFalse(saver.write('/', []))
        self.assertTrue(saver.write('', {'ver': '1'}))
        self.assertTrue(saver.write('/', {'num': 100, 'list': [1, 2, 3]}))
        self.assertTrue(saver.write('group', {'desc': 'desc'}))
        saver.close()
        hdf5 = h5py.File(saver.get_store(), 'r')
        inkeys = {'ver', 'num', 'list', 'group/desc'}
        outkeys = set()
        hdf5.visititems(
            lambda name, obj: outkeys.add(name)
            if isinstance(obj, h5py.Dataset) else None)
        self.assertSetEqual(inkeys, outkeys)

    def test_hdf5saver_with(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.status)
        with saver:
            self.assertIsNotNone(saver._storeobj)
            self.assertTrue(saver.status)
        self.assertIsNone(saver._storeobj)
        self.assertFalse(saver.status)
