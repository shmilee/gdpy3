# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import os
import tempfile
import numpy


class PckSaverTest(object):
    ''' Common test methods for PckSaver '''
    PckSaver = None

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix='-test')
        self.tmpfile = self.tmp + self.PckSaver._extension

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def saver_iopen_close(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.status)
        saver.iopen()
        self.assertTrue(saver.status)
        saver.close()
        self.assertFalse(saver.status)

    def saver_write(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.write('', {'ver': '1'}))
        saver.iopen()
        self.assertFalse(saver.write('/', []))
        self.assertTrue(saver.write('', {'ver': '1'}))
        self.assertTrue(saver.write('/', {'num': 100, 'list': [1, 2, 3]}))
        self.assertTrue(saver.write('group', {'desc': 'desc'}))
        self.assertTrue(saver.write('grp/sub', {'n': 1}))
        saver.close()
        inkeys = {'ver', 'num', 'list', 'group/desc', 'grp/sub/n'}
        outkeys = self.saver_get_keys(saver.get_store())
        self.assertSetEqual(inkeys, outkeys)

    def saver_get_keys(self, store):
        raise NotImplementedError()

    def saver_get(self, store, *keys):
        raise NotImplementedError()

    def saver_write_str_byte(self):
        with self.PckSaver(self.tmpfile) as saver:
            self.assertTrue(saver.write('', {'sver': r'v1', 'bver': b'v1'}))
            store = saver.get_store()
        sver, bver = self.saver_get(store, 'sver', 'bver')
        self.assertEqual(sver, r'v1')
        self.assertEqual(bver, b'v1')

    def saver_write_num_arr(self):
        with self.PckSaver(self.tmpfile) as saver:
            self.assertTrue(saver.write('', {'n': 1, 'f': 1.1, 'a': [1, 2]}))
            store = saver.get_store()
        n, f, a = self.saver_get(store, 'n', 'f', 'a')
        self.assertEqual(n, 1)
        self.assertEqual(f, 1.1)
        self.assertTrue(numpy.array_equal(a, numpy.array([1, 2])))

    def saver_with(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.status)
        with saver:
            self.assertIsNotNone(saver._storeobj)
            self.assertTrue(saver.status)
        self.assertIsNone(saver._storeobj)
        self.assertFalse(saver.status)
