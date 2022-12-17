# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import unittest

from . import DATA, DATA_C, PckLoaderTest
from ..cachepck import CachePckLoader


class TestCachePckLoader(PckLoaderTest, unittest.TestCase):
    ''' Test class CachePckLoader '''
    PckLoader = CachePckLoader

    def test_cacheloader_init(self):
        self.loader_init(DATA_C)

    def test_cacheloader_get(self):
        self.loader_get(DATA_C)
