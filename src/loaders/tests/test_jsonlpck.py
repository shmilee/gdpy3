# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import os
import unittest
import tempfile
import numpy

from . import DATA


class TestJsonlPckLoader(unittest.TestCase):
    '''
    Test class JsonlPckLoader
    '''

    def setUp(self):
        from ..jsonlpck import JsonLines, JsonlPckLoader
        self.PckLoader = JsonlPckLoader
        self.tmpfile = tempfile.mktemp(suffix='-test.jsonl')
        self.tmpfilegz = self.tmpfile + '-gz'
        jl = JsonLines(self.tmpfile)
        jl.update(DATA)
        jl.finalize(self.tmpfilegz, slim_jsonl=True)

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)
        if os.path.isfile(self.tmpfilegz):
            os.remove(self.tmpfilegz)

    def _t_loader_init(self, tmpfile):
        loader = self.PckLoader(tmpfile)
        self.assertSetEqual(set(loader.datakeys), set(DATA.keys()))
        self.assertSetEqual(set(loader.datagroups), {'test', 'te/st'})
        self.assertMultiLineEqual(loader.description, DATA['description'])

    def test_jsonlloader_init(self):
        self._t_loader_init(self.tmpfile)

    def test_jsonlloader_init_gz(self):
        self._t_loader_init(self.tmpfilegz)

    def _t_loader_get(self, tmpfile):
        loader = self.PckLoader(tmpfile)
        self.assertEqual(loader.get('bver'), DATA['bver'])
        self.assertTrue(
            numpy.array_equal(loader.get('test/array'), DATA['test/array']))
        self.assertEqual(loader.get('test/float'), 3.1415)
        self.assertEqual(loader.get('te/st/int'), 1)

    def test_jsonlloader_get(self):
        self._t_loader_get(self.tmpfile)

    def test_jsonlloader_get_gz(self):
        self._t_loader_get(self.tmpfilegz)
