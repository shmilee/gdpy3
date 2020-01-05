# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

import unittest

from . import RawLoader, PckLoader
from ..base import BaseCore


class TestBaseCore(unittest.TestCase):
    '''
    Test class BaseCore
    '''

    def setUp(self):
        self.raw = RawLoader()
        self.pck = PckLoader()

    def test_one_section_one_item_core(self):
        class ImpBaseCore11(BaseCore):
            nitems = '?'
            itemspattern = ['.*/(?P<section>eq).out$', '^(?P<section>eq).out$']
            commonpattern = ['g.out']

        cores = ImpBaseCore11.generate_cores(self.raw, self.raw.filenames)
        self.assertEqual(len(cores), 1)
        self.assertEqual(cores[0].loader.path, 'test/rawlodaer')
        self.assertEqual(cores[0].section, ('eq',))
        self.assertEqual(cores[0].items, ['eq.out'])
        self.assertEqual(cores[0].common, ['g.out'])

        ImpBaseCore11.itemspattern = ['^(?P<section>s\d).out$']
        cores = ImpBaseCore11.generate_cores(self.raw, self.raw.filenames)
        self.assertEqual(len(cores), 3)
        self.assertEqual(cores[0].section, ('s0',))
        self.assertEqual(cores[0].items, ['s0.out'])

    def test_two_section_one_item_core(self):
        class ImpBaseCore21(BaseCore):
            nitems = '?'
            itemspattern = ['^(?P<sect1>his)/(?P<sect2>(?:i|e))$']
            commonpattern = ['g/c']

        cores = ImpBaseCore21.generate_cores(self.pck, self.pck.datakeys)
        self.assertEqual(len(cores), 2)
        self.assertEqual(cores[0].loader.path, 'test/pcklodaer')
        self.assertEqual(cores[0].section, ('his', 'i'))
        self.assertEqual(cores[0].items, ['his/i'])
        self.assertEqual(cores[0].common, ['g/c'])

    def test_one_section_multi_items_core(self):
        class ImpBaseCore12(BaseCore):
            nitems = '+'
            itemspattern = ['^p/(?P<section>s\d)_t\d.out$']
            commonpattern = ['g.out']

        cores = ImpBaseCore12.generate_cores(self.raw, self.raw.filenames)
        self.assertEqual(len(cores), 2)
        self.assertEqual(cores[0].section, ('s0',))
        self.assertEqual(cores[0].items, ['p/s0_t0.out',
                                          'p/s0_t1.out', 'p/s0_t2.out'])
        self.assertEqual(cores[0].common, ['g.out'])

    def test_two_section_multi_items_core(self):
        class ImpBaseCore22(BaseCore):
            nitems = '+'
            itemspattern = [
                '^(?P<sect1>his)/(?P<sect2>(?:i|e))$', '^(?P<sect1>his)/n']
            commonpattern = ['g/c']

        cores = ImpBaseCore22.generate_cores(self.pck, self.pck.datakeys)
        self.assertEqual(len(cores), 2)
        self.assertEqual(cores[0].loader.path, 'test/pcklodaer')
        self.assertEqual(cores[0].section, ('his', 'i'))
        self.assertEqual(cores[0].items, ['his/i', 'his/n'])
        self.assertEqual(cores[0].common, ['g/c'])
        self.assertEqual(cores[1].section, ('his', 'e'))
        self.assertEqual(cores[1].items, ['his/e', 'his/n'])
        self.assertEqual(cores[1].common, ['g/c'])

        ImpBaseCore22.itemspattern = ['^(?P<sect1>s\d)/(?P<sect2>(?:p|a))$',
                                      '^(?P<sect1>s\d)/(?:x|y)$']
        cores = ImpBaseCore22.generate_cores(self.pck, self.pck.datakeys)
        self.assertEqual(len(cores), 4)
        self.assertEqual(cores[0].section, ('s0', 'p'))
        self.assertEqual(cores[0].items, ['s0/p', 's0/x', 's0/y'])
        self.assertEqual(cores[1].section, ('s0', 'a'))
        self.assertEqual(cores[1].items, ['s0/a', 's0/x', 's0/y'])

        ImpBaseCore22.itemspattern = ['^(?P<sect1>tp)/(?P<sect2>(?:i|e))-\d$']
        cores = ImpBaseCore22.generate_cores(self.pck, self.pck.datakeys)
        self.assertEqual(len(cores), 2)
        self.assertEqual(cores[0].section, ('tp', 'i'))
        self.assertEqual(cores[0].items, ['tp/i-1', 'tp/i-2', 'tp/i-3'])
