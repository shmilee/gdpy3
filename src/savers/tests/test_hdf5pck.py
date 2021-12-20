# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import os
import unittest
import tempfile
import numpy

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
        self.assertTrue(saver.write('grp/sub', {'n': 1}))
        saver.close()
        hdf5 = h5py.File(saver.get_store(), 'r')
        inkeys = {'ver', 'num', 'list', 'group/desc', 'grp/sub/n'}
        outkeys = set()
        hdf5.visititems(
            lambda name, obj: outkeys.add(name)
            if isinstance(obj, h5py.Dataset) else None)
        self.assertSetEqual(inkeys, outkeys)

    def test_hdf5saver_write_str_byte(self):
        with self.PckSaver(self.tmpfile) as saver:
            self.assertTrue(saver.write('', {'sver': r'v1', 'bver': b'v1'}))
        hdf5 = h5py.File(saver.get_store(), 'r')
        self.assertEqual(hdf5['sver'][()].decode(encoding='utf-8'), r'v1')
        self.assertEqual(hdf5['bver'][()].tobytes(), b'v1')

    def test_hdf5saver_write_num_arr(self):
        with self.PckSaver(self.tmpfile) as saver:
            self.assertTrue(saver.write('', {'n': 1, 'f': 1.1, 'a': [1, 2]}))
        hdf5 = h5py.File(saver.get_store(), 'r')
        self.assertEqual(hdf5['n'][()], 1)
        self.assertEqual(hdf5['f'][()], 1.1)
        self.assertTrue(numpy.array_equal(hdf5['a'][()], numpy.array([1, 2])))

    def test_hdf5saver_with(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.status)
        with saver:
            self.assertIsNotNone(saver._storeobj)
            self.assertTrue(saver.status)
        self.assertIsNone(saver._storeobj)
        self.assertFalse(saver.status)
