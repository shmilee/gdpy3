# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import numpy
import unittest
import tempfile

from .. import glogger
from ..convert import utils

glogger.getGLogger('gdc').handlers[0].setLevel(60)


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
        return None
        with self.assertRaises(IOError):
            utils.NpzSaver(os.path.join(self.npzfile, 'BreakSuffix'))
        with self.assertRaises(IOError):
            utils.Hdf5Saver(os.path.join(self.hd5file, 'BreakSuffix'))

    def test_saver_iopen_close(self):
        for f in [self.npzfile, self.hd5file]:
            ext = os.path.splitext(f)[1]
            if ext == '.npz':
                saver = utils.NpzSaver(f)
            else:
                saver = utils.Hdf5Saver(f)
            self.assertTrue(saver.iopen())
            self.assertTrue(saver.fobj)
            self.assertTrue(saver.fobj_on)
            saver.close()
            self.assertFalse(saver.fobj)
            self.assertFalse(saver.fobj_on)

    def test_saver_write(self):
        for f in [self.npzfile, self.hd5file]:
            ext = os.path.splitext(f)[1]
            if ext == '.npz':
                saver = utils.NpzSaver(f)
            else:
                saver = utils.Hdf5Saver(f)
            self.assertFalse(saver.write('', {'ver': '1'}))
            saver.iopen()
            self.assertFalse(saver.write('/', []))
            saver.write('/', {'num': 100, 'list': [1, 2, 3]})
            saver.close()


class TestNpzLoader(unittest.TestCase):
    '''
    Test NpzLoader load pickled data
    '''

    def setUp(self):
        tmpfile = tempfile.mktemp(suffix='-test.npz')
        saver = utils.NpzSaver(tmpfile)
        saver.iopen()
        saver.write('/', {'num': 100, 'description': 'test case'})
        saver.write('group', {'str': 'abc', 'list': [1, 2, 3]})
        saver.close()
        self.tmpfile = tmpfile
        self.loadercls = utils.NpzLoader

        tmpfile2 = tempfile.mktemp(suffix='-test.npz')
        saver = utils.NpzSaver(tmpfile2)
        saver.iopen()
        saver.write('/', {'num': 100})
        saver.close()
        self.tmpfile2 = tmpfile2

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)
        if os.path.isfile(self.tmpfile2):
            os.remove(self.tmpfile2)

    def test_npzloader_init(self):
        with self.assertRaises(IOError):
            self.loadercls(os.path.join(self.tmpfile, 'BreakSuffix'))
        with self.assertRaises((KeyError, ValueError)):
            self.loadercls(self.tmpfile2)

    def test_npzloader_keys(self):
        inkeys = {'num', 'description', 'group/str', 'group/list'}
        outkeys = set(self.loadercls(self.tmpfile).keys())
        self.assertEqual(inkeys, outkeys)

    def test_npzloader_get(self):
        inval = [100, 'test case', 'abc', [1, 2, 3]]
        outval = []
        loader = self.loadercls(self.tmpfile)
        for key in ['num', 'description', 'group/str']:
            outval.append(loader[key])
        outval.append(list(loader['group/list']))
        self.assertEqual(inval, outval)

    def test_npzloader_find(self):
        loader = self.loadercls(self.tmpfile)
        outval = set(loader.find('st'))
        inval = {'group/str', 'group/list'}
        self.assertEqual(inval, outval)

    def test_npzloader_get_many(self):
        inval = (100, 'test case', 'abc')
        loader = self.loadercls(self.tmpfile)
        outval = loader.get_many('num', 'description', 'group/str')
        self.assertEqual(inval, outval)


class TestHdf5Loader(unittest.TestCase):
    '''
    Test Hdf5Loader load pickled data
    '''

    def setUp(self):
        tmpfile = tempfile.mktemp(suffix='-test.hdf5')
        saver = utils.Hdf5Saver(tmpfile)
        saver.iopen()
        saver.write('/', {'num': 100, 'description': 'test case'})
        saver.write('group', {'str': 'abc', 'list': [1, 2, 3]})
        saver.close()
        self.tmpfile = tmpfile
        self.loadercls = utils.Hdf5Loader

        tmpfile2 = tempfile.mktemp(suffix='-test.hdf5')
        saver = utils.Hdf5Saver(tmpfile2)
        saver.iopen()
        saver.write('/', {'num': 100})
        saver.close()
        self.tmpfile2 = tmpfile2

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)
        if os.path.isfile(self.tmpfile2):
            os.remove(self.tmpfile2)

    def test_hd5loader_init(self):
        with self.assertRaises(IOError):
            self.loadercls(os.path.join(self.tmpfile, 'BreakSuffix'))
        with self.assertRaises((KeyError, ValueError)):
            self.loadercls(self.tmpfile2)

    def test_hd5loader_keys(self):
        inkeys = {'num', 'description', 'group/str', 'group/list'}
        outkeys = set(self.loadercls(self.tmpfile).keys())
        self.assertEqual(inkeys, outkeys)

    def test_hd5loader_get(self):
        inval = [100, 'test case', 'abc', [1, 2, 3]]
        outval = []
        loader = self.loadercls(self.tmpfile)
        for key in ['num', 'description', 'group/str']:
            outval.append(loader[key])
        outval.append(list(loader['group/list']))
        self.assertEqual(inval, outval)

    def test_hd5loader_find(self):
        loader = self.loadercls(self.tmpfile)
        outval = set(loader.find('st'))
        inval = {'group/str', 'group/list'}
        self.assertEqual(inval, outval)

    def test_hd5loader_get_many(self):
        inval = (100, 'test case', 'abc')
        loader = self.loadercls(self.tmpfile)
        outval = loader.get_many('num', 'description', 'group/str')
        self.assertEqual(inval, outval)
