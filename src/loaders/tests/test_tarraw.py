# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import os
import unittest
import tarfile
from . import RawLoaderTest
from ..tarraw import TarRawLoader

TARPATH = os.path.join(os.path.dirname(__file__), 'raw.tar.gz')


@unittest.skipUnless(tarfile.is_tarfile(TARPATH),
                     "'%s' is not a tar archive!" % TARPATH)
class TestTarRawLoader(RawLoaderTest, unittest.TestCase):
    ''' Test class TarRawLoader '''
    RawLoader = TarRawLoader
    RawPath = TARPATH

    def test_tarloader_init(self):
        self.loader_init()

    def test_tarloader_get(self):
        self.loader_get()
