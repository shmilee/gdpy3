# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

import os
import unittest
import tempfile
import zipfile

ZIPFILE = os.path.join(os.path.dirname(__file__), 'raw.zip')


@unittest.skipUnless(zipfile.is_zipfile(ZIPFILE),
                     "'%s' is not a tar archive!" % ZIPFILE)
class TestZipRawLoader(unittest.TestCase):
    '''
    Test class ZipRawLoader
    '''

    def setUp(self):
        from ..zipraw import ZipRawLoader
        self.tmpfile = tempfile.mktemp(suffix='-test.zip')
        with open(self.tmpfile, mode='w') as f:
            f.write('test')
        self.RawLoader = ZipRawLoader
        self.tmpzip = ZIPFILE

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_ziploader_init(self):
        with self.assertRaises(ValueError):
            loader = self.RawLoader(self.tmpfile)
        loader = self.RawLoader(self.tmpzip)
        self.assertSetEqual(set(loader.filenames),
                            {'f1.ignore', 'f1.out', 'd1/f2.out', 'd1/d2/f3.out'})

    def test_ziploader_get(self):
        loader = self.RawLoader(self.tmpzip)
        with loader.get('f1.out') as f1:
            self.assertEqual(f1.readlines(), ['test1'])
        with loader.get('d1/f2.out') as f2:
            self.assertEqual(f2.read(), 'test2')
        with self.assertRaises(ValueError):
            f2.read()
