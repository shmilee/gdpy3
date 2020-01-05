# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

import os
import unittest
import tempfile
import shutil


class TestDirRawLoader(unittest.TestCase):
    '''
    Test class DirRawLoader
    '''

    def setUp(self):
        from ..dirraw import DirRawLoader
        self.DirRawLoader = DirRawLoader
        self.tmpdir = tempfile.mktemp(suffix='-test')
        # tmp-test/{f1.ignore,f1.out}
        # tmp-test/d1/f2.out
        # tmp-test/d1/d2/{f3.out, d3/}
        os.makedirs(os.path.join(self.tmpdir, 'd1', 'd2', 'd3'))
        with open(os.path.join(self.tmpdir, 'f1.out'), mode='w') as f1:
            f1.write('test1')
        with open(os.path.join(self.tmpdir, 'f1.ignore'), mode='w') as f1:
            pass
        with open(os.path.join(self.tmpdir, 'd1', 'f2.out'), mode='w') as f2:
            f2.write('test2')
        with open(os.path.join(self.tmpdir, 'd1', 'd2', 'f3.out'),
                  mode='w') as f3:
            f3.write('test3')

    def tearDown(self):
        if os.path.isdir(self.tmpdir):
            shutil.rmtree(self.tmpdir)

    def test_dirloader_init(self):
        with self.assertRaises(IOError):
            loader = self.DirRawLoader(self.tmpdir + 'BreakSuffix')
        loader = self.DirRawLoader(self.tmpdir)
        self.assertSetEqual(set(loader.filenames),
                            {'f1.ignore', 'f1.out', 'd1/f2.out'})
        loader = self.DirRawLoader(
            self.tmpdir,
            filenames_filter=lambda n: True if n.endswith('.out') else False)
        self.assertSetEqual(set(loader.filenames), {'f1.out', 'd1/f2.out'})

    def test_dirloader_get(self):
        loader = self.DirRawLoader(self.tmpdir)
        with loader.get('f1.out') as f1:
            self.assertEqual(f1.readlines(), ['test1'])
        with loader.get('d1/f2.out') as f2:
            self.assertEqual(f2.read(), 'test2')
        with self.assertRaises(ValueError):
            f2.read()
