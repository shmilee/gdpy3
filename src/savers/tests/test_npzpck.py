# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

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
        self.assertTrue(saver.write('grp/sub', {'n': 1}))
        saver.close()
        npz = numpy.load(saver.get_store())
        inkeys = {'ver', 'num', 'list', 'group/desc', 'grp/sub/n'}
        outkeys = set(npz.files)
        self.assertSetEqual(inkeys, outkeys)

    def test_npzsaver_overwrite(self):
        with self.PckSaver(self.tmpfile) as saver:
            self.assertTrue(saver.write('/', {'v': 1}))
            self.assertTrue(saver.write('', {'v': 2}))
            for i in range(3):
                saver.write('/', {'a%d' % i: i})
        npz = numpy.load(saver.get_store())
        self.assertEqual(npz['v'], 2)
        with self.PckSaver(self.tmpfile, duplicate_name=False) as saver:
            self.assertTrue(saver.write('g/k', {'num': 10}))
            self.assertTrue(saver.write('g/k', {'num': 20}))
        npz = numpy.load(saver.get_store())
        self.assertEqual(npz['g/k/num'], 20)
        inkeys = {'v', 'a0', 'a1', 'a2', 'g/k/num'}
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
