# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import os
import unittest
import zipfile
from . import RawLoaderTest
from ..zipraw import ZipRawLoader

ZIPPATH = os.path.join(os.path.dirname(__file__), 'raw.zip')


@unittest.skipUnless(zipfile.is_zipfile(ZIPPATH),
                     "'%s' is not a tar archive!" % ZIPPATH)
class TestZipRawLoader(RawLoaderTest, unittest.TestCase):
    ''' Test class ZipRawLoader '''
    RawLoader = ZipRawLoader
    RawPath = ZIPPATH

    def test_ziploader_init(self):
        self.loader_init()

    def test_ziploader_get(self):
        self.loader_get()
