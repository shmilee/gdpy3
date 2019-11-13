# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

import re
import unittest

from . import PckLoader
from ..digger import Digger


class ImpDigger1(Digger):
    '''
    Get four cores:
    1. 'da/i-p-f', 2. 'da/i-m-f', 3. 'da/e-p-f', 4. 'da/e-m-f'
    '''
    nitems = '?'
    itemspattern = ['^(?P<sect>da)/(?P<spc>(?:i|e))-(?P<fld>(?:p|m))-f$']
    commonpattern = ['g/c', 'his/n']
    neededpattern = ['da/(?:i|e)-(?:p|m)-f', 'g/c']

    def _set_fignum(self):
        self._fignum = '%s_%s_f' % (self.section[1], self.section[2])

    def _dig(self):
        return self.fignum


class ImpDigger2(Digger):
    '''
    Get two cores:
    1. 'his/i', 'his/n'
    2. 'his/e', 'his/n'
    '''
    nitems = '+'
    itemspattern = ['^(?P<sect>his)/(?P<spc>(?:i|e))$', '^(?P<sect>his)/n']
    commonpattern = ['g/c']
    neededpattern = 'ALL'

    def _set_fignum(self):
        self._fignum = self.section[1]

    def _dig(self):
        return self.fignum


class ImpDigger3(ImpDigger2):
    '''
    Get four cores:
    1. 's0/p', 's0/x', 's0/y'
    2. 's0/a', 's0/x', 's0/y'
    3. 's2/p', 's2/x', 's2/y'
    4. 's2/a', 's2/x', 's2/y'
    '''
    nitems = '+'
    itemspattern = ['^(?P<sect>s\d)/(?P<fld>(?:p|a))$',
                    '^(?P<sect>s\d)/(?:x|y)$']
    commonpattern = ['g/c']
    neededpattern = ['^(?P<sect>s\d)/(?P<fld>(?:p|a))$',
                     '^(?P<sect>s\d)/x$', '^(?P<sect>s\d)/y$']


class ImpDigger4(ImpDigger2):
    '''Get four cores: ImpDigger2 two cores, with numseed 1 or 'a'.'''
    numseeds = [1, 'a']

    def _set_fignum(self, numseed=None):
        self._fignum = '%s_%s' % (self.section[1], numseed)


class TestDigger(unittest.TestCase):
    '''
    Test class Digger
    '''

    def setUp(self):
        self.pck = PckLoader()

    def test_one_key_2_one_core(self):
        cores = ImpDigger1.generate_cores(self.pck)
        self.assertEqual(len(cores), 4)
        self.assertEqual(cores[0].srckeys, ['da/i-p-f'])
        self.assertEqual(cores[0].extrakeys, ['g/c', 'his/n'])
        self.assertEqual(cores[0].group, 'da')
        self.assertEqual(cores[0].dig(), 'i_p_f')

    def test_one_addition_key_2_one_core(self):
        cores = ImpDigger2.generate_cores(self.pck)
        self.assertEqual(len(cores), 2)
        self.assertEqual(cores[0].srckeys, ['his/i', 'his/n'])
        self.assertEqual(cores[0].extrakeys, ['g/c'])
        self.assertEqual(cores[0].group, 'his')
        self.assertEqual(cores[0].dig(), 'i')

    def test_multi_addition_key_2_one_core(self):
        cores = ImpDigger3.generate_cores(self.pck)
        self.assertEqual(len(cores), 4)
        self.assertEqual(cores[0].srckeys, ['s0/p', 's0/x', 's0/y'])
        self.assertEqual(cores[0].extrakeys, ['g/c'])
        self.assertEqual(cores[0].group, 's0')
        self.assertEqual(cores[0].dig(), 'p')
        self.assertEqual(cores[3].group, 's2')
        self.assertEqual(cores[3].dig(), 'a')

    def test_one_addition_key_2_one_core_with_numseeds(self):
        cores = ImpDigger4.generate_cores(self.pck)
        self.assertEqual(len(cores), 4)
        self.assertEqual(cores[0].fignum, 'i_1')
        self.assertEqual(cores[1].fignum, 'i_a')
        self.assertEqual(cores[2].fignum, 'e_1')
        self.assertEqual(cores[3].fignum, 'e_a')
