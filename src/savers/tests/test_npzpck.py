# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import unittest
import numpy
from . import PckSaverTest
from ..npzpck import NpzPckSaver


class TestNpzPckSaver(PckSaverTest, unittest.TestCase):
    ''' Test class NpzPckSaver'''
    PckSaver = NpzPckSaver

    def test_npzsaver_iopen_close(self):
        self.saver_iopen_close()

    def test_npzsaver_write(self):
        self.saver_write()

    def saver_get_keys(self, store):
        npz = numpy.load(store)
        return set(npz.files)

    def saver_get(self, store, *keys):
        npz = numpy.load(store)
        return [npz[k].item() if npz[k].size == 1 else npz[k] for k in keys]

    def test_npzsaver_write_str_byte(self):
        self.saver_write_str_byte()

    def test_npzsaver_write_num_arr(self):
        self.saver_write_num_arr()

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
        self.saver_with()
