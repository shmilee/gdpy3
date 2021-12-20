# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import os
import unittest
import tempfile


class TestCachePckSaver(unittest.TestCase):
    '''
    Test class CachePckSaver
    '''

    def setUp(self):
        from ..cachepck import CachePckSaver
        self.PckSaver = CachePckSaver
        self.tmp = tempfile.mktemp(suffix='-test')
        self.tmpfile = self.tmp + CachePckSaver._extension

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_cachesaver_iopen_close(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.status)
        saver.iopen()
        self.assertTrue(saver.status)
        saver.close()
        self.assertFalse(saver.status)

    def test_cachesaver_write(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.write('', {'ver': '1'}))
        saver.iopen()
        self.assertFalse(saver.write('/', []))
        self.assertTrue(saver.write('', {'ver': '1'}))
        self.assertTrue(saver.write('/', {'num': 100, 'list': [1, 2, 3]}))
        self.assertTrue(saver.write('group', {'desc': 'desc'}))
        self.assertTrue(saver.write('grp/sub', {'n': 1}))
        saver.close()
        store = saver.get_store()
        inkeys = {'pathstr', 'ver', 'num', 'list', 'group/desc', 'grp/sub/n'}
        outkeys = set()
        for k in store.keys():
            if isinstance(store[k], dict):
                outkeys.update([k + '/' + kk for kk in store[k]])
            else:
                outkeys.add(k)
        self.assertSetEqual(inkeys, outkeys)

    def test_cachesaver_write_str_byte(self):
        with self.PckSaver(self.tmpfile) as saver:
            self.assertTrue(saver.write('', {'sver': r'v1'}))
            self.assertTrue(saver.write('', {'bver': b'v1'}))
        store = saver.get_store()
        self.assertEqual(store['sver'], r'v1')
        self.assertEqual(store['bver'], b'v1')

    def test_cachesaver_with(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.status)
        with saver:
            self.assertIsNotNone(saver._storeobj)
            self.assertTrue(saver.status)
        self.assertTrue(isinstance(saver._storeobj, dict))
        self.assertFalse(saver.status)
