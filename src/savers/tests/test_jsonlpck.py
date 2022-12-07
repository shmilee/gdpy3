# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import os
import unittest
import tempfile


class TestJsonlPckSaver(unittest.TestCase):
    '''
    Test class JsonlPckSaver
    '''

    def setUp(self):
        from ..jsonlpck import JsonLines, JsonlPckSaver
        self.JsonLines = JsonLines
        self.PckSaver = JsonlPckSaver
        self.tmp = tempfile.mktemp(suffix='-test')
        self.tmpfile = self.tmp + JsonlPckSaver._extension

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_jsonlsaver_iopen_close(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.status)
        saver.iopen()
        self.assertTrue(saver.status)
        saver.close()
        self.assertFalse(saver.status)

    def test_jsonlsaver_write(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.write('', {'ver': '1'}))
        saver.iopen()
        self.assertFalse(saver.write('/', []))
        self.assertTrue(saver.write('', {'ver': '1'}))
        self.assertTrue(saver.write('/', {'num': 100, 'list': [1, 2, 3]}))
        self.assertTrue(saver.write('group', {'desc': 'desc'}))
        self.assertTrue(saver.write('grp/sub', {'n': 1}))
        saver.close()
        jl = self.JsonLines(saver.get_store())
        inkeys = {'ver', 'num', 'list', 'group/desc', 'grp/sub/n'}
        outkeys = set(k for k in jl.index if k != '__RecordCount__')
        self.assertSetEqual(inkeys, outkeys)

    def test_jsonlsaver_write_str_byte(self):
        with self.PckSaver(self.tmpfile) as saver:
            self.assertTrue(saver.write('', {'sver': r'v1'}))
            self.assertTrue(saver.write('', {'bver': b'v1'}))
        jl = self.JsonLines(saver.get_store())
        self.assertEqual(jl.get_record('sver'), r'v1')
        self.assertEqual(jl.get_record('bver'), b'v1')

    def test_jsonlsaver_with(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.status)
        with saver:
            self.assertIsNotNone(saver._storeobj)
            self.assertTrue(saver.status)
        self.assertIsNone(saver._storeobj)
        self.assertFalse(saver.status)
