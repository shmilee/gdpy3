# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

import os
import unittest
import tempfile
import contextlib

from ..base import BaseRawLoader, BaseFileLoader


class ImpBaseRawLoader(BaseRawLoader):

    _D = {'f1': 1, 'd2/f2': 'two', 'd3/sd3/f3': 3}
    __slots__ = ['_special_history']

    class _Fcls(object):
        def __init__(self, data):
            self.data = data

        def close(self):
            self.data = None

        def read(self):
            return self.data

    def _special_check_path(self):
        self._special_history = ['check']
        return True

    def _special_open(self):
        self._special_history.append('open')
        return

    def _special_close(self, tmpobj):
        self._special_history.append('close')

    def _special_getkeys(self, tmpobj):
        return self._D.keys()

    def _special_getfile(self, tmpobj, key):
        return self._Fcls(self._D[key])


class TestBaseRawLoader(unittest.TestCase):
    '''
    Test class BaseRawLoader
    '''

    def setUp(self):
        self.tmpfile = tempfile.mktemp(suffix='-test')
        with open(self.tmpfile, mode='w') as f:
            f.write('test')

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_rawloader_init(self):
        with self.assertRaises(NotImplementedError):
            BaseRawLoader(self.tmpfile)
        with self.assertRaises(IOError):
            ImpBaseRawLoader(os.path.join(self.tmpfile, 'BreakSuffix'))
        loader = ImpBaseRawLoader(self.tmpfile)
        self.assertEqual(loader.path, self.tmpfile)
        self.assertSetEqual(set(loader.filenames),
                            set(ImpBaseRawLoader._D.keys()))
        self.assertListEqual(loader._special_history,
                             ['check', 'open', 'close'])

    def test_rawloader_get(self):
        loader = ImpBaseRawLoader(self.tmpfile)
        self.assertTrue(isinstance(loader.get('f1'),
                                   contextlib._GeneratorContextManager))
        with loader.get('d2/f2') as f2, loader.get('d3/sd3/f3') as f3:
            self.assertEqual(f2.read(), 'two')
            self.assertEqual(f3.read(), 3)
        with self.assertRaises(KeyError):
            with loader.get('lost-key'):
                pass


class ImpBaseFileLoader(BaseFileLoader):

    _D = {'description': 'desc', 'k1': 1, 'g2/k2': 2, 'g3/k3': 3, 'g3/k4': 4}
    _G = ('g2', 'g3')

    def _special_openfile(self):
        return True

    def _special_closefile(self, tmpobj):
        pass

    def _special_getkeys(self, tmpobj):
        return tuple(self._D.keys())

    def _special_getitem(self, tmpobj, key):
        return self._D[key]


class TestBaseFileLoader(unittest.TestCase):
    '''
    Test class BaseFileLoader
    '''

    def setUp(self):
        self.tmpfile = tempfile.mktemp(suffix='-test')
        with open(self.tmpfile, mode='w') as f:
            f.write('test')

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_fileloader_init(self):
        with self.assertRaises(NotImplementedError):
            BaseFileLoader(self.tmpfile)
        with self.assertRaises(IOError):
            ImpBaseFileLoader(os.path.join(self.tmpfile, 'BreakSuffix'))
        loader = ImpBaseFileLoader(self.tmpfile)
        self.assertTrue(loader.file == self.tmpfile)
        self.assertSetEqual(
            set(loader.datakeys), set(ImpBaseFileLoader._D.keys()))
        self.assertSetEqual(
            set(loader.datagroups), set(ImpBaseFileLoader._G))
        self.assertMultiLineEqual(loader.description, 'desc')
        self.assertEqual(len(loader.cache), 0)

    def test_fileloader_get(self):
        loader = ImpBaseFileLoader(self.tmpfile)
        self.assertEqual(loader.get('k1'), 1)
        self.assertEqual(loader['g2/k2'], 2)
        with self.assertRaises(KeyError):
            loader.get('lost-key')

    def test_fileloader_get_many(self):
        loader = ImpBaseFileLoader(self.tmpfile)
        self.assertEqual(loader.get_many('k1', 'g2/k2'), (1, 2))
        self.assertTrue('k1' in loader.cache)

    def test_fileloader_find(self):
        loader = ImpBaseFileLoader(self.tmpfile)
        self.assertEqual(loader.find('g', 4), ('g3/k4',))
