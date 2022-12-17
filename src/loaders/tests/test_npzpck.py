# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import unittest
import numpy

from . import DATA, PckLoaderTest
from ..npzpck import NpzPckLoader


class TestNpzPckLoader(PckLoaderTest, unittest.TestCase):
    ''' Test class NpzPckLoader '''
    PckLoader = NpzPckLoader

    def setUp(self):
        super(TestNpzPckLoader, self).setUp()
        numpy.savez_compressed(self.tmpfile, **DATA)

    def test_npzloader_init(self):
        self.loader_init()

    def test_npzloader_get(self):
        self.loader_get()
