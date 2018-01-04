# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import unittest
import tempfile
try:
    import h5py
    HAVE_H5PY = True
except ImportError:
    HAVE_H5PY = False


@unittest.skipUnless(HAVE_H5PY, "requires h5py")
class TestHdf5FileSaver(unittest.TestCase):
    '''
    Test class Hdf5FileSaver
    '''

    def setUp(self):
        from ..hdf5file import Hdf5FileSaver
        self.Hdf5FileSaver = Hdf5FileSaver
        self.tmp = tempfile.mktemp(suffix='-test')
        self.tmpfile = self.tmp + Hdf5FileSaver._extension

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_saver_iopen_close(self):
        saver = self.Hdf5FileSaver(self.tmpfile)
        self.assertFalse(saver.fobj)
        saver.iopen()
        self.assertTrue(saver.fobj)
        saver.close()
        self.assertFalse(saver.fobj)

    def test_saver_write(self):
        saver = self.Hdf5FileSaver(self.tmpfile)
        self.assertFalse(saver.write('', {'ver': '1'}))
        saver.iopen()
        self.assertFalse(saver.write('/', []))
        self.assertTrue(saver.write('', {'ver': '1'}))
        self.assertTrue(saver.write('/', {'num': 100, 'list': [1, 2, 3]}))
        self.assertTrue(saver.write('group', {'desc': 'desc'}))
        saver.close()
        hdf5 = h5py.File(saver.file, 'r')
        inkeys = {'ver', 'num', 'list', 'group/desc'}
        outkeys = set()
        hdf5.visititems(
            lambda name, obj: outkeys.add(name)
            if isinstance(obj, h5py.Dataset) else None)
        self.assertSetEqual(inkeys, outkeys)
