# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

import os
import unittest
import tempfile
import numpy


class TestNpzPckSaver(unittest.TestCase):
    '''
    Test class NpzPckSaver
    '''

    def setUp(self):
        from ..npzpck import NpzPckSaver
        self.PckSaver = NpzPckSaver
        self.tmp = tempfile.mktemp(suffix='-test')
        self.tmpfile = self.tmp + NpzPckSaver._extension

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_npzsaver_iopen_close(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.status)
        saver.iopen()
        self.assertTrue(saver.status)
        saver.close()
        self.assertFalse(saver.status)

    def test_npzsaver_write(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.write('', {'ver': '1'}))
        saver.iopen()
        self.assertFalse(saver.write('/', []))
        self.assertTrue(saver.write('', {'ver': '1'}))
        self.assertTrue(saver.write('/', {'num': 100, 'list': [1, 2, 3]}))
        self.assertTrue(saver.write('group', {'desc': 'desc'}))
        saver.close()
        npz = numpy.load(saver.get_store())
        inkeys = {'ver', 'num', 'list', 'group/desc'}
        outkeys = set(npz.files)
        self.assertSetEqual(inkeys, outkeys)

    def test_npzsaver_with(self):
        saver = self.PckSaver(self.tmpfile)
        self.assertFalse(saver.status)
        with saver:
            self.assertIsNotNone(saver._storeobj)
            self.assertTrue(saver.status)
        self.assertIsNone(saver._storeobj)
        self.assertFalse(saver.status)
