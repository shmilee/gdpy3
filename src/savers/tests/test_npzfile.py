# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

import os
import unittest
import tempfile
import numpy


class TestNpzFileSaver(unittest.TestCase):
    '''
    Test class NpzFileSaver
    '''

    def setUp(self):
        from ..npzfile import NpzFileSaver
        self.NpzFileSaver = NpzFileSaver
        self.tmp = tempfile.mktemp(suffix='-test')
        self.tmpfile = self.tmp + NpzFileSaver._extension

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_npzsaver_iopen_close(self):
        saver = self.NpzFileSaver(self.tmpfile)
        self.assertFalse(saver.fobj)
        saver.iopen()
        self.assertTrue(saver.fobj)
        saver.close()
        self.assertFalse(saver.fobj)

    def test_npzsaver_write(self):
        saver = self.NpzFileSaver(self.tmpfile)
        self.assertFalse(saver.write('', {'ver': '1'}))
        saver.iopen()
        self.assertFalse(saver.write('/', []))
        self.assertTrue(saver.write('', {'ver': '1'}))
        self.assertTrue(saver.write('/', {'num': 100, 'list': [1, 2, 3]}))
        self.assertTrue(saver.write('group', {'desc': 'desc'}))
        saver.close()
        npz = numpy.load(saver.file)
        inkeys = {'ver', 'num', 'list', 'group/desc'}
        outkeys = set(npz.files)
        self.assertSetEqual(inkeys, outkeys)

