# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

import os
import unittest
import tempfile
import shutil
from . import RawLoaderTest
from ..dirraw import DirRawLoader


class TestDirRawLoader(RawLoaderTest, unittest.TestCase):
    ''' Test class DirRawLoader '''
    RawLoader = DirRawLoader
    RawPath = tempfile.mktemp(suffix='-test')
    RawFilenames = {'f1.ignore', 'f1.out', 'd1/f2.out'}

    def setUp(self):
        super(TestDirRawLoader, self).setUp()
        # tmp-test/{f1.ignore,f1.out}
        # tmp-test/d1/f2.out
        # tmp-test/d1/d2/{f3.out, d3/}
        os.makedirs(os.path.join(self.RawPath, 'd1', 'd2', 'd3'))
        with open(os.path.join(self.RawPath, 'f1.out'), mode='w') as f1:
            f1.write('test1')
        with open(os.path.join(self.RawPath, 'f1.ignore'), mode='w') as f1:
            pass
        with open(os.path.join(self.RawPath, 'd1', 'f2.out'), mode='w') as f2:
            f2.write('test2')
        with open(os.path.join(self.RawPath, 'd1', 'd2', 'f3.out'),
                  mode='w') as f3:
            f3.write('test3')

    def tearDown(self):
        super(TestDirRawLoader, self).tearDown()
        if os.path.isdir(self.RawPath):
            shutil.rmtree(self.RawPath)

    def test_dirloader_init(self):
        self.loader_init()

    def test_dirloader_get(self):
        self.loader_get()
