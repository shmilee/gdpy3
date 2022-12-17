# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import unittest
from . import PckSaverTest
from ..cachepck import CachePckSaver


class TestCachePckSaver(PckSaverTest, unittest.TestCase):
    ''' Test class CachePckSaver '''
    PckSaver = CachePckSaver

    def test_cachesaver_iopen_close(self):
        self.saver_iopen_close()

    def test_cachesaver_write(self):
        self.saver_write()

    def saver_get_keys(self, store):
        outkeys = set()
        for k in store.keys():
            if isinstance(store[k], dict):
                outkeys.update([k + '/' + kk for kk in store[k]])
            else:
                outkeys.add(k)
        outkeys.remove('pathstr')
        return outkeys

    def saver_get(self, store, *keys):
        res = []
        for key in keys:
            gstop = key.rfind('/')
            if gstop == -1:
                res.append(store[key])
            elif gstop > 0:
                res.append(store[key[:gstop]][key[gstop+1:]])
        return res

    def test_cachesaver_write_str_byte(self):
        self.saver_write_str_byte()

    def test_cachesaver_with(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.status)
        with saver:
            self.assertIsNotNone(saver._storeobj)
            self.assertTrue(saver.status)
        self.assertTrue(isinstance(saver._storeobj, dict))  # IsNotNone
        self.assertFalse(saver.status)
