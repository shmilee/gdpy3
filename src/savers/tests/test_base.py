# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

import os
import unittest
import tempfile

from ..base import BasePckSaver


class TestBasePckSaver(unittest.TestCase):
    '''
    Test class BasePckSaver
    '''

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix='-test')
        self.tmpfile = self.tmp + BasePckSaver._extension

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_pcksaver_init(self):
        saver = BasePckSaver(self.tmp)
        self.assertTrue(saver.path == self.tmpfile)
        self.assertIsNone(saver._storeobj)
        with self.assertRaises(IOError):
            BasePckSaver(os.path.join(self.tmpfile, 'BreakSuffix'))

    def test_pcksaver_iopen(self):
        saver = BasePckSaver(self.tmpfile)
        with self.assertRaises(NotImplementedError):
            saver.iopen()

    def test_pcksaver_write(self):
        saver = BasePckSaver(self.tmpfile)
        with open(saver.path, mode='w') as saver._storeobj:
            saver.status = True
            with self.assertRaises(NotImplementedError):
                saver.write('g', {'t': 1})

    def test_pcksaver_close(self):
        saver = BasePckSaver(self.tmpfile)
        with open(saver.path, mode='w') as saver._storeobj:
            saver.status = True
            saver.close()
            self.assertIsNone(saver._storeobj)

    def test_pcksaver_get_store(self):
        saver = BasePckSaver(self.tmpfile)
        self.assertEqual(self.tmpfile, saver.get_store())
