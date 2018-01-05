# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import unittest
import tempfile
import tarfile

TARFILE = os.path.join(os.path.dirname(__file__), 'raw.tar.gz')

@unittest.skipUnless(tarfile.is_tarfile(TARFILE),
                     "'%s' is not a tar archive!" % TARFILE)
class TestTarRawLoader(unittest.TestCase):
    '''
    Test class TarRawLoader
    '''

    def setUp(self):
        from ..tarraw import TarRawLoader
        self.tmpfile = tempfile.mktemp(suffix='-test.tar.gz')
        with open(self.tmpfile, mode='w') as f:
            f.write('test')
        self.TarRawLoader = TarRawLoader
        self.tmptar = TARFILE

    def tearDown(self):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)

    def test_tarloader_init(self):
        with self.assertRaises(IOError):
            loader = self.TarRawLoader(self.tmpfile)
        loader = self.TarRawLoader(self.tmptar)
        self.assertSetEqual(set(loader.filenames), {'f1.ignore', 'f1.out', 'd1/f2.out', 'd1/d2/f3.out'})

    def test_tarloader_get(self):
        loader = self.TarRawLoader(self.tmptar)
        with loader.get('f1.out') as f1:
            self.assertEqual(f1.readlines(), ['test1'])
        with loader.get('d1/f2.out') as f2:
            self.assertEqual(f2.read(), 'test2')
        with self.assertRaises(ValueError):
            f2.read()
