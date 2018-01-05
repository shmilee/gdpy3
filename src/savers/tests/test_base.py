# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import unittest
import tempfile

from ..base import BaseFileSaver

class TestBaseFileSaver(unittest.TestCase):
    '''
    Test class BaseFileSaver
    '''

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix='-test')
        self.tmpfile = self.tmp + BaseFileSaver._extension

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_filesaver_init(self):
        saver = BaseFileSaver(self.tmp)
        self.assertTrue(saver.file == self.tmpfile)
        self.assertIsNone(saver.fobj)
        with self.assertRaises(IOError):
            BaseFileSaver(os.path.join(self.tmpfile, 'BreakSuffix'))

    def test_filesaver_iopen(self):
        saver = BaseFileSaver(self.tmpfile)
        with self.assertRaises(NotImplementedError):
            saver.iopen()

    def test_filesaver_write(self):
        saver = BaseFileSaver(self.tmpfile)
        with open(saver.file,mode='w') as saver.fobj:
            with self.assertRaises(NotImplementedError):
                saver.write('g', {'t': 1})

    def test_filesaver_close(self):
        saver = BaseFileSaver(self.tmpfile)
        with open(saver.file,mode='w') as saver.fobj:
            with self.assertRaises(NotImplementedError):
                saver.close()
