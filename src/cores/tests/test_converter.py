# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

import unittest

from . import RawLoader
from ..converter import Converter


class TestConverter(unittest.TestCase):
    '''
    Test class Converter
    '''

    def setUp(self):
        self.raw = RawLoader()

    def test_one2one_file(self):
        class ImpConverter1(Converter):
            nitems = '?'
            itemspattern = ['^(?P<section>g).out$']

            def _convert(self):
                return {'a': 1}

        cores = ImpConverter1.generate_cores(self.raw)
        self.assertEqual(len(cores), 1)
        self.assertEqual(cores[0].files, 'g.out')
        self.assertEqual(cores[0].group, 'g')
        self.assertEqual(cores[0].convert(), {'a': 1})
        self.assertEqual(cores[0].short_files, 'g.out')

    def test_multi2multi_file(self):
        class ImpConverter2(Converter):
            nitems = '?'
            itemspattern = ['^(?P<section>s\d).out$']

        cores = ImpConverter2.generate_cores(self.raw)
        self.assertEqual(len(cores), 3)
        self.assertEqual(cores[0].files, 's0.out')
        self.assertEqual(cores[0].group, 's0')
        with self.assertRaises(NotImplementedError):
            res = cores[0]._convert()
        self.assertEqual(cores[1].files, 's2.out')

    def test_multi2one_file(self):
        class ImpConverter3(Converter):
            nitems = '+'
            itemspattern = ['^p/(?P<section>s\d)_t\d.out$']

            def _convert(self):
                pass

        cores = ImpConverter3.generate_cores(self.raw)
        self.assertEqual(len(cores), 2)
        self.assertEqual(cores[0].files, ['p/s0_t0.out',
                                          'p/s0_t1.out', 'p/s0_t2.out'])
        self.assertEqual(cores[0].group, 's0')
        self.assertEqual(cores[0].convert(), None)
        self.assertEqual(cores[0].short_files, 'p/s0_t*.out')
