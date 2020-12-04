# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

import os
import unittest
import tempfile
import contextlib

from ..base import BaseRawLoader, BasePckLoader


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
        return self.path

    def _special_close(self, pathobj):
        self._special_history.append('close')

    def _special_getkeys(self, pathobj):
        return self._D.keys()

    def _special_get(self, pathobj, key):
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
                             ['check', 'open'])
        loader.update()
        self.assertListEqual(loader._special_history,
                             ['check', 'open', 'close', 'open'])

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

    def test_rawloader_find(self):
        loader = ImpBaseRawLoader(self.tmpfile)
        self.assertEqual(loader.find('d', 2), ('d2/f2',))
        self.assertEqual(loader.refind('^d2.*'), ('d2/f2',))

    def test_rawloader_contains(self):
        loader = ImpBaseRawLoader(self.tmpfile)
        self.assertTrue('f1' in loader)
        self.assertTrue(loader.all_in_loader('f1', 'd2/f2'))
        self.assertFalse(loader.all_in_loader('f1', 'd2/f2', 'f3'))


class ImpBasePckLoader(BasePckLoader):

    _D = {'description': 'desc', 'k1': 1, 'g2/k2': 2,
          'g3/k3': 3, 'g3/k33': 33, 'g4/sg4/k4': 4}
    _G = ('g2', 'g3', 'g4/sg4')

    def _special_check_path(self):
        return os.path.isfile(self.path)

    def _special_open(self):
        return True

    def _special_close(self, pathobj):
        pass

    def _special_getkeys(self, pathobj):
        return tuple(self._D.keys())

    def _special_get(self, pathobj, key):
        return self._D[key]


class TestBasePckLoader(unittest.TestCase):
    '''
    Test class BasePckLoader
    '''

    def setUp(self):
        self.tmpfile = tempfile.mktemp(suffix='-test')
        with open(self.tmpfile, mode='w') as f:
            f.write('test')

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_pckloader_init(self):
        with self.assertRaises(NotImplementedError):
            BasePckLoader(self.tmpfile)
        with self.assertRaises(IOError):
            ImpBasePckLoader(os.path.join(self.tmpfile, 'BreakSuffix'))
        loader = ImpBasePckLoader(self.tmpfile)
        self.assertTrue(loader.path == self.tmpfile)
        self.assertSetEqual(
            set(loader.datakeys), set(ImpBasePckLoader._D.keys()))
        self.assertSetEqual(
            set(loader.datagroups), set(ImpBasePckLoader._G))
        self.assertMultiLineEqual(loader.description, 'desc')
        self.assertEqual(len(loader.cache), 0)
        loader = ImpBasePckLoader(
            self.tmpfile,
            datagroups_exclude=[r'^g2$'])
        self.assertSetEqual(
            set(loader.datagroups), {'g3', 'g4/sg4'})

    def test_pckloader_get(self):
        loader = ImpBasePckLoader(self.tmpfile)
        self.assertEqual(loader.get('k1'), 1)
        self.assertEqual(loader['g2/k2'], 2)
        self.assertEqual(loader.get('g4/sg4/k4'), 4)
        with self.assertRaises(KeyError):
            loader.get('lost-key')

    def test_pckloader_get_many(self):
        loader = ImpBasePckLoader(self.tmpfile)
        self.assertEqual(loader.get_many('k1', 'g2/k2'), (1, 2))
        self.assertTrue('k1' in loader.cache)

    def test_pckloader_get_by_group(self):
        loader = ImpBasePckLoader(self.tmpfile)
        self.assertEqual(loader.get_by_group('g3'), {'k3': 3, 'k33': 33})

    def test_pckloader_find(self):
        loader = ImpBasePckLoader(self.tmpfile)
        self.assertEqual(loader.find('g', 33), ('g3/k33',))
        self.assertEqual(loader.refind('^g.*4$'), ('g4/sg4/k4',))

    def test_pckloader_contains(self):
        loader = ImpBasePckLoader(self.tmpfile)
        self.assertTrue(loader.all_in_loader('k1', 'g2/k2', 'g4/sg4/k4'))
        self.assertFalse(loader.all_in_loader('k1', 'g2/k2', 'lost-key'))
