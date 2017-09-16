# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import numpy
import unittest
import tempfile

from .. import glogger
from ..convert import utils

glogger.getGLogger('C').handlers[0].setLevel(60)


class TestSaver(unittest.TestCase):
    '''
    Test class NpzSaver, Hdf5Saver
    '''

    def setUp(self):
        tmpfile = tempfile.mktemp(suffix='-test')
        self.npzfile = tmpfile + '.npz'
        self.hd5file = tmpfile + '.hdf5'

    def tearDown(self):
        if os.path.isfile(self.npzfile):
            os.remove(self.npzfile)
        if os.path.isfile(self.hd5file):
            os.remove(self.hd5file)

    def test_saver_init(self):
        saver = utils.NpzSaver(self.npzfile)
        saver2 = utils.Hdf5Saver(self.hd5file)
        with self.assertRaises(IOError):
            utils.NpzSaver(os.path.join(self.npzfile, 'BreakSuffix'))
        with self.assertRaises(IOError):
            utils.Hdf5Saver(os.path.join(self.hd5file, 'BreakSuffix'))

    def test_saver_iopen_close(self):
        for saver in [utils.NpzSaver(self.npzfile),
                      utils.Hdf5Saver(self.hd5file)]:
            self.assertTrue(saver.iopen())
            self.assertTrue(saver.fobj)
            self.assertTrue(saver.fobj_on)
            saver.close()
            self.assertFalse(saver.fobj)
            self.assertFalse(saver.fobj_on)

    def test_saver_write(self):
        for saver in [utils.NpzSaver(self.npzfile),
                      utils.Hdf5Saver(self.hd5file)]:
            self.assertFalse(saver.write('', {'ver': '1'}))
            saver.iopen()
            self.assertFalse(saver.write('/', []))
            saver.write('/', {'num': 100, 'list': [1, 2, 3]})
            saver.close()


class TestLoader(unittest.TestCase):
    '''
    Test NpzLoader, Hdf5Loader load pickled data
    '''

    def setUp(self):
        tmpfile = tempfile.mktemp(suffix='-test')
        self.npzfile = tmpfile + '.npz'
        self.hd5file = tmpfile + '.hdf5'
        for saver in [utils.NpzSaver(self.npzfile),
                      utils.Hdf5Saver(self.hd5file)]:
            saver.iopen()
            saver.write('/', {'num': 100, 'description': 'test case'})
            saver.write('group', {'str': 'abc', 'list': [1, 2, 3]})
            saver.close()

        self.npzfile2 = tmpfile + '-nodesc.npz'
        self.hd5file2 = tmpfile + '-nodesc.hdf5'
        for saver in [utils.NpzSaver(self.npzfile2),
                      utils.Hdf5Saver(self.hd5file2)]:
            saver.iopen()
            saver.write('/', {'num': 100})
            saver.close()

    def tearDown(self):
        if os.path.isfile(self.npzfile):
            os.remove(self.npzfile)
        if os.path.isfile(self.hd5file):
            os.remove(self.hd5file)
        if os.path.isfile(self.npzfile2):
            os.remove(self.npzfile2)
        if os.path.isfile(self.hd5file2):
            os.remove(self.hd5file2)

    def test_loader_init(self):
        with self.assertRaises(IOError):
            utils.NpzLoader(os.path.join(self.npzfile, 'BreakSuffix'))
        with self.assertRaises(IOError):
            utils.Hdf5Loader(os.path.join(self.hd5file, 'BreakSuffix'))
        with self.assertRaises((KeyError, ValueError)):
            utils.NpzLoader(self.npzfile2)
        with self.assertRaises((KeyError, ValueError)):
            utils.Hdf5Loader(self.hd5file2)

    def test_loader_keys(self):
        for loader in [utils.NpzLoader(self.npzfile),
                       utils.Hdf5Loader(self.hd5file)]:
            inkeys = {'num', 'description', 'group/str', 'group/list'}
            outkeys = set(loader.keys())
            self.assertSetEqual(inkeys, outkeys)

    def test_loader_get(self):
        for loader in [utils.NpzLoader(self.npzfile),
                       utils.Hdf5Loader(self.hd5file)]:
            inval = [100, 'test case', 'abc', [1, 2, 3]]
            outval = []
            for key in ['num', 'description', 'group/str']:
                outval.append(loader[key])
            outval.append(list(loader['group/list']))
            self.assertListEqual(inval, outval)

    def test_loader_find(self):
        for loader in [utils.NpzLoader(self.npzfile),
                       utils.Hdf5Loader(self.hd5file)]:
            outval = set(loader.find('st'))
            inval = {'group/str', 'group/list'}
            self.assertSetEqual(inval, outval)

    def test_loader_get_many(self):
        for loader in [utils.NpzLoader(self.npzfile),
                       utils.Hdf5Loader(self.hd5file)]:
            inval = (100, 'test case', 'abc')
            outval = loader.get_many('num', 'description', 'group/str')
            self.assertTupleEqual(inval, outval)
