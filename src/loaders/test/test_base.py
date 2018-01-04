# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import unittest
import tempfile

from ..base import BaseFileLoader


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

    def test_loader_init(self):
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

    def test_loader_get(self):
        loader = ImpBaseFileLoader(self.tmpfile)
        self.assertEqual(loader.get('k1'), 1)
        self.assertEqual(loader['g2/k2'], 2)
        with self.assertRaises(KeyError):
            loader.get('lost-key')

    def test_loader_get_many(self):
        loader = ImpBaseFileLoader(self.tmpfile)
        self.assertEqual(loader.get_many('k1', 'g2/k2'), (1, 2))
        self.assertTrue('k1' in loader.cache)

    def test_loader_find(self):
        loader = ImpBaseFileLoader(self.tmpfile)
        self.assertEqual(loader.find('g', 4), ('g3/k4',))
